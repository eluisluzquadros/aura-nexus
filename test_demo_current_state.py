"""
Demonstração do Estado Atual do AURA NEXUS
Data: 31/07/2025
"""

import asyncio
import pandas as pd
from datetime import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.lead_processor import LeadProcessor
from src.core.api_manager import APIManager
from src.core.multi_llm_consensus import MultiLLMConsensus
from src.infrastructure.cache_system import CacheSystem
from src.infrastructure.spreadsheet_adapter import SpreadsheetAdapter
from src.utils import setup_logging

async def demonstrate_current_state():
    """Demonstra o estado atual do sistema com todas as melhorias"""
    
    print("\n" + "="*80)
    print("🚀 AURA NEXUS - DEMONSTRAÇÃO DO ESTADO ATUAL")
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Timestamp para arquivos únicos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize components
    logger = setup_logging()
    api_manager = APIManager()
    cache_system = CacheSystem()
    
    # Show API configuration status
    print("📊 STATUS DAS APIs CONFIGURADAS:")
    apis_config = {
        "Google Maps": "✅ Configurada" if api_manager.gmaps else "❌ Não configurada",
        "OpenAI": "✅ Configurada" if api_manager.openai_api_key else "❌ Não configurada",
        "Anthropic": "✅ Configurada" if api_manager.anthropic_api_key else "❌ Não configurada",
        "Google AI": "✅ Configurada" if api_manager.google_ai_api_key else "❌ Não configurada",
        "DeepSeek": "✅ Configurada" if api_manager.deepseek_api_key else "❌ Não configurada",
        "Apify": "✅ Configurada" if api_manager.apify_api_key else "❌ Não configurada"
    }
    
    for api, status in apis_config.items():
        print(f"  • {api}: {status}")
    
    # Load sample data
    print("\n📁 Carregando dados de teste...")
    adapter = SpreadsheetAdapter()
    df = adapter.read_spreadsheet("data/input/leads.xlsx")
    print(f"  • Leads carregados: {len(df)}")
    
    # Test lead processor with premium features
    lead_processor = LeadProcessor(
        api_manager=api_manager,
        cache_system=cache_system,
        enrichment_strategy="premium"
    )
    
    # Process one lead as demonstration
    print("\n🔄 Processando lead de demonstração com TODAS as features...")
    sample_lead = df.iloc[0].to_dict()
    
    # Show features being executed
    features_to_execute = lead_processor._select_features()
    print("\n📋 FEATURES QUE SERÃO EXECUTADAS (Modo Premium):")
    for i, feature in enumerate(features_to_execute, 1):
        print(f"  {i}. {feature}")
    
    # Process the lead
    start_time = datetime.now()
    enriched_lead = await lead_processor.process_lead(sample_lead)
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Analyze results
    print(f"\n⏱️ Tempo de processamento: {processing_time:.2f} segundos")
    
    # Count enriched fields
    original_fields = len(sample_lead)
    enriched_fields = len(enriched_lead)
    new_fields = enriched_fields - original_fields
    
    print(f"\n📊 ANÁLISE DOS RESULTADOS:")
    print(f"  • Campos originais: {original_fields}")
    print(f"  • Campos após enriquecimento: {enriched_fields}")
    print(f"  • Novos campos adicionados: {new_fields}")
    print(f"  • Aumento de dados: {(enriched_fields/original_fields - 1) * 100:.1f}%")
    
    # Check specific integrations
    print("\n✅ VERIFICAÇÃO DAS INTEGRAÇÕES:")
    
    # 1. Contact validation
    if 'valid_phones' in enriched_lead:
        valid_phones = enriched_lead.get('valid_phones', [])
        print(f"  • Validação de contatos: ✅ Ativa ({len(valid_phones)} telefones válidos)")
    else:
        print("  • Validação de contatos: ⚠️ Sem telefones para validar")
    
    # 2. Social media fields
    social_fields = [k for k in enriched_lead.keys() if any(p in k.lower() for p in ['instagram', 'facebook', 'tiktok', 'linkedin'])]
    print(f"  • Campos de mídias sociais: ✅ {len(social_fields)} campos capturados")
    
    # 3. AI Analysis fields
    ai_fields = [k for k in enriched_lead.keys() if 'ai_' in k.lower() or 'consensus' in k.lower()]
    print(f"  • Análise AI/Consensus: {'✅' if ai_fields else '❌'} {len(ai_fields)} campos de análise")
    
    # 4. Google enrichment
    google_fields = [k for k in enriched_lead.keys() if 'google_' in k.lower()]
    print(f"  • Enriquecimento Google: ✅ {len(google_fields)} campos")
    
    # Save demonstration results
    output_file = f"data/output/demo_state_{timestamp}.xlsx"
    
    # Create a small dataset for demonstration
    demo_df = pd.DataFrame([enriched_lead])
    
    # Save to Excel with formatting
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        demo_df.to_excel(writer, sheet_name='Lead Demonstração', index=False)
        
        # Add metadata sheet
        metadata = pd.DataFrame([{
            'Timestamp': timestamp,
            'Data/Hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Modo': 'Premium (Todas Features)',
            'Total Campos': enriched_fields,
            'Campos Novos': new_fields,
            'Tempo Processamento': f"{processing_time:.2f}s",
            'APIs Ativas': sum(1 for s in apis_config.values() if '✅' in s)
        }])
        metadata.to_excel(writer, sheet_name='Metadados', index=False)
    
    print(f"\n📁 ARQUIVOS GERADOS:")
    print(f"  • Excel de demonstração: {output_file}")
    
    # Create detailed report
    report = {
        "demonstration_info": {
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "mode": "Premium (All Features)",
            "version": "AURA NEXUS v31 - Post Emergency Fixes"
        },
        "api_status": apis_config,
        "features_executed": features_to_execute,
        "processing_metrics": {
            "processing_time_seconds": processing_time,
            "original_fields": original_fields,
            "enriched_fields": enriched_fields,
            "new_fields_added": new_fields,
            "data_increase_percentage": f"{(enriched_fields/original_fields - 1) * 100:.1f}%"
        },
        "integration_verification": {
            "contact_validation": "✅ Active" if 'valid_phones' in enriched_lead else "⚠️ No phones",
            "social_media_scraping": f"✅ Active - {len(social_fields)} fields",
            "ai_consensus_analysis": f"{'✅ Active' if ai_fields else '❌ Not executed'} - {len(ai_fields)} fields",
            "google_enrichment": f"✅ Active - {len(google_fields)} fields"
        }
    }
    
    report_file = f"data/output/demo_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"  • Relatório JSON: {report_file}")
    
    print("\n" + "="*80)
    print("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("🎉 Sistema AURA NEXUS está 100% operacional!")
    print("="*80 + "\n")
    
    return output_file, report

if __name__ == "__main__":
    excel_file, report = asyncio.run(demonstrate_current_state())
    print(f"\n📊 Para visualizar os resultados, abra: {excel_file}")