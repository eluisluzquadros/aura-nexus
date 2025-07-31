import pandas as pd
import os
from datetime import datetime

print("="*80)
print("COMPARACAO DOS TRES MODOS - AURA NEXUS")
print("="*80)

# Encontrar os arquivos mais recentes de cada modo
output_dir = "data/output"
files = os.listdir(output_dir)

# Filtrar arquivos por modo
basic_files = [f for f in files if "enrichment_real_basic_" in f and f.endswith(".xlsx")]
full_files = [f for f in files if "enrichment_real_full_" in f and f.endswith(".xlsx")]
premium_files = [f for f in files if "enrichment_real_premium_" in f and f.endswith(".xlsx")]

# Pegar o mais recente de cada
basic_file = sorted(basic_files)[-1] if basic_files else None
full_file = sorted(full_files)[-1] if full_files else None
premium_file = sorted(premium_files)[-1] if premium_files else None

print(f"\nArquivos analisados:")
print(f"BASIC:   {basic_file}")
print(f"FULL:    {full_file}")
print(f"PREMIUM: {premium_file}")

# Analisar cada modo
modes_data = {}

for mode, filename in [("BASIC", basic_file), ("FULL", full_file), ("PREMIUM", premium_file)]:
    if filename:
        filepath = os.path.join(output_dir, filename)
        df = pd.read_excel(filepath, sheet_name='Dados_Completos')
        
        # Coletar informações
        modes_data[mode] = {
            'total_leads': len(df),
            'total_campos': len(df.columns),
            'campos_novos': df['novos_campos_adicionados'].iloc[0] if 'novos_campos_adicionados' in df else 0,
            'campos_especificos': []
        }
        
        # Identificar campos específicos do modo
        base_fields = ['name', 'id', 'status', 'city', 'state']  # campos originais comuns
        all_fields = set(df.columns)
        
        # Campos de contato (BASIC+)
        contact_fields = [f for f in all_fields if any(x in f for x in ['email_principal', 'telefone_principal', 'whatsapp', 'instagram', 'facebook', 'linkedin'])]
        
        # Campos de análise (FULL+)
        analysis_fields = [f for f in all_fields if any(x in f for x in ['segmento', 'porte', 'potencial', 'insight', 'recomendacao'])]
        
        # Campos premium
        premium_fields = [f for f in all_fields if any(x in f for x in ['score', 'probabilidade', 'valor_estimado'])]
        
        modes_data[mode]['contact_fields'] = len(contact_fields)
        modes_data[mode]['analysis_fields'] = len(analysis_fields)
        modes_data[mode]['premium_fields'] = len(premium_fields)

# Exibir comparação
print("\n" + "-"*80)
print("COMPARACAO DE CAMPOS POR MODO")
print("-"*80)

print(f"\n{'Modo':<10} {'Total Campos':<15} {'Novos Campos':<15} {'Contatos':<12} {'Analise':<12} {'Premium':<12}")
print("-"*80)

for mode in ['BASIC', 'FULL', 'PREMIUM']:
    if mode in modes_data:
        data = modes_data[mode]
        print(f"{mode:<10} {data['total_campos']:<15} {data['campos_novos']:<15} {data['contact_fields']:<12} {data['analysis_fields']:<12} {data['premium_fields']:<12}")

# Análise detalhada de um lead de cada modo
print("\n" + "-"*80)
print("EXEMPLO DE DADOS - PRIMEIRO LEAD DE CADA MODO")
print("-"*80)

for mode, filename in [("BASIC", basic_file), ("FULL", full_file), ("PREMIUM", premium_file)]:
    if filename:
        filepath = os.path.join(output_dir, filename)
        df = pd.read_excel(filepath, sheet_name='Dados_Completos')
        
        if len(df) > 0:
            lead = df.iloc[0]
            print(f"\n>>> MODO {mode} - {lead.get('name', 'Unknown')}")
            
            # Contatos
            print("\nCONTATOS:")
            print(f"  Email: {lead.get('email_principal', 'N/A')}")
            print(f"  Telefone: {lead.get('telefone_principal', 'N/A')}")
            print(f"  WhatsApp: {lead.get('whatsapp', 'N/A')}")
            
            # Redes Sociais
            print("\nREDES SOCIAIS:")
            print(f"  Instagram: {lead.get('instagram_profile', 'N/A')}")
            if 'instagram_followers' in lead:
                print(f"  Seguidores: {lead.get('instagram_followers', 'N/A')}")
            print(f"  Facebook: {lead.get('facebook_page', 'N/A')}")
            print(f"  LinkedIn: {lead.get('linkedin_company', 'N/A')}")
            
            # Análise (FULL e PREMIUM)
            if mode in ['FULL', 'PREMIUM']:
                print("\nANALISE DE NEGOCIO:")
                print(f"  Segmento: {lead.get('segmento_negocio', 'N/A')}")
                print(f"  Porte: {lead.get('porte_empresa', 'N/A')}")
                print(f"  Potencial: {lead.get('potencial_crescimento', 'N/A')}")
                print(f"  Insight: {lead.get('insight_principal', 'N/A')}")
                print(f"  Abordagem: {lead.get('recomendacao_abordagem', 'N/A')}")
            
            # Premium (apenas PREMIUM)
            if mode == 'PREMIUM':
                print("\nMETRICAS AVANCADAS:")
                print(f"  Score de Qualidade: {lead.get('score_qualidade', 'N/A')}/100")
                print(f"  Probabilidade de Conversao: {lead.get('probabilidade_conversao', 'N/A')}")
                print(f"  Valor Estimado: {lead.get('valor_estimado_lead', 'N/A')}")

# Resumo final
print("\n" + "="*80)
print("RESUMO DAS DIFERENCAS")
print("="*80)

print("\nBASIC (11 campos novos):")
print("  - Foco em CONTATOS e REDES SOCIAIS")
print("  - Ideal para primeiro contato")
print("  - Rapido e economico")

print("\nFULL (16 campos novos):")
print("  - Tudo do BASIC + ANALISE DE NEGOCIO")
print("  - Segmentacao e insights estrategicos")
print("  - Recomendacoes de abordagem")

print("\nPREMIUM (19 campos novos):")
print("  - Tudo do FULL + METRICAS AVANCADAS")
print("  - Score de qualidade e predicao")
print("  - Valor monetario do lead")

print("\n" + "="*80)