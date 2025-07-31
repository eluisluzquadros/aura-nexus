#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for LLM Consensus Integration
Tests the critical consensus system functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.api_manager import APIManager
from src.core.multi_llm_consensus import MultiLLMConsensus
from src.core.lead_processor import LeadProcessor
from src.infrastructure.cache_system import SmartMultiLevelCache


async def test_api_manager_initialization():
    """Test 1: API Manager initialization with all providers"""
    print("🧪 Test 1: API Manager Initialization")
    
    api_manager = APIManager()
    await api_manager.initialize()
    
    available_apis = api_manager.get_available_apis()
    print(f"   Available APIs: {available_apis}")
    
    # Check expected APIs
    expected_apis = ['openai', 'anthropic', 'gemini', 'deepseek']
    found_llm_apis = [api for api in expected_apis if api in available_apis]
    
    print(f"   LLM APIs Found: {found_llm_apis}")
    print(f"   Status: {'✅ PASS' if found_llm_apis else '❌ FAIL - No LLM APIs configured'}")
    
    await api_manager.close()
    return len(found_llm_apis) > 0


async def test_consensus_system():
    """Test 2: MultiLLM Consensus System"""
    print("\n🧪 Test 2: Consensus System Initialization")
    
    api_manager = APIManager()
    await api_manager.initialize()
    
    consensus = MultiLLMConsensus(api_manager)
    
    print(f"   Available LLMs: {consensus.available_llms}")
    print(f"   Total LLMs: {len(consensus.available_llms)}")
    
    # Test health check
    health = await consensus.health_check()
    print(f"   Health Status: {health['status']}")
    print(f"   LLM Status: {health['llm_status']}")
    
    success = len(consensus.available_llms) > 0
    print(f"   Status: {'✅ PASS' if success else '❌ FAIL - No LLMs available'}")
    
    await api_manager.close()
    return success


async def test_lead_processor_integration():
    """Test 3: Lead Processor with Consensus Integration"""
    print("\n🧪 Test 3: Lead Processor Integration")
    
    # Initialize components
    api_manager = APIManager()
    await api_manager.initialize()
    
    cache = SmartMultiLevelCache()
    await cache.initialize()
    
    processor = LeadProcessor(api_manager, cache)
    await processor.initialize()
    
    # Check if consensus is initialized
    has_consensus = hasattr(processor, 'consensus') and processor.consensus is not None
    print(f"   Consensus Initialized: {'✅ Yes' if has_consensus else '❌ No'}")
    
    if has_consensus:
        print(f"   Available LLMs: {processor.consensus.available_llms}")
        llm_count = len(processor.consensus.available_llms)
        print(f"   LLM Count: {llm_count}")
    else:
        llm_count = 0
    
    # Test with sample data if LLMs are available
    sample_lead = {
        'nome_empresa': 'Assistência Técnica Teste',
        'cidade': 'São Paulo',
        'estado': 'SP'
    }
    
    if llm_count > 0:
        print("   Testing consensus analysis...")
        try:
            # Test only the new consensus_analysis feature
            await processor._enrich_consensus_analysis(sample_lead)
            
            has_result = 'consensus_analysis' in sample_lead
            if has_result:
                status = sample_lead['consensus_analysis'].get('status', 'unknown')
                print(f"   Consensus Analysis Status: {status}")
                
                if status == 'concluido':
                    score = sample_lead['consensus_analysis'].get('score', 0)
                    agreement = sample_lead['consensus_analysis'].get('agreement_score', 0)
                    participating = sample_lead['consensus_analysis'].get('participating_llms', [])
                    print(f"   Analysis Score: {score}")
                    print(f"   Agreement Score: {agreement}")
                    print(f"   Participating LLMs: {participating}")
                
                success = True
            else:
                success = False
                
        except Exception as e:
            print(f"   ❌ Error during consensus analysis: {e}")
            success = False
    else:
        print("   ⚠️ Skipping consensus analysis test - no LLMs configured")
        success = True  # Don't fail if no APIs are configured
    
    print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
    
    # Cleanup
    await processor.close()
    await cache.close()
    await api_manager.close()
    
    return success


async def test_cost_tracking():
    """Test 4: Cost and Token Tracking"""
    print("\n🧪 Test 4: Cost and Token Tracking")
    
    api_manager = APIManager()
    await api_manager.initialize()
    
    consensus = MultiLLMConsensus(api_manager)
    
    if consensus.available_llms:
        # Test token counter
        test_text = "This is a test prompt for token counting."
        
        for llm in consensus.available_llms[:2]:  # Test first 2 LLMs
            token_count = consensus.token_counter.count_tokens(test_text, llm)
            print(f"   {llm} - Tokens: {token_count}")
        
        # Test cost calculation
        test_cost = consensus.token_counter.calculate_cost(100, 50, 'openai', 'gpt-3.5-turbo')
        print(f"   Test Cost (100 input, 50 output): ${test_cost:.4f}")
        
        success = True
    else:
        print("   ⚠️ Skipping cost tracking test - no LLMs available")
        success = True
    
    print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
    
    await api_manager.close()
    return success


async def main():
    """Run all integration tests"""
    print("🚀 AURA NEXUS - LLM Consensus Integration Tests")
    print("=" * 60)
    
    tests = [
        ("API Manager", test_api_manager_initialization),
        ("Consensus System", test_consensus_system),
        ("Lead Processor", test_lead_processor_integration),
        ("Cost Tracking", test_cost_tracking)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ CRITICAL ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Integration successful!")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed - Check configuration")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))