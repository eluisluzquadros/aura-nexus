#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AURA NEXUS - Teste dos Componentes
Testa os módulos criados
"""

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import asyncio
import pandas as pd
from pathlib import Path
import logging

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.spreadsheet_adapter import SpreadsheetAdapter
from src.infrastructure.cache_system import SmartMultiLevelCache
from src.infrastructure.checkpoint_manager import CheckpointManager
from src.core.api_manager import APIManager
from src.core.lead_processor import LeadProcessor
from src.core.multi_llm_consensus import MultiLLMConsensus

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("AURA_NEXUS.Test")


async def test_components():
    """Testa todos os componentes"""
    print("=== AURA NEXUS - TESTE DE COMPONENTES ===\n")
    
    # 1. Testar SpreadsheetAdapter
    print("1. Testando SpreadsheetAdapter...")
    try:
        adapter = SpreadsheetAdapter()
        df = adapter.adapt_spreadsheet('data/input/base-leads_amostra_v2.xlsx')
        print(f"   ✅ {len(df)} leads carregados")
        print(f"   📍 Primeiro lead: {df.iloc[0]['nome_empresa']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 2. Testar Cache
    print("\n2. Testando SmartMultiLevelCache...")
    try:
        cache = SmartMultiLevelCache(Path("data/cache"))
        await cache.initialize()
        
        # Salvar e recuperar
        await cache.set("test_key", {"value": "test"})
        result = await cache.get("test_key")
        print(f"   ✅ Cache funcionando: {result}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 3. Testar CheckpointManager
    print("\n3. Testando CheckpointManager...")
    try:
        checkpoint = CheckpointManager()
        session = checkpoint.create_session("test_session")
        
        # Salvar checkpoint
        await checkpoint.save_checkpoint({"test": "data"}, "test_checkpoint")
        print(f"   ✅ Checkpoint salvo na sessão: {session}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 4. Testar APIManager
    print("\n4. Testando APIManager...")
    try:
        api_manager = APIManager()
        await api_manager.initialize()
        
        apis = api_manager.get_available_apis()
        print(f"   ✅ APIs disponíveis: {apis}")
        print(f"   📊 Status: {api_manager.get_api_status()}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 5. Testar LeadProcessor
    print("\n5. Testando LeadProcessor...")
    try:
        processor = LeadProcessor(api_manager, cache)
        await processor.initialize()
        
        # Processar primeiro lead
        lead_data = df.iloc[0].to_dict()
        
        # Testar apenas extração de contatos (não requer APIs)
        result = await processor.process_lead(
            lead_data,
            features=['contact_extraction']
        )
        
        print(f"   ✅ Lead processado: {result['nome_empresa']}")
        print(f"   📍 Features executadas: {result['processamento']['features_executadas']}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    finally:
        if 'processor' in locals():
            await processor.close()
    
    # 6. Testar MultiLLMConsensus
    print("\n6. Testando MultiLLMConsensus...")
    try:
        consensus = MultiLLMConsensus(api_manager)
        print(f"   ✅ LLMs disponíveis: {consensus.available_llms}")
        
        # Se houver LLMs, testar análise simples
        if consensus.available_llms:
            test_data = {
                'nome': 'Teste Assistência',
                'rating': 4.5,
                'website': 'www.exemplo.com'
            }
            
            result = await consensus.analyze_with_consensus(
                test_data,
                'qualitative_summary'
            )
            
            print(f"   ✅ Análise concluída: {result.consensus_type}")
            print(f"   📊 Score de concordância: {result.agreement_score}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Fechar recursos
    if 'api_manager' in locals():
        await api_manager.close()
    
    print("\n✅ Teste de componentes concluído!")
    print("\nPara executar o processamento completo:")
    print("python scripts/process_leads.py --input data/input/base-leads_amostra_v2.xlsx --mode basic")


if __name__ == "__main__":
    asyncio.run(test_components())