#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AURA NEXUS - Teste Mínimo
Executa processamento básico de 1 lead
"""

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import asyncio
import pandas as pd
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.spreadsheet_adapter import SpreadsheetAdapter
from src.infrastructure.cache_system import SmartMultiLevelCache


async def test_minimal():
    """Testa processamento mínimo"""
    print("=== AURA NEXUS - TESTE MÍNIMO ===\n")
    
    # 1. Carregar e adaptar planilha
    print("1. Carregando planilha...")
    adapter = SpreadsheetAdapter()
    df = adapter.adapt_spreadsheet('data/input/base-leads_amostra_v2.xlsx')
    print(f"   ✅ {len(df)} leads carregados")
    
    # 2. Pegar primeiro lead
    first_lead = df.iloc[0]
    print(f"\n2. Primeiro lead:")
    print(f"   📍 Nome: {first_lead['nome_empresa']}")
    print(f"   📍 Cidade: {first_lead['cidade']}")
    print(f"   📍 Estado: {first_lead['estado']}")
    print(f"   📍 Já tem Google ID: {'Sim' if first_lead.get('gdr_ja_enriquecido_google') else 'Não'}")
    
    # 3. Testar cache
    print("\n3. Testando sistema de cache...")
    cache = SmartMultiLevelCache(Path("data/cache"))
    await cache.initialize()
    
    # Salvar no cache
    test_data = {
        'nome': first_lead['nome_empresa'],
        'processado': True
    }
    
    cache_key = f"test_{first_lead['nome_empresa']}"
    await cache.set(cache_key, test_data)
    print(f"   ✅ Dados salvos no cache")
    
    # Recuperar do cache
    cached_data = await cache.get(cache_key)
    if cached_data:
        print(f"   ✅ Dados recuperados do cache: {cached_data}")
    
    # 4. Estatísticas do cache
    stats = cache.get_stats()
    print(f"\n4. Estatísticas do cache:")
    print(f"   📦 Total de itens: {stats['total_items']}")
    print(f"   💾 Tamanho total: {stats['total_size_mb']} MB")
    
    print("\n✅ Teste mínimo concluído!")
    print("\nPara executar processamento completo:")
    print("python scripts/process_leads.py --input data/input/base-leads_amostra_v2.xlsx --mode basic --debug")


if __name__ == "__main__":
    asyncio.run(test_minimal())