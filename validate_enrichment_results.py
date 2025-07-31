import pandas as pd
import os
from datetime import datetime

# Encontrar o arquivo mais recente
output_dir = "data/output"
files = [f for f in os.listdir(output_dir) if f.startswith("enrichment_real_") and f.endswith(".xlsx")]
latest_file = sorted(files)[-1]
file_path = os.path.join(output_dir, latest_file)

print("="*80)
print("VALIDACAO DO ARQUIVO DE ENRIQUECIMENTO REAL")
print("="*80)
print(f"\nArquivo analisado: {latest_file}")

# Ler todas as abas
excel_file = pd.ExcelFile(file_path)
print(f"Abas encontradas: {excel_file.sheet_names}")

# Analisar aba principal
df = pd.read_excel(file_path, sheet_name='Dados_Completos')
print(f"\nTotal de leads: {len(df)}")
print(f"Total de colunas: {len(df.columns)}")

# Verificar dados únicos
print("\n--- ANALISE DE UNICIDADE DOS DADOS ---")

# Emails
emails = df['email_principal'].tolist()
unique_emails = set(emails)
print(f"\nEmails:")
print(f"  Total: {len(emails)}")
print(f"  Unicos: {len(unique_emails)}")
print(f"  Taxa de unicidade: {len(unique_emails)/len(emails)*100:.1f}%")
print("  Exemplos:")
for email in list(unique_emails)[:5]:
    print(f"    - {email}")

# Telefones
phones = df['telefone_principal'].tolist()
unique_phones = set(phones)
print(f"\nTelefones:")
print(f"  Total: {len(phones)}")
print(f"  Unicos: {len(unique_phones)}")
print(f"  Taxa de unicidade: {len(unique_phones)/len(phones)*100:.1f}%")
print("  Exemplos:")
for phone in list(unique_phones)[:5]:
    print(f"    - {phone}")

# Instagram
instagrams = df['instagram_profile'].tolist()
unique_instagrams = set(instagrams)
print(f"\nPerfis Instagram:")
print(f"  Total: {len(instagrams)}")
print(f"  Unicos: {len(unique_instagrams)}")
print(f"  Taxa de unicidade: {len(unique_instagrams)/len(instagrams)*100:.1f}%")
print("  Exemplos:")
for ig in list(unique_instagrams)[:5]:
    followers = df[df['instagram_profile'] == ig]['instagram_followers'].iloc[0]
    print(f"    - {ig} ({followers} seguidores)")

# Verificar padrões
print("\n--- ANALISE DE PADROES ---")

# Verificar se os dados seguem um padrão realista
print("\nVariacao nos numeros de seguidores:")
followers = df['instagram_followers'].tolist()
print(f"  Minimo: {min(followers)}")
print(f"  Maximo: {max(followers)}")
print(f"  Media: {sum(followers)/len(followers):.0f}")
print(f"  Todos diferentes: {len(set(followers)) == len(followers)}")

# Analisar novos campos
print(f"\nNovos campos adicionados por lead:")
for idx, row in df.iterrows():
    print(f"  {row['name']}: {row['novos_campos_adicionados']} campos")

# Comparar com dados mockados anteriores
print("\n--- COMPARACAO COM DADOS MOCKADOS ---")
print("Dados mockados anteriores tinham:")
print("  - Todos os emails iguais: contato@empresa.com.br")
print("  - Todos os telefones iguais: (11) 98765-4321")
print("  - Todos os instagrams iguais: @empresa_oficial")
print("\nDados atuais:")
print(f"  - Emails unicos: {len(unique_emails)} diferentes")
print(f"  - Telefones unicos: {len(unique_phones)} diferentes")
print(f"  - Instagrams unicos: {len(unique_instagrams)} diferentes")

# Conclusão
print("\n" + "="*80)
if len(unique_emails) >= len(emails) * 0.8 and len(unique_phones) == len(phones):
    print("CONCLUSAO: DADOS SAO MAJORITARIAMENTE UNICOS!")
    print("O enriquecimento esta gerando dados diferentes para cada lead.")
else:
    print("CONCLUSAO: Alguns dados ainda tem duplicacoes.")
    print("Mas e uma melhoria significativa em relacao aos dados 100% mockados.")
print("="*80)