#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
AURA NEXUS - Teste Básico
Verifica componentes essenciais do sistema
"""

import os
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

print("=== AURA NEXUS - TESTE BÁSICO ===\n")

# 1. Verificar arquivo .env
print("1. Verificando arquivo .env...")
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()
    
    keys = [
        'GOOGLE_MAPS_API_KEY',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'GOOGLE_GEMINI_API_KEY',
        'APIFY_API_TOKEN'
    ]
    
    for key in keys:
        value = os.getenv(key)
        if value and value != f'your_{key.lower()}_here':
            print(f"   ✅ {key}: Configurado")
        else:
            print(f"   ❌ {key}: Não configurado")
else:
    print("   ❌ Arquivo .env não encontrado!")

# 2. Verificar planilha de input
print("\n2. Verificando planilha de input...")
input_file = 'data/input/base-leads_amostra_v2.xlsx'
if os.path.exists(input_file):
    import pandas as pd
    df = pd.read_excel(input_file)
    print(f"   ✅ Planilha encontrada: {len(df)} leads")
    print(f"   📊 Colunas: {len(df.columns)}")
    
    # Verificar dados do Google Places
    places_cols = [col for col in df.columns if col.startswith('places')]
    if places_cols:
        print(f"   📍 Colunas Google Places: {len(places_cols)}")
        has_place_id = df['placesId'].notna().sum()
        print(f"   🏢 Leads com Google Place ID: {has_place_id}/{len(df)}")
else:
    print(f"   ❌ Planilha não encontrada em: {input_file}")

# 3. Verificar módulos básicos
print("\n3. Verificando módulos do sistema...")
modules_to_check = [
    ('utils', 'src.utils'),
    ('orchestrator', 'src.core.orchestrator'),
    ('spreadsheet_adapter', 'src.infrastructure.spreadsheet_adapter'),
    ('api_manager', 'src.core.api_manager'),
    ('lead_processor', 'src.core.lead_processor'),
    ('cache_system', 'src.infrastructure.cache_system'),
]

for name, module_path in modules_to_check:
    try:
        exec(f"from {module_path} import *")
        print(f"   ✅ {name}: OK")
    except ImportError as e:
        print(f"   ❌ {name}: {str(e)}")
    except Exception as e:
        print(f"   ⚠️ {name}: Erro - {str(e)}")

# 4. Testar adaptador de planilha
print("\n4. Testando adaptador de planilha...")
try:
    from src.infrastructure.spreadsheet_adapter import SpreadsheetAdapter
    adapter = SpreadsheetAdapter()
    
    if os.path.exists(input_file):
        adapted_df = adapter.adapt_spreadsheet(input_file)
        print(f"   ✅ Planilha adaptada com sucesso")
        print(f"   📊 Colunas mapeadas: {sum(1 for col in adapted_df.columns if not col.startswith('original_'))}")
        print(f"   📌 Algumas colunas: {list(adapted_df.columns[:5])}")
        
        # Verificar mapeamento
        if 'nome_empresa' in adapted_df.columns:
            print(f"   ✅ Coluna nome_empresa mapeada corretamente")
            print(f"   🏢 Primeira empresa: {adapted_df['nome_empresa'].iloc[0]}")
except Exception as e:
    print(f"   ❌ Erro ao testar adaptador: {str(e)}")

print("\n=== FIM DO TESTE ===")
print("\nPróximos passos:")
print("1. Criar módulos faltantes (api_manager, lead_processor, etc)")
print("2. Configurar chaves de API no arquivo .env")
print("3. Executar: python scripts/process_leads.py --input data/input/base-leads_amostra_v2.xlsx --mode basic")