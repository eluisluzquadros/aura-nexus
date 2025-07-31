import pandas as pd
import json

# Ler arquivo
df = pd.read_excel('data/input/base-leads_amostra_v2_enriched_basic.xlsx')

print("=== DADOS ENRIQUECIDOS ===\n")
print(f"Total de colunas: {len(df.columns)}")
print(f"Total de leads: {len(df)}\n")

# Mostrar dados do primeiro lead
lead = df.iloc[0]
print("LEAD 1: My Case Store")
print("-" * 50)

# Mostrar apenas colunas com dados interessantes
for col in df.columns:
    value = lead[col]
    if pd.notna(value) and value != '' and value != 0:
        if isinstance(value, dict):
            print(f"\n{col}:")
            print(json.dumps(value, indent=2, ensure_ascii=False))
        elif isinstance(value, str) and len(value) > 100:
            print(f"\n{col}: {value[:100]}...")
        else:
            print(f"{col}: {value}")