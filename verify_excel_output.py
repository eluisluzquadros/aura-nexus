#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify the Excel output to ensure all enriched data is properly saved
"""

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path

def verify_excel_output():
    """Verify the Excel output contains all enriched data"""
    
    print("🔍 Verifying Excel Output")
    print("=" * 50)
    
    # Check if file exists
    output_file = Path("data/output/test_enriched_fixed.xlsx")
    if not output_file.exists():
        print(f"❌ Output file not found: {output_file}")
        return False
    
    # Load the Excel file
    try:
        # Check all sheets
        excel_file = pd.ExcelFile(output_file)
        print(f"📋 Available sheets: {excel_file.sheet_names}")
        
        # Load main data sheet
        if 'Leads_Enriched' in excel_file.sheet_names:
            df = pd.read_excel(output_file, sheet_name='Leads_Enriched')
        else:
            df = pd.read_excel(output_file)
        
        print(f"✅ Data loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Analyze column categories
        print("\n📊 Column Analysis:")
        
        categories = {
            'Original Data': [col for col in df.columns if any(x in col for x in ['nome_empresa', 'cnpj', 'cidade', 'estado'])],
            'Google Maps': [col for col in df.columns if col.startswith('google_maps_')],
            'Website Info': [col for col in df.columns if col.startswith('website_info_')],
            'Contacts': [col for col in df.columns if col.startswith('contatos_')],
            'Social Media': [col for col in df.columns if 'social' in col or any(x in col for x in ['facebook', 'instagram', 'linkedin'])],
            'AI Analysis': [col for col in df.columns if col.startswith('ai_analysis_')],
            'Processing Info': [col for col in df.columns if col.startswith('processamento_')],
            'Traceability': [col for col in df.columns if col.startswith('gdr_')]
        }
        
        total_categorized = 0
        for category, columns in categories.items():
            count = len(columns)
            total_categorized += count
            print(f"  • {category}: {count} columns")
            
            # Show a few example columns
            if columns:
                for col in columns[:3]:
                    sample_value = df[col].iloc[0] if not pd.isna(df[col].iloc[0]) else 'N/A'
                    if isinstance(sample_value, str) and len(sample_value) > 40:
                        sample_value = sample_value[:40] + "..."
                    print(f"    - {col}: {sample_value}")
                if len(columns) > 3:
                    print(f"    ... and {len(columns)-3} more")
        
        uncategorized = len(df.columns) - total_categorized
        if uncategorized > 0:
            print(f"  • Other columns: {uncategorized}")
        
        # Check data completeness
        print("\n📈 Data Completeness:")
        
        key_checks = [
            ('Company Names', df['nome_empresa'].notna().sum()),
            ('Google Place IDs', df['google_maps_place_id'].notna().sum() if 'google_maps_place_id' in df.columns else 0),
            ('Google Ratings', df['google_maps_rating'].notna().sum() if 'google_maps_rating' in df.columns else 0),
            ('Phone Numbers', df['google_maps_telefone'].notna().sum() if 'google_maps_telefone' in df.columns else 0),
            ('Websites', df['google_maps_website'].notna().sum() if 'google_maps_website' in df.columns else 0),
            ('Total Contacts', (df['contatos_total_contatos'] > 0).sum() if 'contatos_total_contatos' in df.columns else 0),
            ('Processing Success', (df['gdr_taxa_sucesso'] > 0).sum() if 'gdr_taxa_sucesso' in df.columns else 0)
        ]
        
        for check_name, count in key_checks:
            percentage = (count / len(df) * 100) if len(df) > 0 else 0
            print(f"  • {check_name}: {count}/{len(df)} ({percentage:.1f}%)")
        
        # Check for data loss indicators
        print("\n🔍 Data Loss Check:")
        
        # Check if we have flattened data
        has_flattened = any(col.startswith('google_maps_') for col in df.columns)
        has_nested = any(col == 'google_maps' for col in df.columns)
        
        print(f"  • Flattened data present: {'✅' if has_flattened else '❌'}")
        print(f"  • Raw nested data present: {'❌ (good)' if not has_nested else '⚠️ (indicates incomplete flattening)'}")
        
        # Check traceability
        trace_columns = ['gdr_processamento_inicio', 'gdr_processamento_fim', 'gdr_features_executadas']
        has_traceability = all(col in df.columns for col in trace_columns)
        print(f"  • Traceability data: {'✅' if has_traceability else '❌'}")
        
        # Sample some key data
        print("\n📋 Sample Data (First Row):")
        sample_columns = [
            'nome_empresa', 'google_maps_place_id', 'google_maps_nome', 
            'google_maps_rating', 'contatos_total_contatos', 'gdr_taxa_sucesso'
        ]
        
        for col in sample_columns:
            if col in df.columns:
                value = df[col].iloc[0]
                print(f"  • {col}: {value}")
        
        # Check for additional sheets
        if len(excel_file.sheet_names) > 1:
            print(f"\n📑 Additional Sheets:")
            for sheet in excel_file.sheet_names:
                if sheet != 'Leads_Enriched':
                    try:
                        sheet_df = pd.read_excel(output_file, sheet_name=sheet)
                        print(f"  • {sheet}: {len(sheet_df)} rows, {len(sheet_df.columns)} columns")
                    except Exception as e:
                        print(f"  • {sheet}: Error reading - {e}")
        
        # Overall assessment
        print("\n✅ VERIFICATION RESULTS:")
        
        success_criteria = [
            ('Data loaded successfully', True),
            ('Has flattened columns', has_flattened),
            ('Has traceability', has_traceability),
            ('Contains enriched data', any('google_maps_' in col for col in df.columns)),
            ('No data loss', not has_nested),
            ('Multiple columns', len(df.columns) > 50)
        ]
        
        passed = sum(1 for _, result in success_criteria if result)
        
        for criteria, result in success_criteria:
            print(f"  {'✅' if result else '❌'} {criteria}")
        
        print(f"\n📊 Overall Score: {passed}/{len(success_criteria)} ({passed/len(success_criteria)*100:.1f}%)")
        
        return passed >= len(success_criteria) * 0.8  # 80% success rate
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

if __name__ == "__main__":
    success = verify_excel_output()
    if success:
        print("\n🎉 Excel output verification PASSED! All enriched data is properly saved.")
    else:
        print("\n⚠️ Excel output verification FAILED. Check the issues above.")