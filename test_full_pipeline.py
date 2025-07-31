#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the full lead processing pipeline
"""

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import asyncio
from datetime import datetime

async def test_full_pipeline():
    """Test the complete lead processing pipeline"""
    
    print("🚀 Testing Full Lead Processing Pipeline")
    print("=" * 60)
    
    # Check if input file exists
    input_file = Path("data/input/base-leads_amostra_v2.xlsx")
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return False
    
    # Load a small sample for testing
    df = pd.read_excel(input_file)
    print(f"📋 Loaded {len(df)} leads from input file")
    
    # Test with just the first lead
    sample_df = df.head(1)
    print(f"🧪 Testing with 1 lead: {sample_df.iloc[0].get('name', 'Unknown')}")
    
    # Save test input
    test_input = Path("data/input/test_sample.xlsx")
    sample_df.to_excel(test_input, index=False)
    print(f"💾 Test sample saved to: {test_input}")
    
    # Import processing components
    from src.infrastructure.spreadsheet_adapter import SpreadsheetAdapter
    from src.infrastructure.cache_system import SmartMultiLevelCache
    from src.core.api_manager import APIManager
    from src.core.lead_processor import LeadProcessor
    
    print("\n🔧 Initializing components...")
    
    # 1. Load and adapt spreadsheet
    adapter = SpreadsheetAdapter()
    adapted_df = adapter.adapt_spreadsheet(str(test_input))
    print(f"✅ Spreadsheet adapted: {len(adapted_df.columns)} columns")
    
    # 2. Initialize processing components
    cache = SmartMultiLevelCache(Path("data/cache"))
    await cache.initialize()
    print("✅ Cache initialized")
    
    api_manager = APIManager()
    await api_manager.initialize()
    print("✅ API Manager initialized")
    
    processor = LeadProcessor(api_manager, cache)
    await processor.initialize()
    print("✅ Lead Processor initialized")
    
    # 3. Process the lead
    print("\n📊 Processing lead...")
    
    lead_data = adapted_df.iloc[0].to_dict()
    features = ['google_details', 'contact_extraction']  # Basic features only for testing
    
    print(f"🔄 Processing: {lead_data.get('nome_empresa', 'Unknown')}")
    print(f"📋 Features: {features}")
    
    try:
        result = await processor.process_lead(lead_data, features)
        print("✅ Lead processed successfully")
        
        # Check the result structure
        print(f"📈 Result has {len(result)} top-level keys")
        
        # Create DataFrame from result
        results_df = pd.DataFrame([result])
        print(f"✅ DataFrame created with {len(results_df.columns)} columns")
        
        # Save results
        output_file = Path("data/output/test_pipeline_result.xlsx")
        output_file.parent.mkdir(exist_ok=True)
        
        # Use the enhanced saving function
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            results_df.to_excel(writer, sheet_name='Test_Results', index=False)
            
            # Add column summary
            col_summary = pd.DataFrame({
                'Column': results_df.columns,
                'Type': [str(results_df[col].dtype) for col in results_df.columns],
                'Has_Data': [not pd.isna(results_df[col].iloc[0]) and results_df[col].iloc[0] != '' for col in results_df.columns],
                'Sample_Value': [str(results_df[col].iloc[0])[:100] if pd.notna(results_df[col].iloc[0]) else 'N/A' for col in results_df.columns]
            })
            col_summary.to_excel(writer, sheet_name='Column_Analysis', index=False)
        
        print(f"💾 Results saved to: {output_file}")
        
        # Analyze the results
        print("\n📊 Result Analysis:")
        
        # Check key data preservation
        checks = [
            ('Company Name', bool(result.get('nome_empresa'))),
            ('Processing Start', bool(result.get('gdr_processamento_inicio'))),
            ('Processing End', bool(result.get('gdr_processamento_fim'))),
            ('Features Executed', bool(result.get('gdr_features_executadas'))),
            ('Success Rate', result.get('gdr_taxa_sucesso', 0) >= 0),
        ]
        
        # Check Google Maps data if available
        if result.get('google_maps_place_id'):
            checks.append(('Google Place ID', True))
            checks.append(('Google Maps Data', bool(result.get('google_maps_nome'))))
        
        # Check contact data
        if result.get('contatos_total_contatos', 0) > 0:
            checks.append(('Contacts Found', True))
        
        passed = 0
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {check_result}")
            if check_result:
                passed += 1
        
        print(f"\n📈 Pipeline Test Results: {passed}/{len(checks)} checks passed")
        
        # Show some key columns that should exist
        key_columns = [
            'nome_empresa', 'cidade', 'estado',
            'gdr_processamento_inicio', 'gdr_processamento_fim',
            'gdr_features_executadas', 'gdr_taxa_sucesso',
            'gdr_total_features_executadas', 'gdr_total_erros'
        ]
        
        print("\n🔑 Key Columns Status:")
        for col in key_columns:
            has_col = col in result
            value = result.get(col, 'N/A')
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  {'✅' if has_col else '❌'} {col}: {value}")
        
        success = passed >= len(checks) * 0.8  # 80% success rate
        
    except Exception as e:
        print(f"❌ Error processing lead: {e}")
        success = False
    
    finally:
        # Cleanup
        await processor.close()
        await api_manager.close()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(test_full_pipeline())
    if success:
        print("\n🎉 Full pipeline test passed! All enriched data will be saved to Excel.")
    else:
        print("\n⚠️ Pipeline test had issues. Check the logs above.")