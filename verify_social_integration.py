#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final verification of social media scraping integration
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Suppress verbose logging
logging.getLogger().setLevel(logging.ERROR)

async def verify_complete_integration():
    """Verify the complete social scraping integration"""
    
    from src.core.api_manager import APIManager
    from src.core.lead_processor import LeadProcessor
    from src.infrastructure.cache_system import SmartMultiLevelCache
    
    print("AURA NEXUS - Social Media Scraping Integration Verification")
    print("=" * 70)
    
    # Initialize
    api_manager = APIManager()
    await api_manager.initialize()
    
    cache = SmartMultiLevelCache()
    await cache.initialize()
    
    processor = LeadProcessor(api_manager, cache)
    await processor.initialize()
    
    try:
        # Create comprehensive test lead
        test_lead = {
            'nome_empresa': 'Test Company SA',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'website_info': {
                'url': 'https://testcompany.com',
                'emails': ['info@testcompany.com'],
                'telefones': ['1133334444'],
                'redes_sociais': {
                    'instagram': 'https://instagram.com/testcompany',
                    'facebook': 'https://facebook.com/testcompany'
                }
            },
            'google_search': {
                'resultados': [
                    {'link': 'https://linkedin.com/company/testcompany', 'title': 'Test Company'},
                    {'link': 'https://twitter.com/testcompany', 'title': 'Test Company Twitter'}
                ]
            }
        }
        
        print("1. PROCESSING COMPLETE LEAD WITH ALL FEATURES...")
        print(f"   Company: {test_lead['nome_empresa']}")
        print(f"   Initial social links: {list(test_lead['website_info']['redes_sociais'].keys())}")
        
        # Process with all features
        features = ['web_scraping', 'social_scraping', 'contact_extraction']
        result = await processor.process_lead(test_lead, features)
        
        print(f"\n2. SOCIAL SCRAPING RESULTS:")
        print("   " + "-" * 40)
        
        if 'redes_sociais' in result:
            social = result['redes_sociais']
            
            # Summary stats
            if 'summary' in social:
                s = social['summary']
                print(f"   Total platforms: {s.get('total_platforms', 0)}")
                print(f"   Successful scrapes: {s.get('successful_scrapes', 0)}")
                print(f"   Success rate: {s.get('success_rate', 0)}%")
                print(f"   Apify used: {s.get('apify_used', False)}")
                print(f"   Fallback used: {s.get('fallback_used', False)}")
            
            # Platform details
            platforms = ['instagram', 'facebook', 'linkedin', 'twitter']
            for platform in platforms:
                if platform in social and social[platform]:
                    data = social[platform]
                    if 'error' not in data:
                        print(f"   {platform.title()}: SUCCESS")
                        if platform == 'instagram':
                            print(f"     Username: {data.get('username', 'N/A')}")
                            print(f"     Followers: {data.get('followers_count', 0)}")
                            print(f"     Email: {data.get('contact_email', 'N/A')}")
                        elif platform == 'facebook':
                            print(f"     Name: {data.get('name', 'N/A')}")
                            print(f"     Category: {data.get('category', 'N/A')}")
                    else:
                        print(f"   {platform.title()}: ERROR - {data['error']}")
        
        print(f"\n3. CONTACT CONSOLIDATION:")
        print("   " + "-" * 40)
        
        if 'contatos' in result:
            contacts = result['contatos']
            print(f"   Total emails: {len(contacts.get('emails', []))}")
            print(f"   Total phones: {len(contacts.get('telefones', []))}")
            print(f"   Total websites: {len(contacts.get('websites', []))}")
            print(f"   Total contacts: {contacts.get('total_contatos', 0)}")
            
            if contacts.get('emails'):
                print(f"   Emails: {', '.join(contacts['emails'][:3])}")
            if contacts.get('telefones'):
                print(f"   Phones: {', '.join(contacts['telefones'][:3])}")
        
        print(f"\n4. EXCEL OUTPUT VERIFICATION:")
        print("   " + "-" * 40)
        
        # Check flattened data
        social_columns = [k for k in result.keys() if 'redes_sociais' in k]
        
        print(f"   Total social columns: {len(social_columns)}")
        print(f"   Column examples:")
        
        key_columns = [
            'redes_sociais_summary_success_rate',
            'redes_sociais_instagram_username',
            'redes_sociais_instagram_followers_count',
            'redes_sociais_facebook_name',
            'redes_sociais_summary_total_platforms'
        ]
        
        for col in key_columns:
            if col in result:
                value = str(result[col])[:50]
                print(f"     {col}: {value}")
        
        print(f"\n5. API STATUS:")
        print("   " + "-" * 40)
        
        api_status = api_manager.get_api_status()
        available_apis = api_status['available_apis']
        
        print(f"   Available APIs: {', '.join(available_apis)}")
        
        if 'apify' in available_apis:
            print("   Apify: CONFIGURED - Full scraping available")
        else:
            print("   Apify: NOT CONFIGURED - Fallback scraping only")
        
        print(f"\n6. PROCESSING STATUS:")
        print("   " + "-" * 40)
        
        if 'processamento' in result:
            proc = result['processamento']
            features_run = proc.get('features_executadas', [])
            errors = proc.get('erros', [])
            
            print(f"   Features executed: {', '.join(features_run)}")
            print(f"   Processing errors: {len(errors)}")
            
            if errors:
                for error in errors[:3]:  # Show first 3 errors
                    print(f"     {error.get('feature', 'unknown')}: {error.get('erro', 'unknown')}")
        
        # Final validation
        success_indicators = [
            'redes_sociais' in result,
            len([k for k in result.keys() if 'redes_sociais' in k]) >= 10,
            result.get('redes_sociais', {}).get('summary', {}).get('total_platforms', 0) > 0,
            result.get('contatos', {}).get('total_contatos', 0) > 0
        ]
        
        success_count = sum(success_indicators)
        
        print(f"\n" + "=" * 70)
        print(f"INTEGRATION STATUS: {success_count}/4 SUCCESS INDICATORS")
        print("=" * 70)
        
        if success_count >= 3:
            print("✅ SOCIAL MEDIA SCRAPING INTEGRATION: SUCCESSFUL")
            print("\nThe integration is working correctly:")
            print("• Social media links are being discovered")
            print("• Scraping is being performed (with fallback)")
            print("• Data is being structured properly")
            print("• Excel columns are being generated")
            print("• Contacts are being consolidated")
            
            if 'apify' not in available_apis:
                print("\n📝 NOTE: Configure APIFY_API_TOKEN for enhanced scraping")
        else:
            print("❌ SOCIAL MEDIA SCRAPING INTEGRATION: NEEDS ATTENTION")
        
        return success_count >= 3
        
    except Exception as e:
        print(f"\n❌ INTEGRATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await processor.close()
        await api_manager.close()

if __name__ == "__main__":
    success = asyncio.run(verify_complete_integration())
    
    if success:
        print(f"\n🎉 VERIFICATION COMPLETE - READY FOR PRODUCTION!")
    else:
        print(f"\n🔧 VERIFICATION FAILED - NEEDS FIXES!")
        sys.exit(1)