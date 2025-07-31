# -*- coding: utf-8 -*-
"""
AURA NEXUS - Final Integration Pipeline Test
Tests complete lead processing pipeline with all emergency fixes
"""

import asyncio
import sys
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_full_pipeline():
    """Test complete pipeline with sample data"""
    try:
        from src.core.api_manager import APIManager
        from src.core.lead_processor import LeadProcessor
        from src.core.multi_llm_consensus import MultiLLMConsensus, ConsensusStrategy
        from src.infrastructure.cache_system import SmartMultiLevelCache
        
        print("Testing full pipeline integration...")
        
        # Initialize components
        api_manager = APIManager()
        cache = SmartMultiLevelCache()
        processor = LeadProcessor(api_manager, cache)
        consensus = MultiLLMConsensus(api_manager)
        
        await processor.initialize()
        
        # Sample lead data
        test_lead = {
            'nome_empresa': 'Test Company Ltda',
            'cnpj': '12.345.678/0001-90',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'telefone': '11999887766',
            'email': 'contato@testcompany.com',
            'website': 'https://testcompany.com'
        }
        
        # Test different feature combinations
        feature_sets = [
            ['google_details'],  # Basic Google Maps
            ['web_scraping'],    # Website scraping
            ['contact_extraction'],  # Contact validation
            ['google_details', 'web_scraping', 'contact_extraction']  # Combined
        ]
        
        results = {}
        
        for i, features in enumerate(feature_sets):
            print(f"Testing feature set {i+1}: {features}")
            
            try:
                # Process lead
                result = await processor.process_lead(test_lead.copy(), features)
                
                # Flatten data (test the fix)
                flattened = processor._flatten_lead_data(result)
                
                # Test Multi-LLM consensus if needed
                if 'ai_analysis' in features:
                    consensus_result = await consensus.analyze_with_consensus(
                        result, 'LEAD_ANALYSIS', strategy=ConsensusStrategy.MAJORITY_VOTE
                    )
                    flattened.update(processor._flatten_lead_data({'consensus': consensus_result}))
                
                results[f"test_{i+1}"] = {
                    'features': features,
                    'original_columns': len(test_lead),
                    'enriched_columns': len(flattened),
                    'data_expansion_rate': (len(flattened) / len(test_lead)) * 100,
                    'has_google_data': any(k.startswith('google_maps_') for k in flattened.keys()),
                    'has_website_data': any(k.startswith('website_info_') for k in flattened.keys()),
                    'has_contact_data': any(k.startswith('contatos_') for k in flattened.keys()),
                    'success': True
                }
                
            except Exception as e:
                results[f"test_{i+1}"] = {
                    'features': features,
                    'success': False,
                    'error': str(e)
                }
        
        await processor.close()
        
        return results
        
    except Exception as e:
        print(f"Pipeline test failed: {e}")
        return {}

def test_excel_output_simulation():
    """Simulate Excel output creation"""
    try:
        # Test data with flattened structure
        sample_flattened_data = {
            'nome_empresa': 'Test Company',
            'cnpj': '12.345.678/0001-90',
            'google_maps_place_id': 'ChIJ123xyz',
            'google_maps_rating': 4.5,
            'google_maps_reviews_count': 100,
            'website_info_title': 'Test Company - Homepage',
            'website_info_emails': 'contato@test.com',
            'website_info_phones': '11999887766',
            'redes_sociais_instagram_username': 'testcompany',
            'redes_sociais_instagram_followers_count': 5000,
            'redes_sociais_facebook_name': 'Test Company',
            'contatos_emails_total': 2,
            'contatos_telefones_total': 1,
            'gdr_processamento_inicio': datetime.now().isoformat(),
            'gdr_processamento_fim': datetime.now().isoformat(),
            'gdr_features_executadas': 'google_details,web_scraping,social_scraping,contact_extraction',
            'gdr_total_features_executadas': 4,
            'gdr_taxa_sucesso': 100.0
        }
        
        # Create DataFrame (simulating Excel creation)
        df = pd.DataFrame([sample_flattened_data])
        
        # Test column organization
        columns = list(df.columns)
        organized_columns = {
            'basic_info': [col for col in columns if col in ['nome_empresa', 'cnpj', 'cidade', 'estado']],
            'google_maps': [col for col in columns if col.startswith('google_maps_')],
            'website_info': [col for col in columns if col.startswith('website_info_')],
            'social_media': [col for col in columns if col.startswith('redes_sociais_')],
            'contacts': [col for col in columns if col.startswith('contatos_')],
            'processing': [col for col in columns if col.startswith('gdr_')]
        }
        
        return {
            'total_columns': len(columns),
            'organized_categories': len(organized_columns),
            'google_maps_columns': len(organized_columns['google_maps']),
            'website_columns': len(organized_columns['website_info']),
            'social_columns': len(organized_columns['social_media']),
            'contact_columns': len(organized_columns['contacts']),
            'processing_columns': len(organized_columns['processing']),
            'success': True
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_system_dependencies():
    """Check if all system dependencies are working"""
    results = {}
    
    # Test numpy/scipy for Multi-LLM consensus
    try:
        import numpy as np
        import scipy
        from sklearn.metrics import cohen_kappa_score
        results['statistical_libs'] = True
    except ImportError as e:
        results['statistical_libs'] = False
        results['statistical_error'] = str(e)
    
    # Test web scraping libraries
    try:
        import aiohttp
        import beautifulsoup4
        results['web_scraping_libs'] = True
    except ImportError as e:
        results['web_scraping_libs'] = False
        results['web_scraping_error'] = str(e)
    
    # Test Excel libraries
    try:
        import pandas as pd
        import openpyxl
        results['excel_libs'] = True
    except ImportError as e:
        results['excel_libs'] = False
        results['excel_error'] = str(e)
    
    # Test optional Apify
    try:
        from apify_client import ApifyClient
        results['apify_client'] = True
    except ImportError:
        results['apify_client'] = False
        results['apify_note'] = "Apify client not installed (optional)"
    
    return results

async def main():
    """Main integration pipeline test"""
    print("AURA NEXUS - FINAL INTEGRATION PIPELINE TEST")
    print("=============================================")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: System Dependencies
    print("1. Testing System Dependencies...")
    dependency_results = check_system_dependencies()
    
    # Test 2: Full Pipeline
    print("2. Testing Full Pipeline...")
    pipeline_results = await test_full_pipeline()
    
    # Test 3: Excel Output Simulation
    print("3. Testing Excel Output...")
    excel_results = test_excel_output_simulation()
    
    # Compile results
    final_results = {
        'test_timestamp': datetime.now().isoformat(),
        'dependencies': dependency_results,
        'pipeline': pipeline_results,
        'excel_output': excel_results
    }
    
    # Calculate success rates
    dependency_success = sum(1 for k, v in dependency_results.items() 
                           if k.endswith('_libs') and v) / 3 * 100
    
    pipeline_success = 0
    if pipeline_results:
        pipeline_success = sum(1 for test in pipeline_results.values() 
                             if test.get('success', False)) / len(pipeline_results) * 100
    
    excel_success = 100 if excel_results.get('success', False) else 0
    
    overall_success = (dependency_success + pipeline_success + excel_success) / 3
    
    # Report results
    print("\nFINAL INTEGRATION RESULTS")
    print("=" * 50)
    print(f"Dependencies Success Rate: {dependency_success:.1f}%")
    print(f"Pipeline Success Rate: {pipeline_success:.1f}%")
    print(f"Excel Output Success Rate: {excel_success:.1f}%")
    print(f"Overall Integration Rate: {overall_success:.1f}%")
    print()
    
    # Detailed results
    if pipeline_results:
        print("Pipeline Test Details:")
        for test_name, result in pipeline_results.items():
            if result.get('success'):
                print(f"  {test_name}: SUCCESS - {result['enriched_columns']} columns, "
                      f"{result['data_expansion_rate']:.1f}% expansion")
            else:
                print(f"  {test_name}: FAILED - {result.get('error', 'Unknown error')}")
    
    if excel_results.get('success'):
        print(f"\nExcel Output Structure:")
        print(f"  Total Columns: {excel_results['total_columns']}")
        print(f"  Google Maps Columns: {excel_results['google_maps_columns']}")
        print(f"  Website Columns: {excel_results['website_columns']}")
        print(f"  Social Media Columns: {excel_results['social_columns']}")
        print(f"  Contact Columns: {excel_results['contact_columns']}")
        print(f"  Processing Columns: {excel_results['processing_columns']}")
    
    # Save detailed results
    with open('integration_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: integration_test_results.json")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_success >= 85

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Critical pipeline test failure: {e}")
        sys.exit(1)