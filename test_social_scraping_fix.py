#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the new social media scraping implementation
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.api_manager import APIManager
from src.core.lead_processor import LeadProcessor
from src.infrastructure.cache_system import SmartMultiLevelCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("SocialScrapingTest")

async def test_social_scraping():
    """Test the new social scraping implementation"""
    
    # Initialize components
    api_manager = APIManager()
    await api_manager.initialize()
    
    cache = SmartMultiLevelCache()
    await cache.initialize()
    
    processor = LeadProcessor(api_manager, cache)
    await processor.initialize()
    
    try:
        # Test data with social media links
        test_lead = {
            'nome_empresa': 'Test Company',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'website_info': {
                'url': 'https://example.com',
                'redes_sociais': {
                    'instagram': 'https://instagram.com/testcompany',
                    'facebook': 'https://facebook.com/testcompany'
                }
            },
            'google_search': {
                'resultados': [
                    {
                        'link': 'https://linkedin.com/company/testcompany',
                        'title': 'Test Company - LinkedIn'
                    }
                ]
            }
        }
        
        print("🧪 Testando social scraping com dados de exemplo...")
        print(f"Links sociais identificados: {test_lead['website_info']['redes_sociais']}")
        
        # Process social scraping
        await processor._enrich_social_scraping(test_lead)
        
        # Display results
        print("\n📊 RESULTADOS DO SOCIAL SCRAPING:")
        print("=" * 50)
        
        if 'redes_sociais' in test_lead:
            social_data = test_lead['redes_sociais']
            
            print(f"Status: {social_data.get('status', 'processed')}")
            print(f"Links encontrados: {social_data.get('links', {})}")
            
            # Summary
            if 'summary' in social_data:
                summary = social_data['summary']
                print(f"\nResumo:")
                print(f"  Total plataformas: {summary.get('total_platforms', 0)}")
                print(f"  Scraping sucessos: {summary.get('successful_scrapes', 0)}")
                print(f"  Scraping falhas: {summary.get('failed_scrapes', 0)}")
                print(f"  Taxa de sucesso: {summary.get('success_rate', 0)}%")
                print(f"  Apify usado: {summary.get('apify_used', False)}")
                print(f"  Fallback usado: {summary.get('fallback_used', False)}")
            
            # Instagram data
            if 'instagram' in social_data and social_data['instagram']:
                print(f"\n📱 Instagram:")
                insta = social_data['instagram']
                if 'error' in insta:
                    print(f"  Erro: {insta['error']}")
                else:
                    print(f"  Username: {insta.get('username', 'N/A')}")
                    print(f"  Nome completo: {insta.get('full_name', 'N/A')}")
                    print(f"  Seguidores: {insta.get('followers_count', 0)}")
                    print(f"  Bio: {insta.get('bio', 'N/A')[:100]}...")
                    print(f"  Email: {insta.get('contact_email', 'N/A')}")
                    print(f"  Telefone: {insta.get('contact_phone_number', 'N/A')}")
                    print(f"  Método: {insta.get('scraping_method', 'N/A')}")
            
            # Facebook data
            if 'facebook' in social_data and social_data['facebook']:
                print(f"\n📘 Facebook:")
                fb = social_data['facebook']
                if 'error' in fb:
                    print(f"  Erro: {fb['error']}")
                else:
                    print(f"  Nome: {fb.get('name', 'N/A')}")
                    print(f"  Categoria: {fb.get('category', 'N/A')}")
                    print(f"  Seguidores: {fb.get('followers_count', 0)}")
                    print(f"  Bio: {fb.get('bio', 'N/A')[:100]}...")
                    print(f"  Email: {fb.get('contact_email', 'N/A')}")
                    print(f"  Telefone: {fb.get('contact_phone_number', 'N/A')}")
                    print(f"  Método: {fb.get('scraping_method', 'N/A')}")
            
            # LinkedIn data
            if 'linkedin' in social_data and social_data['linkedin']:
                print(f"\n💼 LinkedIn:")
                li = social_data['linkedin']
                if 'error' in li:
                    print(f"  Erro: {li['error']}")
                else:
                    print(f"  Company slug: {li.get('company_slug', 'N/A')}")
                    print(f"  Método: {li.get('scraping_method', 'N/A')}")
                    print(f"  Nota: {li.get('note', 'N/A')}")
        
        # Test flattening
        print(f"\n🗂️ Testando flattening para Excel...")
        flattened = processor._flatten_lead_data(test_lead)
        
        # Display social fields in flattened data
        social_fields = {k: v for k, v in flattened.items() if 'redes_sociais' in k}
        
        print(f"\nCampos sociais no Excel ({len(social_fields)} campos):")
        for field, value in sorted(social_fields.items())[:20]:  # Show first 20
            print(f"  {field}: {str(value)[:100]}...")
        
        if len(social_fields) > 20:
            print(f"  ... e mais {len(social_fields) - 20} campos")
        
        # Test contact extraction with social data
        print(f"\n📞 Testando extração de contatos...")
        await processor._enrich_contact_extraction(test_lead)
        
        if 'contatos' in test_lead:
            contatos = test_lead['contatos']
            print(f"Emails encontrados: {contatos.get('emails', [])}")
            print(f"Telefones encontrados: {contatos.get('telefones', [])}")
            print(f"Websites encontrados: {contatos.get('websites', [])}")
            print(f"Total contatos: {contatos.get('total_contatos', 0)}")
        
        print(f"\n✅ Teste concluído com sucesso!")
        
        # Check API status
        api_status = api_manager.get_api_status()
        print(f"\n📡 Status das APIs:")
        print(f"APIs disponíveis: {api_status['available_apis']}")
        
        if 'apify' in api_status['available_apis']:
            print("✅ Apify configurado e disponível")
        else:
            print("⚠️ Apify não configurado - usando apenas fallback")
        
        return test_lead
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}", exc_info=True)
        return None
        
    finally:
        await processor.close()
        await cache.close()
        await api_manager.close()

async def test_edge_cases():
    """Test edge cases for social scraping"""
    
    print(f"\n🧪 Testando casos extremos...")
    
    # Initialize minimal components  
    api_manager = APIManager()
    await api_manager.initialize()
    
    cache = SmartMultiLevelCache()
    await cache.initialize()
    
    processor = LeadProcessor(api_manager, cache)
    await processor.initialize()
    
    try:
        # Test 1: No social links
        test_no_social = {
            'nome_empresa': 'Company No Social',
            'cidade': 'Rio de Janeiro',
            'estado': 'RJ'
        }
        
        print("Test 1: Empresa sem redes sociais")
        await processor._enrich_social_scraping(test_no_social)
        print(f"  Resultado: {test_no_social.get('redes_sociais', {})}")
        
        # Test 2: Invalid URLs
        test_invalid = {
            'nome_empresa': 'Company Invalid URLs',
            'website_info': {
                'redes_sociais': {
                    'instagram': 'https://instagram.com/invalid-user-999999',
                    'facebook': 'https://facebook.com/non-existent-page'
                }
            }
        }
        
        print("\nTest 2: URLs inválidas")
        await processor._enrich_social_scraping(test_invalid)
        if 'redes_sociais' in test_invalid:
            for platform, data in test_invalid['redes_sociais'].items():
                if isinstance(data, dict) and 'error' in data:
                    print(f"  {platform}: {data['error']}")
        
        # Test 3: Mixed results
        test_mixed = {
            'nome_empresa': 'Company Mixed Results',
            'website_info': {
                'redes_sociais': {
                    'instagram': 'https://instagram.com/testuser',
                    'facebook': 'https://facebook.com/invalid'
                }
            }
        }
        
        print("\nTest 3: Resultados mistos")
        await processor._enrich_social_scraping(test_mixed)
        if 'redes_sociais' in test_mixed and 'summary' in test_mixed['redes_sociais']:
            summary = test_mixed['redes_sociais']['summary']
            print(f"  Sucessos: {summary.get('successful_scrapes', 0)}")
            print(f"  Falhas: {summary.get('failed_scrapes', 0)}")
        
        print("✅ Casos extremos testados!")
        
    finally:
        await processor.close()
        await cache.close()
        await api_manager.close()

if __name__ == "__main__":
    print("AURA NEXUS - Teste Social Media Scraping Fix")
    print("=" * 60)
    
    # Run main test
    result = asyncio.run(test_social_scraping())
    
    if result:
        print(f"\n" + "="*60)
        
        # Run edge cases
        asyncio.run(test_edge_cases())
        
        print(f"\n🎉 Todos os testes concluídos!")
        print(f"\nPróximos passos:")
        print(f"1. Configure APIFY_API_TOKEN no .env para usar Apify")
        print(f"2. Execute um processamento real de leads")
        print(f"3. Verifique se todos os campos aparecem no Excel")
    else:
        print(f"\n❌ Teste falhou!")
        sys.exit(1)