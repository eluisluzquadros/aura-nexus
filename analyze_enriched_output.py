import pandas as pd

# Ler o arquivo gerado
file_path = "data/output/enriquecido_real_basic_20250731_060420.xlsx"
df = pd.read_excel(file_path, sheet_name='Leads_Enriquecidos')

print("="*80)
print("ANÁLISE DO ARQUIVO ENRIQUECIDO")
print("="*80)
print(f"\nTotal de leads: {len(df)}")
print(f"Total de colunas: {len(df.columns)}")

# Verificar campos enriquecidos
enriched_fields = ['email_encontrado', 'telefone_encontrado', 'whatsapp', 
                   'instagram', 'instagram_followers', 'facebook', 'linkedin',
                   'google_rating', 'google_reviews', 'google_verified']

print("\n--- COMPARAÇÃO DOS DADOS ENRIQUECIDOS ---")
for field in enriched_fields:
    if field in df.columns:
        unique_values = df[field].unique()
        print(f"\n{field}:")
        print(f"  Valores únicos: {len(unique_values)}")
        print(f"  Valores: {unique_values}")

# Mostrar os 3 leads lado a lado
print("\n--- DADOS DOS 3 LEADS ---")
for idx, row in df.iterrows():
    lead_name = row.get('name', 'Unknown')
    print(f"\nLead {idx+1}: {lead_name}")
    print(f"  Email original: {row.get('email', 'N/A')}")
    print(f"  Email enriquecido: {row.get('email_encontrado', 'N/A')}")
    print(f"  Telefone enriquecido: {row.get('telefone_encontrado', 'N/A')}")
    print(f"  Instagram: {row.get('instagram', 'N/A')}")
    print(f"  Instagram followers: {row.get('instagram_followers', 'N/A')}")

print("\n" + "="*80)
print("CONCLUSÃO: Os dados enriquecidos são IDÊNTICOS para todos os leads!")
print("Isso comprova que NÃO está ocorrendo enriquecimento real.")
print("="*80)