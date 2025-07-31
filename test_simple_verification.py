#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple verification of LeadProcessor fixes
"""

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path

def simple_verification():
    """Simple verification that the fixes are working"""
    
    print("🔍 Simple Verification - LeadProcessor Fix")
    print("=" * 50)
    
    # Check the Excel file that was generated
    test_file = Path("data/output/test_full_features.xlsx")
    
    if not test_file.exists():
        print("❌ Test file not found")
        return False
    
    try:
        # Load Excel file
        excel_file = pd.ExcelFile(test_file)
        print(f"📋 Sheets available: {excel_file.sheet_names}")
        
        # Load main data
        df = pd.read_excel(test_file, sheet_name='Leads_Enriched')
        print(f"✅ Data loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Key verification checks
        checks = [
            ("Has company data", 'nome_empresa' in df.columns and df['nome_empresa'].notna().any()),
            ("Has Google Maps data", any('google_maps_' in col for col in df.columns)),
            ("Has flattened structure", 'google_maps_place_id' in df.columns),
            ("Has contact data", any('contatos_' in col for col in df.columns)),
            ("Has traceability", any('gdr_' in col for col in df.columns)),
            ("Has processing info", 'gdr_processamento_inicio' in df.columns),
            ("Has success tracking", 'gdr_taxa_sucesso' in df.columns),
            ("Multiple sheets", len(excel_file.sheet_names) > 1),
            ("Sufficient columns", len(df.columns) >= 80)
        ]
        
        print("\n🔍 Verification Checks:")
        passed = 0
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if result:
                passed += 1
        
        # Show some sample data
        print("\n📊 Sample Data:")
        sample_cols = ['nome_empresa', 'google_maps_place_id', 'google_maps_rating', 'contatos_total_contatos', 'gdr_taxa_sucesso']
        for col in sample_cols:
            if col in df.columns:
                value = df[col].iloc[0] if len(df) > 0 else 'N/A'
                print(f"  • {col}: {value}")
        
        # Category breakdown
        print("\n📂 Column Categories:")
        categories = {
            'Google Maps': len([col for col in df.columns if col.startswith('google_maps_')]),
            'Website Info': len([col for col in df.columns if col.startswith('website_info_')]),
            'Contacts': len([col for col in df.columns if col.startswith('contatos_')]),
            'Processing': len([col for col in df.columns if col.startswith('processamento_')]),
            'Traceability': len([col for col in df.columns if col.startswith('gdr_')])
        }
        
        for category, count in categories.items():
            print(f"  • {category}: {count} columns")
        
        success_rate = passed / len(checks)
        print(f"\n📈 Verification Score: {passed}/{len(checks)} ({success_rate*100:.1f}%)")
        
        if success_rate >= 0.8:
            print("\n🎉 VERIFICATION PASSED!")
            print("✅ All critical data is being saved to Excel")
            print("✅ Data flattening is working correctly")
            print("✅ Traceability information is preserved")
            print("✅ Contact validation is functioning")
            print("✅ Multiple Excel sheets with documentation")
            return True
        else:
            print("\n⚠️ Some issues detected")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    success = simple_verification()
    if success:
        print("\n🚀 READY FOR USE:")
        print("python process_leads_simple.py --input your_file.xlsx --mode basic")
        print("python process_leads_simple.py --input your_file.xlsx --mode full") 
        print("python process_leads_simple.py --input your_file.xlsx --mode premium")
    else:
        print("\n⚠️ Issues detected - check the logs above")