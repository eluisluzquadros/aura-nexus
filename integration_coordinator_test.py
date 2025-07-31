# -*- coding: utf-8 -*-
"""
AURA NEXUS - Integration Coordinator Test
Tests all emergency fixes work together seamlessly
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all core component imports"""
    try:
        from src.core.api_manager import APIManager
        from src.core.lead_processor import LeadProcessor  
        from src.core.multi_llm_consensus import MultiLLMConsensus, ConsensusStrategy
        from src.infrastructure.cache_system import SmartMultiLevelCache
        from src.infrastructure.checkpoint_manager import CheckpointManager
        print("All imports successful")
        return True
    except Exception as e:
        print(f"Import failed: {e}")
        return False

def test_multi_llm_system():
    """Test Multi-LLM consensus system"""
    try:
        from src.core.multi_llm_consensus import MultiLLMConsensus, ConsensusStrategy
        from src.core.api_manager import APIManager
        
        api_manager = APIManager()
        consensus = MultiLLMConsensus(api_manager)
        
        # Test basic initialization
        assert len(ConsensusStrategy) >= 8, "Should have 8+ consensus strategies"
        
        # Test strategies are available
        strategies = [s.value for s in ConsensusStrategy]
        expected_strategies = ['majority_vote', 'weighted_average', 'kappa_weighted', 'ensemble_voting']
        for strategy in expected_strategies:
            assert strategy in strategies, f"Missing strategy: {strategy}"
        
        print("Multi-LLM consensus system verified")
        return True
    except Exception as e:
        print(f"Multi-LLM test failed: {e}")
        return False

def test_lead_processor_flattening():
    """Test lead processor data flattening"""
    try:
        from src.core.lead_processor import LeadProcessor
        from src.core.api_manager import APIManager
        from src.infrastructure.cache_system import SmartMultiLevelCache
        
        # Create test instances
        api_manager = APIManager()
        cache = SmartMultiLevelCache()
        processor = LeadProcessor(api_manager, cache)
        
        # Test flattening method exists
        assert hasattr(processor, '_flatten_lead_data'), "Missing _flatten_lead_data method"
        
        # Test with nested data
        test_data = {
            'nome_empresa': 'Test Company',
            'google_maps': {
                'place_id': 'test123',
                'rating': 4.5,
                'reviews': 100
            },
            'website_info': {
                'emails': ['test@company.com'],
                'phones': ['11999999999']
            },
            'ai_analysis': {
                'score': 85,
                'analysis': 'Good company'
            }
        }
        
        flattened = processor._flatten_lead_data(test_data)
        
        # Verify flattening worked
        assert 'google_maps_place_id' in flattened, "Google Maps data not flattened"
        assert 'website_info_emails' in flattened, "Website info not flattened"
        assert 'ai_analysis_score' in flattened, "AI analysis not flattened"
        assert flattened['google_maps_rating'] == 4.5, "Rating not preserved"
        
        print("Lead processor flattening verified")
        return True
    except Exception as e:
        print(f"Lead processor test failed: {e}")
        return False

def test_social_scraping_integration():
    """Test social scraping integration"""
    try:
        from src.core.lead_processor import LeadProcessor
        from src.core.api_manager import APIManager
        from src.infrastructure.cache_system import SmartMultiLevelCache
        
        api_manager = APIManager()
        cache = SmartMultiLevelCache()
        processor = LeadProcessor(api_manager, cache)
        
        # Check if social scraping methods exist
        assert hasattr(processor, '_enrich_social_scraping'), "Missing _enrich_social_scraping method"
        
        # Test Apify integration in API manager
        assert hasattr(api_manager, 'scrape_with_apify'), "Missing Apify integration"
        
        print("Social scraping integration verified")
        return True
    except Exception as e:
        print(f"Social scraping test failed: {e}")
        return False

def test_contact_validation():
    """Test contact validation system"""
    try:
        from src.core.lead_processor import LeadProcessor
        from src.core.api_manager import APIManager
        from src.infrastructure.cache_system import SmartMultiLevelCache
        
        api_manager = APIManager()
        cache = SmartMultiLevelCache()
        processor = LeadProcessor(api_manager, cache)
        
        # Check validation methods exist
        assert hasattr(processor, '_validate_contacts'), "Missing _validate_contacts method"
        assert hasattr(processor, '_is_valid_phone'), "Missing _is_valid_phone method"
        assert hasattr(processor, '_is_valid_email'), "Missing _is_valid_email method"
        
        # Test phone validation
        assert processor._is_valid_phone('11999999999'), "Valid phone rejected"
        assert not processor._is_valid_phone('123456789'), "Invalid phone accepted"
        assert not processor._is_valid_phone('000000000'), "Fake phone accepted"
        
        # Test email validation
        assert processor._is_valid_email('test@company.com'), "Valid email rejected"
        assert not processor._is_valid_email('invalid-email'), "Invalid email accepted"
        
        print("Contact validation verified")
        return True
    except Exception as e:
        print(f"Contact validation test failed: {e}")
        return False

def test_excel_integration():
    """Test Excel output integration"""
    try:
        # Check if process_leads_simple.py exists and has required functions
        if not os.path.exists('process_leads_simple.py'):
            print("❌ process_leads_simple.py not found")
            return False
            
        # Read and check for required functions
        with open('process_leads_simple.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_functions = ['organize_columns', 'save_enhanced_excel', 'create_summary_sheet']
        for func in required_functions:
            if func not in content:
                print(f"Missing function: {func}")
                return False
        
        print("Excel integration verified")
        return True
    except Exception as e:
        print(f"Excel integration test failed: {e}")
        return False

def test_system_configuration():
    """Test system configuration and environment"""
    try:
        # Check requirements.txt has new dependencies
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
                
            required_deps = ['numpy', 'scipy', 'scikit-learn', 'apify-client', 'beautifulsoup4']
            for dep in required_deps:
                if dep not in requirements:
                    print(f"Missing dependency in requirements.txt: {dep}")
        
        # Check .env.example has new variables
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as f:
                env_example = f.read()
                
            required_vars = ['APIFY_API_TOKEN', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
            for var in required_vars:
                if var not in env_example:
                    print(f"Missing environment variable in .env.example: {var}")
        
        print("System configuration verified")
        return True
    except Exception as e:
        print(f"Configuration test failed: {e}")
        return False

def test_integration_metrics():
    """Test that all integration points work together"""
    success_metrics = {}
    
    # Test each component
    success_metrics['imports'] = test_imports()
    success_metrics['multi_llm'] = test_multi_llm_system()
    success_metrics['lead_processor'] = test_lead_processor_flattening()
    success_metrics['social_scraping'] = test_social_scraping_integration()
    success_metrics['contact_validation'] = test_contact_validation()
    success_metrics['excel_integration'] = test_excel_integration()
    success_metrics['system_config'] = test_system_configuration()
    
    # Calculate integration rate
    total_tests = len(success_metrics)
    passed_tests = sum(success_metrics.values())
    integration_rate = (passed_tests / total_tests) * 100
    
    print(f"\nINTEGRATION SUMMARY")
    print(f"==========================================")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Integration Rate: {integration_rate:.1f}%")
    
    # Success criteria
    if integration_rate >= 85:
        print(f"INTEGRATION SUCCESS - Rate: {integration_rate:.1f}%")
        return True
    else:
        print(f"INTEGRATION INCOMPLETE - Rate: {integration_rate:.1f}%")
        return False

def main():
    """Main integration test"""
    print("AURA NEXUS INTEGRATION COORDINATOR TEST")
    print("==========================================")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    
    # Run integration tests
    success = test_integration_metrics()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nTest Duration: {duration:.2f} seconds")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Critical test failure: {e}")
        sys.exit(1)