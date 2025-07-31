#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify lead data flattening functionality
"""

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.lead_processor import LeadProcessor
from src.core.api_manager import APIManager
from src.infrastructure.cache_system import SmartMultiLevelCache
import asyncio
import pandas as pd
import json

async def test_lead_flattening():
    """Test the lead data flattening functionality"""
    
    print("🧪 Testing Lead Data Flattening")
    print("=" * 50)
    
    # Initialize components
    cache = SmartMultiLevelCache(Path("data/cache"))
    await cache.initialize()
    
    api_manager = APIManager()
    await api_manager.initialize()
    
    processor = LeadProcessor(api_manager, cache)
    await processor.initialize()
    
    # Create test lead data
    test_lead = {
        'nome_empresa': 'Test Company Ltda',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cnpj': '12345678000195'
    }
    
    print(f"📋 Test Lead: {test_lead['nome_empresa']}")
    
    # Test flattening with sample nested data
    nested_data = {
        'nome_empresa': 'Test Company Ltda',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'google_maps': {
            'place_id': 'ChIJTest123',
            'nome': 'Test Company',
            'endereco': 'Test Address, São Paulo',
            'telefone': '(11) 99999-9999',
            'website': 'https://test.com',
            'rating': 4.5,
            'total_avaliacoes': 150
        },
        'website_info': {
            'url': 'https://test.com',
            'titulo': 'Test Company - Home',
            'emails': ['contact@test.com', 'info@test.com'],
            'telefones': ['1199999999', '1188888888'],
            'redes_sociais': {
                'facebook': 'https://facebook.com/test',
                'instagram': 'https://instagram.com/test'
            }
        },
        'contatos': {
            'emails': ['contact@test.com', 'info@test.com'],
            'telefones': ['1199999999', '1188888888'],
            'websites': ['https://test.com'],
            'total_contatos': 5
        },
        'ai_analysis': {
            'status': 'concluido',
            'score': 85,
            'analise': 'Company with good potential',
            'pontos_fortes': ['Good rating', 'Active website'],
            'oportunidades': ['Expand social media', 'More reviews']
        },
        'processamento': {
            'inicio': '2024-01-01T10:00:00',
            'fim': '2024-01-01T10:05:00',
            'features_executadas': ['google_details', 'web_scraping', 'ai_analysis'],
            'erros': []
        }
    }
    
    print("\n🔄 Testing flattening process...")
    
    # Test the flattening function
    flattened = processor._flatten_lead_data(nested_data)
    
    print(f"✅ Flattened data has {len(flattened)} columns")
    
    # Display key flattened columns
    key_columns = [
        'nome_empresa',
        'google_maps_place_id',
        'google_maps_telefone', 
        'google_maps_rating',
        'website_info_url',
        'website_info_emails',
        'contatos_total_contatos',
        'ai_analysis_score',
        'ai_analysis_analise',
        'gdr_features_executadas',
        'gdr_taxa_sucesso'
    ]
    
    print("\n📊 Key Flattened Columns:")
    for col in key_columns:
        if col in flattened:
            value = flattened[col]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  • {col}: {value}")
    
    # Test with DataFrame
    print("\n📋 Testing DataFrame creation...")
    df = pd.DataFrame([flattened])
    print(f"✅ DataFrame created with {len(df.columns)} columns")
    
    # Save test results
    test_output = Path("data/output/test_flattened_lead.xlsx")
    test_output.parent.mkdir(exist_ok=True)
    
    with pd.ExcelWriter(test_output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Test_Flattened', index=False)
        
        # Create column summary
        col_summary = pd.DataFrame({
            'Column': df.columns,
            'Type': [str(df[col].dtype) for col in df.columns],
            'Sample_Value': [str(df[col].iloc[0])[:100] if pd.notna(df[col].iloc[0]) else 'N/A' for col in df.columns]
        })
        col_summary.to_excel(writer, sheet_name='Column_Summary', index=False)
    
    print(f"💾 Test results saved to: {test_output}")
    
    # Verify critical data preservation
    print("\n🔍 Data Preservation Verification:")
    
    checks = [
        ('Google Place ID', flattened.get('google_maps_place_id') == 'ChIJTest123'),
        ('Google Rating', flattened.get('google_maps_rating') == 4.5),
        ('Website URL', flattened.get('website_info_url') == 'https://test.com'),
        ('Total Contacts', flattened.get('contatos_total_contatos') == 5),
        ('AI Score', flattened.get('ai_analysis_score') == 85),
        ('Features Executed', 'google_details' in str(flattened.get('gdr_features_executadas', ''))),
        ('Success Rate', flattened.get('gdr_taxa_sucesso', 0) > 0)
    ]
    
    passed = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}: {result}")
        if result:
            passed += 1
    
    print(f"\n📈 Test Results: {passed}/{len(checks)} checks passed")
    
    # Cleanup
    await processor.close()
    await api_manager.close()
    
    return passed == len(checks)

if __name__ == "__main__":
    success = asyncio.run(test_lead_flattening())
    if success:
        print("\n🎉 All tests passed! Lead flattening is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the implementation.")