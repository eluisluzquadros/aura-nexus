#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for LLM Consensus Integration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def main():
    """Simple integration test"""
    print("AURA NEXUS - LLM Consensus Integration Test")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.core.api_manager import APIManager
        from src.core.multi_llm_consensus import MultiLLMConsensus
        from src.core.lead_processor import LeadProcessor
        from src.infrastructure.cache_system import SmartMultiLevelCache
        print("   Imports: OK")
        
        # Test API Manager
        print("2. Testing API Manager...")
        api_manager = APIManager()
        await api_manager.initialize()
        available_apis = api_manager.get_available_apis()
        print(f"   Available APIs: {available_apis}")
        
        # Test Consensus System
        print("3. Testing Consensus System...")
        consensus = MultiLLMConsensus(api_manager)
        print(f"   Available LLMs: {consensus.available_llms}")
        
        if consensus.available_llms:
            print("   LLM APIs are configured!")
            
            # Simple analysis test
            test_data = {
                'nome': 'Test Company',
                'endereco': 'Sao Paulo, SP',
                'rating': 4.5,
                'reviews': 100,
                'website': 'https://test.com'
            }
            
            print("4. Testing Consensus Analysis...")
            result = await consensus.analyze_with_consensus(
                test_data,
                'business_potential'
            )
            
            if result.success:
                print("   Consensus Analysis: SUCCESS")
                print(f"   Score: {result.final_result.get('score', 'N/A')}")
                print(f"   Agreement: {result.agreement_score:.3f}")
                print(f"   LLMs Used: {result.participating_llms}")
                
                # Test cost tracking
                total_cost = sum(result.cost_breakdown.values())
                print(f"   Total Cost: ${total_cost:.4f}")
                print("   === INTEGRATION SUCCESSFUL ===")
            else:
                print(f"   Consensus Analysis: FAILED - {result.final_result.get('error', 'Unknown error')}")
        else:
            print("   No LLM APIs configured - check .env file")
            print("   Expected: OpenAI, Anthropic, Google AI, or DeepSeek API keys")
        
        await api_manager.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 50)
    print("Test completed successfully!")
    return True

if __name__ == "__main__":
    asyncio.run(main())