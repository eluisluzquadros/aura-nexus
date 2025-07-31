# 📚 GUIA COMPLETO DOS MODOS - AURA NEXUS

## 🎯 Visão Geral dos Modos

O AURA NEXUS oferece três modos de enriquecimento, cada um com diferentes níveis de profundidade e análise:

### 1️⃣ **MODO BASIC** - Enriquecimento Essencial
### 2️⃣ **MODO FULL** - Análise Completa com IA
### 3️⃣ **MODO PREMIUM** - Inteligência Avançada

---

## 📋 MODO BASIC - Enriquecimento Essencial

### 🎯 O que faz:
Coleta informações fundamentais de contato e presença digital básica.

### 📊 Campos Gerados (11 novos campos):
- **email_principal** - Email de contato principal
- **telefone_principal** - Telefone formatado brasileiro
- **whatsapp** - Número do WhatsApp
- **instagram_profile** - Perfil do Instagram
- **instagram_followers** - Número de seguidores
- **facebook_page** - Página do Facebook
- **linkedin_company** - Perfil da empresa no LinkedIn
- **processamento_timestamp** - Data/hora do processamento
- **processamento_modo** - Modo utilizado
- **novos_campos_adicionados** - Contagem de campos novos
- **total_campos_enriquecidos** - Total de campos final

### 💡 Ideal para:
- Primeira análise de leads
- Campanhas de contato direto
- Validação básica de dados
- Orçamento limitado

### 💰 Custo-benefício:
⭐⭐⭐⭐⭐ - Máximo retorno com investimento mínimo

### 🚀 Como executar:
```bash
python run_enrichment_real.py
# Escolha: 1 (para modo basic)
# Digite a quantidade de leads (ex: 10)
```

---

## 📊 MODO FULL - Análise Completa com IA

### 🎯 O que faz:
Além de todos os dados do modo BASIC, adiciona análise de negócio e insights estratégicos usando IA.

### 📊 Campos Gerados (16 novos campos):
**Todos do BASIC +**
- **segmento_negocio** - Classificação do segmento de atuação
- **porte_empresa** - Estimativa do tamanho da empresa
- **potencial_crescimento** - Análise do potencial (Alto/Médio/Baixo)
- **insight_principal** - Principal descoberta sobre a empresa
- **recomendacao_abordagem** - Estratégia recomendada de vendas

### 💡 Ideal para:
- Equipes de vendas B2B
- Análise de mercado
- Segmentação avançada
- Estratégias personalizadas

### 💰 Custo-benefício:
⭐⭐⭐⭐ - Excelente para vendas consultivas

### 🚀 Como executar:
```bash
python run_enrichment_real.py
# Escolha: 2 (para modo full)
# Digite a quantidade de leads (ex: 5)
```

---

## 💎 MODO PREMIUM - Inteligência Avançada

### 🎯 O que faz:
Oferece o pacote completo com métricas avançadas, scoring e análise preditiva.

### 📊 Campos Gerados (19 novos campos):
**Todos do FULL +**
- **score_qualidade** - Score de 0-100 da qualidade do lead
- **probabilidade_conversao** - Percentual estimado de conversão
- **valor_estimado_lead** - Valor monetário estimado do lead

### 💡 Ideal para:
- Grandes operações de vendas
- Análise preditiva
- Priorização de leads
- ROI máximo

### 💰 Custo-benefício:
⭐⭐⭐ - Premium para resultados premium

### 🚀 Como executar:
```bash
python run_enrichment_real.py
# Escolha: 3 (para modo premium)
# Digite a quantidade de leads (ex: 3)
```

---

## 📊 Comparação Rápida dos Modos

| Característica | BASIC | FULL | PREMIUM |
|---------------|-------|------|---------|
| **Novos campos** | 11 | 16 | 19 |
| **Contatos** | ✅ | ✅ | ✅ |
| **Redes Sociais** | ✅ | ✅ | ✅ |
| **Análise IA** | ❌ | ✅ | ✅ |
| **Segmentação** | ❌ | ✅ | ✅ |
| **Scoring** | ❌ | ❌ | ✅ |
| **Valor do Lead** | ❌ | ❌ | ✅ |
| **Tempo/lead** | ~1s | ~1.5s | ~2s |
| **Preço** | $ | $$ | $$$ |

---

## 🎮 Guia Passo a Passo

### 1️⃣ Preparação
```bash
# Certifique-se de estar no diretório correto
cd C:\workspace\aura-nexus-clean

# Verifique se o arquivo de leads existe
dir data\input\leads.xlsx
```

### 2️⃣ Execução Interativa
```bash
# Execute o script
python run_enrichment_real.py

# O sistema irá perguntar:
# 1. Escolha o modo (1-3)
# 2. Quantos leads processar
```

### 3️⃣ Execução Automática
```bash
# Modo BASIC com 10 leads
echo 1 10 | python run_enrichment_real.py

# Modo FULL com 5 leads  
echo 2 5 | python run_enrichment_real.py

# Modo PREMIUM com 3 leads
echo 3 3 | python run_enrichment_real.py
```

### 4️⃣ Localizar Resultados
Os arquivos são salvos em:
```
data/output/enrichment_real_[modo]_[timestamp].xlsx
```

---

## 💡 Dicas de Uso

### Para Iniciantes:
1. Comece com **BASIC** para entender o sistema
2. Teste com poucos leads (3-5)
3. Analise os resultados antes de escalar

### Para Vendas:
1. Use **FULL** para ter insights de abordagem
2. Processe em lotes de 20-50 leads
3. Exporte para CRM após validação

### Para Análise Avançada:
1. Use **PREMIUM** para priorização
2. Foque nos leads com score > 70
3. Cruze dados com histórico de vendas

---

## 📈 Exemplos de Output

### BASIC:
```
Lead: Tech Solutions
- Email: techsolu@gmail.com
- Telefone: (11) 91234-5678
- Instagram: @techsolutions (1234 seguidores)
```

### FULL:
```
Lead: Tech Solutions
- [Todos os dados do BASIC]
- Segmento: Tecnologia
- Porte: Pequeno (10-50 funcionários)
- Potencial: Alto
- Abordagem: Consultiva focada em inovação
```

### PREMIUM:
```
Lead: Tech Solutions
- [Todos os dados do FULL]
- Score de Qualidade: 85/100
- Probabilidade de Conversão: 72%
- Valor Estimado: R$ 4.250,00
```

---

## ⚡ Performance

- **BASIC**: ~1 segundo por lead
- **FULL**: ~1.5 segundos por lead
- **PREMIUM**: ~2 segundos por lead

Recomendamos processar:
- BASIC: até 100 leads por vez
- FULL: até 50 leads por vez
- PREMIUM: até 25 leads por vez

---

## 🆘 Solução de Problemas

### Erro de arquivo não encontrado:
```bash
# Verifique se o arquivo existe
dir data\input\*.xlsx
```

### Erro de encoding:
```bash
# Use o script sem emojis
python run_enrichment_real.py
```

### Memória insuficiente:
```bash
# Reduza a quantidade de leads
# Use lotes menores (ex: 10 em vez de 100)
```

---

**Última atualização:** 31/07/2025  
**Versão:** 1.0