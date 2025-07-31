import pandas as pd

# Carregar planilha
df = pd.read_excel('data/input/base-leads_amostra_v2.xlsx')

print('=== ESTRUTURA DA PLANILHA ===')
print(f'Total de leads: {len(df)}')
print(f'\nTodas as colunas ({len(df.columns)}):')

for i, col in enumerate(df.columns):
    print(f'{i+1}. {col}')

print(f'\nPrimeiras 3 linhas:')
print(df.head(3))

# Verificar se já tem colunas gdr_
gdr_cols = [col for col in df.columns if col.startswith('gdr_')]
if gdr_cols:
    print(f'\nColunas GDR existentes: {gdr_cols}')

# Mapear colunas para o formato esperado
print('\n=== MAPEAMENTO DE COLUNAS ===')
print(f'name -> nome_empresa')
print(f'address -> endereco')
print(f'city -> cidade')
print(f'state -> estado')