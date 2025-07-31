#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for social scraping implementation
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_social_methods():
    """Test social scraping methods work"""
    
    from src.core.api_manager import APIManager
    from src.core.lead_processor import LeadProcessor
    from src.infrastructure.cache_system import SmartMultiLevelCache
    
    print("Testing social scraping implementation...")
    
    # Initialize components
    api_manager = APIManager()
    await api_manager.initialize()
    
    cache = SmartMultiLevelCache()
    await cache.initialize()
    
    processor = LeadProcessor(api_manager, cache)
    await processor.initialize()
    
    try:
        # Test helper methods
        print("\n1. Testing social platform identification...")
        
        test_urls = [
            "https://instagram.com/testuser",
            "https://facebook.com/testpage", 
            "https://linkedin.com/company/testcompany",
            "https://twitter.com/testuser",
            "https://example.com"
        ]
        
        for url in test_urls:
            platform = processor._identify_social_platform(url)
            print(f"  {url} -> {platform}")
        
        # Test data gathering
        print("\n2. Testing social link gathering...")
        
        test_data = {
            'website_info': {
                'redes_sociais': {
                    'instagram': 'https://instagram.com/company1',
                    'facebook': 'https://facebook.com/company1'
                }
            },
            'google_search': {
                'resultados': [
                    {'link': 'https://linkedin.com/company/company1'},
                    {'link': 'https://example.com/about'}
                ]
            }
        }
        
        social_links = processor._gather_social_links(test_data)
        print(f"  Found social links: {social_links}")
        
        # Test email/phone extraction
        print("\n3. Testing contact extraction...")
        
        test_bio = "Contact us at hello@company.com or call (11) 99999-8888"
        email = processor._extract_email_from_text(test_bio)
        phone = processor._extract_phone_from_text(test_bio)
        
        print(f"  From '{test_bio}':")
        print(f"  Email: {email}")
        print(f"  Phone: {phone}")
        
        # Test full social scraping
        print("\n4. Testing full social scraping...")
        
        test_lead = {
            'nome_empresa': 'Test Company',
            'website_info': {
                'redes_sociais': {
                    'instagram': 'https://instagram.com/nonexistentuser12345',
                }
            }
        }
        
        await processor._enrich_social_scraping(test_lead)
        
        if 'redes_sociais' in test_lead:
            print(f"  Social data structure created: YES")
            social_data = test_lead['redes_sociais']
            
            if 'summary' in social_data:
                summary = social_data['summary']
                print(f"  Total platforms: {summary.get('total_platforms', 0)}")
                print(f"  Success rate: {summary.get('success_rate', 0)}%")
            
            if 'instagram' in social_data:
                insta = social_data['instagram']
                if 'error' in insta:
                    print(f"  Instagram error (expected): {insta['error']}")
                else:
                    print(f"  Instagram data: {insta.get('username', 'No username')}")
        
        # Test flattening
        print("\n5. Testing Excel flattening...")
        
        flattened = processor._flatten_lead_data(test_lead)
        social_fields = [k for k in flattened.keys() if 'redes_sociais' in k]
        
        print(f"  Social fields in Excel: {len(social_fields)}")
        for field in social_fields[:5]:  # Show first 5
            print(f"    {field}: {str(flattened[field])[:50]}...")
        
        if len(social_fields) > 5:
            print(f"    ... and {len(social_fields) - 5} more fields")
        
        print("\n6. Checking API availability...")
        api_status = api_manager.get_api_status()
        print(f"  Available APIs: {api_status['available_apis']}")
        
        if 'apify' in api_status['available_apis']:
            print("  Apify: CONFIGURED")
        else:
            print("  Apify: NOT CONFIGURED (fallback only)")
        
        print("\nALL TESTS PASSED!")
        
        return True
        
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await processor.close()
        await cache.close()
        await api_manager.close()

if __name__ == "__main__":
    success = asyncio.run(test_social_methods())
    
    if success:
        print("\nSOCIAL SCRAPING IMPLEMENTATION: READY")
        print("\nNext steps:")
        print("1. Add APIFY_API_TOKEN to .env for full functionality")
        print("2. Test with real lead processing")
        print("3. Verify Excel output contains all social fields")
    else:
        print("\nFIX NEEDED!")
        sys.exit(1)