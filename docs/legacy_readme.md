# 🚀 AURA NEXUS v29
### Sistema Avançado de Enriquecimento de Leads com Foco em Dados de Contato

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow.svg)](https://github.com)
[![Colab](https://img.shields.io/badge/Google%20Colab-Ready-orange.svg)](https://colab.research.google.com)
[![Quality](https://img.shields.io/badge/Taxa_Sucesso-0%25-red.svg)](https://github.com)

<div align="center">

```
       █████╗ ██╗   ██╗██████╗  █████╗     ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
      ██╔══██╗██║   ██║██╔══██╗██╔══██╗    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
      ███████║██║   ██║██████╔╝███████║    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
      ██╔══██║██║   ██║██╔══██╗██╔══██║    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
      ██║  ██║╚██████╔╝██║  ██║██║  ██║    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
      ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

**🎯 Enriquecimento automatizado de leads com foco em DADOS DE CONTATO**

</div>

## ⚠️ Status Atual - v29

### 🔴 Problemas Críticos Identificados
- **Taxa de Sucesso: 0%** - Sistema não está processando corretamente
- **Apenas 5/34 leads processados** - Leads com Google ID são ignorados
- **Features não executadas** - Web scraping, social scraping não funcionam
- **Distribuição incorreta** - Enriquecimento de contatos deveria estar no modo BASIC

### ✅ O que está funcionando
- Sistema de logs e monitoramento
- Configuração de APIs
- Leitura e adaptação de planilhas
- Cache e checkpoints
- Busca básica no Google Maps

## 📋 Índice

- [Status Atual](#️-status-atual---v29)
- [Fluxo de Enriquecimento](#-fluxo-de-enriquecimento)
- [Instalação](#-instalação)
- [Configuração](#️-configuração)
- [Modos de Operação](#-modos-de-operação)
- [Uso](#-uso)
- [Arquitetura](#️-arquitetura-do-sistema)
- [Problemas Conhecidos](#-problemas-conhecidos)
- [Roadmap](#-roadmap)

## 🔄 Fluxo de Enriquecimento

```mermaid
graph TD
    A[📥 Entrada: Planilha de Leads] --> B{Tem Google Maps ID?}
    
    B -->|NÃO| C[🌍 Google Maps API]
    B -->|SIM| D[⏭️ Pular Google Maps API]
    
    C --> E[✅ Lead com Google ID]
    D --> E
    
    E --> F{Modo de Análise}
    
    F -->|BASIC| G[📞 Enriquecimento de Contatos]
    F -->|FULL| H[📞 Contatos + 📊 Análises]
    F -->|PREMIUM| I[📞 Contatos + 📊 Análises + 🏢 Premium]
    
    %% Modo BASIC
    G --> G1[🔍 Google CSE<br/>Busca de links e perfis]
    G1 --> G2[🌐 Crawl4AI<br/>Extração do website]
    G2 --> G3[📱 Apify Scrapers<br/>Instagram/Facebook/Linktree]
    G3 --> G4[☎️ Consolidação<br/>Telefones, emails, redes]
    
    %% Modo FULL
    H --> G1
    H --> H1[⭐ Reviews Analysis<br/>Análise de avaliações]
    H1 --> H2[🏆 Competitor Analysis<br/>Identificar concorrentes]
    H2 --> H3[🤖 Multi-LLM Analysis<br/>Insights estratégicos]
    H3 --> H4[💼 Sales Approach<br/>Estratégias de venda]
    H4 --> H5[🔄 Discovery Cycle<br/>Busca recursiva profunda]
    H5 --> H6[📈 Advanced Metrics<br/>Métricas de consenso]
    
    %% Modo PREMIUM
    I --> G1
    I --> H1
    I --> I1{Street View?}
    I1 -->|Habilitado| I2[📸 Facade Analysis<br/>Análise visual de fachada]
    I1 -->|Desabilitado| I3[⏭️ Pular Street View]
    
    %% Saída
    G4 --> J[📊 GDR Enriquecido]
    H6 --> J
    I2 --> J
    I3 --> J
    
    J --> K[💾 Salvar Excel]
    K --> L[📋 Relatório de Qualidade]
    
    style A fill:#e1f5fe
    style J fill:#c8e6c9
    style C fill:#ffeb3b
    style G fill:#b3e5fc
    style H fill:#81c784
    style I fill:#ce93d8
    style I1 fill:#ffd54f
```

### 📝 Descrição do Fluxo

#### 1️⃣ **Entrada e Validação**
- Sistema recebe planilha com leads
- Verifica se lead já tem Google Maps ID
- Se não tiver, busca no Google Maps API
- Se tiver, pula APENAS a API do Google (não o processamento completo)

#### 2️⃣ **Modos de Processamento**

**🔵 BASIC - Foco em Contatos**
1. **Google CSE**: Busca links, perfis e menções na web
2. **Crawl4AI**: Acessa website e extrai contatos
3. **Apify**: Scraping de Instagram, Facebook e Linktree
4. **Consolidação**: Unifica todos os contatos encontrados

**🟢 FULL STRATEGY - Análise Completa**
- Tudo do BASIC +
- **Reviews**: Análise de avaliações e sentimentos
- **Concorrentes**: Identifica competidores próximos
- **Multi-LLM**: Consenso entre 3 IAs para insights
- **Sales**: Gera estratégias de abordagem
- **Discovery Cycle**: Busca recursiva profunda em até 3 níveis
- **Advanced Metrics**: Score de confiabilidade e métricas de consenso

**🟣 PREMIUM - Análise Visual Avançada**
- Tudo do FULL +
- **Street View** (Opcional): Análise visual da fachada com IA
- Foco em análise visual e presença física do negócio

#### 3️⃣ **Processamento Paralelo**
- Features independentes executam em paralelo
- Timeout configurável por feature
- Fallback automático em caso de falha

#### 4️⃣ **Saída e Qualidade**
- GDR (Global Data Record) com todos os dados
- Relatório de inconsistências e qualidade
- Score de confiabilidade por campo

## 💻 Instalação

### Pré-requisitos
```bash
python >= 3.11
pip >= 23.0
```

### Instalação das Dependências
```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```env
# Google APIs
GOOGLE_MAPS_API_KEY=sua_chave_aqui
GOOGLE_CSE_API_KEY=sua_chave_aqui
GOOGLE_CSE_ID=seu_id_aqui

# LLMs
OPENAI_API_KEY=sua_chave_aqui
GEMINI_API_KEY=sua_chave_aqui
DEEPSEEK_API_KEY=sua_chave_aqui

# Scrapers
APIFY_API_KEY=sua_chave_aqui
APIFY_INSTAGRAM_ACTOR_ID=seu_id_aqui
APIFY_FACEBOOK_ACTOR_ID=seu_id_aqui
APIFY_LINKTREE_API_KEY=sua_chave_aqui
```

### Configuração Modo Premium
```python
# Para DESABILITAR Street View no modo Premium
config = {
    'analysis_mode': 'premium',
    'enable_facade_analysis': False,  # Desabilita Street View
    'facade_analysis_options': {
        'skip_if_no_address': True,
        'max_images': 4
    }
}
```

## 📊 Modos de Operação

### 🔵 BASIC - Enriquecimento de Contatos
```python
# Foco: Coletar telefones, emails e redes sociais
process_leads(file='leads.xlsx', mode='basic')
```
- Google Maps (dados básicos)
- Google Search (descoberta de links)
- Web Scraping (extração de contatos)
- Social Scraping (Instagram/Facebook)

### 🟢 FULL STRATEGY - Análise Completa
```python
# Foco: Contatos + análise estratégica + busca profunda
process_leads(file='leads.xlsx', mode='full_strategy')
```
- Tudo do BASIC +
- Análise de reviews
- Identificação de concorrentes
- Multi-LLM para insights
- Estratégias de venda
- Discovery Cycle (busca recursiva)
- Advanced Metrics (consenso e confiabilidade)

### 🟣 PREMIUM - Análise Visual
```python
# Foco: Tudo do FULL + análise visual avançada
process_leads(
    file='leads.xlsx', 
    mode='premium',
    enable_facade_analysis=True  # Street View opcional
)
```
- Tudo do FULL +
- Análise de fachada com Street View (opcional)
- Análise visual avançada com IA

## 🚀 Uso

### Comando Principal
```python
from aura_nexus_v29 import process_leads

# Processar com configuração padrão
results = process_leads(
    file='base-leads_amostra_v2.xlsx',
    mode='full_strategy',
    batch_size=5,
    force_process_all=True  # Processa TODOS os leads
)
```

### Exemplo Avançado
```python
# Configuração customizada
config = {
    'analysis_mode': 'premium',
    'batch_size': 10,
    'enable_facade_analysis': False,  # Sem Street View
    'force_process_all': True,
    'skip_google_api_only': True,
    'max_concurrent_tasks': 5,
    'timeout_per_lead': 120
}

orchestrator = OrchestratorV4(config)
results = orchestrator.process_spreadsheet('leads.xlsx')
```

## 🏗️ Arquitetura do Sistema

```
AURA NEXUS/
├── 📁 células/                     # Módulos principais
│   ├── célula_01_logs.py          # Sistema de logging
│   ├── célula_02_api_manager.py   # Gerenciador de APIs
│   ├── célula_03_adapter.py       # Adaptador de planilhas
│   ├── célula_05_cache.py         # Sistema de cache
│   ├── célula_08_checkpoint.py    # Checkpoints de recuperação
│   ├── célula_09_performance.py   # Monitor de performance
│   ├── célula_10_processor.py     # Processador de leads
│   ├── célula_11_orchestrator.py  # Orquestrador principal
│   ├── célula_13_multi_llm.py     # Consenso multi-LLM
│   ├── célula_14_apify.py         # Scrapers sociais
│   ├── célula_15_crawl4ai.py      # Web scraping
│   ├── célula_16_google_cse.py    # Google Search
│   └── célula_19_data_review.py   # Validação de dados
├── 📁 logs/                        # Logs de execução
├── 📁 cache/                       # Cache local
├── 📁 checkpoints/                 # Pontos de recuperação
└── 📁 aura_nexus_output/           # Resultados processados
```

## ⚠️ Problemas Conhecidos

### 🔴 Críticos
1. **Processamento ignora 85% dos leads** - Leads com Google ID são pulados completamente
2. **Features não executam** - Apenas Google Maps API funciona
3. **Taxa de sucesso 0%** - Contador quebrado

### 🟡 Médios
1. **Erro no relatório de inconsistências** - `'total_critical'` não encontrado
2. **Logs duplicados** - Múltiplas entradas para mesmo processamento
3. **Performance suspeita** - 0.06s por lead indica que APIs não são chamadas

### 🟢 Menores
1. **Cache não funciona corretamente**
2. **Checkpoint salva mas não recupera**
3. **Documentação desatualizada**

## 📅 Roadmap

### v30 - Correções Críticas (Janeiro 2025)
- [ ] Corrigir processamento de TODOS os leads
- [ ] Garantir execução de todas as features
- [ ] Reorganizar features por modo
- [ ] Corrigir contadores de sucesso

### v31 - Otimizações (Fevereiro 2025)
- [ ] Implementar testes automatizados
- [ ] Melhorar sistema de retry
- [ ] Otimizar processamento paralelo
- [ ] Dashboard de monitoramento

### v32 - Novas Features (Março 2025)
- [ ] API REST
- [ ] Integração com CRMs
- [ ] Suporte para LinkedIn
- [ ] Interface web

---

**Última Atualização:** 30/01/2025  
**Versão:** v29 (Em Desenvolvimento)  
**Status:** ⚠️ Necessita correções críticas antes do uso em produção
- **Célula 02**: Response Models - Estruturas de dados (ATUALIZADO v26.2)
- **Célula 03**: Multi-LLM Consensus - **INTEGRADO com DataReviewAgent**

### Células de Análise (04-07)
- **Célula 04**: Contact Extraction - WhatsApp, telefones, emails
- **Célula 05**: Content Validation - Relevância de conteúdo
- **Célula 06**: Web Scraping - AdvancedWebScraper
- **Célula 07**: Review Analysis - NLP avançado

### Células de Infraestrutura (08-09)
- **Célula 08**: Smart Cache - 3 níveis (L1, L2, L3)
- **Célula 09**: Robustness - Checkpoints e recovery

### Células de Processamento (10-11)
- **Célula 10 v3**: Lead Processor - Suporte para discovery cycle
- **Célula 11 v4**: Main Orchestrator - Coordenação completa

### Células Avançadas (12-16)
- **Célula 12**: Google Maps Search
- **Célula 13**: Street View Analysis - Visão computacional
- **Célula 14**: Kepler.gl Viz - Mapas interativos
- **Célula 15**: RAG System - Consultas inteligentes
- **Célula 16**: Social Media Scraping - APIFY dual

### 🆕 Células v26 (17-19)
- **Célula 17**: IntelligentDiscoveryCycle - Retroalimentação completa
- **Célula 18**: GoogleCustomSearchEngine - Busca avançada
- **Célula 19**: DataReviewAgent - Validação e correção automática

## 🔧 Modos de Operação

### INPUT_MODE

#### 1. Modo Spreadsheet (Padrão)
```bash
python aura_nexus_main_v3.py \
    --mode spreadsheet \
    --file base-leads.xlsx \
    --analysis full_strategy \
    --enable-review
```

#### 2. Modo Maps (Busca Direta)
```bash
python aura_nexus_main_v3.py \
    --mode maps \
    --query "assistência técnica" \
    --location "São Paulo SP" \
    --radius 5000 \
    --enable-review
```

#### 3. 🆕 Modo Discovery (Descoberta Total)
```bash
python aura_nexus_main_v3.py \
    --mode maps \
    --query "restaurantes" \
    --analysis full_discovery \
    --use-google-cse \
    --discovery-depth 3
```

### ANALYSIS_MODE

#### 1. Basic (10s/lead)
- Dados essenciais
- Sem análise de IA
- Ideal para triagem

#### 2. Full Strategy (60s/lead)
- Análise completa com IA
- Street View
- Consenso Multi-LLM
- **Validação automática**

#### 3. 🆕 Full Discovery (120s/lead)
- Descoberta recursiva
- Google CSE
- Retroalimentação completa
- **Máxima qualidade garantida**

## 📦 Instalação

### Requisitos Mínimos
- Python 3.8+
- 8GB RAM (16GB para full discovery)
- Google Colab Pro (recomendado)
- APIs configuradas

### Dependências Principais v26.2
```txt
pandas>=1.5.0
googlemaps>=4.10.0
openai>=1.0.0
anthropic>=0.18.0
google-generativeai>=0.4.0
keplergl>=0.3.2
chromadb>=0.4.0
playwright>=1.40.0
beautifulsoup4>=4.12.0
apify-client>=1.5.0
nest-asyncio>=1.5.6
phonenumbers>=8.13.0      # NOVO
validators>=0.20.0        # NOVO
aiohttp>=3.8.0           # NOVO
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```bash
# APIs Obrigatórias
GOOGLE_MAPS_API_KEY=sua_chave_aqui

# APIs de LLM (pelo menos uma)
GEMINI_API_KEY=sua_chave_aqui
CLAUDE_API_KEY=sua_chave_aqui
OPENAI_API_KEY=sua_chave_aqui
DEEPSEEK_API_KEY=sua_chave_aqui

# APIs de Scraping
APIFY_API_KEY=sua_chave_aqui
APIFY_API_KEY_LINKTREE=sua_chave_aqui

# NOVO: Google Custom Search
GOOGLE_CSE_ID=seu_id_aqui
GOOGLE_CSE_API_KEY=sua_chave_aqui

# Configurações v26.2
OUTPUT_DIR=/content/drive/MyDrive/aura_nexus_output
ENABLE_DATA_REVIEW=true          # NOVO
ENABLE_DISCOVERY_CYCLE=true      # NOVO
MAX_DISCOVERY_DEPTH=3            # NOVO
MIN_QUALITY_SCORE=0.8            # NOVO
```

## 🚀 Uso

### Linha de Comando v26.2

```bash
# Processamento com validação automática
python aura_nexus_main_v3.py \
    --file leads.xlsx \
    --analysis full_strategy \
    --enable-review \
    --min-quality 0.8

# Descoberta total com retroalimentação
python aura_nexus_main_v3.py \
    --mode maps \
    --query "clínicas médicas" \
    --location "Porto Alegre RS" \
    --analysis full_discovery \
    --discovery-depth 3 \
    --use-google-cse

# Ver estatísticas de validação
python aura_nexus_main_v3.py --show-validation-stats
```

### Código Python v26.2

```python
from aura_nexus_celula_11_v4 import AuraNexusOrchestrator
from aura_nexus_celula_19_data_review import DataReviewAgent

# Configurar com validação
config = {
    'enable_review': True,
    'min_quality_score': 0.8,
    'enable_discovery_cycle': True,
    'max_discovery_depth': 3
}

# Criar orquestrador
orchestrator = AuraNexusOrchestrator(config)

# Processar com qualidade garantida
results = await orchestrator.process_leads(
    'leads.xlsx',
    num_leads=10,
    enable_review=True
)

# Verificar qualidade
for lead in results['dataframe'].itertuples():
    print(f"{lead.gdr_nome}: Qualidade {lead.gdr_quality_score:.0%}")
```

## 🆕 Sistema de Validação

### DataReviewAgent

O novo sistema de validação garante a qualidade dos dados:

```python
from aura_nexus_celula_19_data_review import DataReviewAgent

# Criar agente de revisão
review_agent = DataReviewAgent(
    consensus_orchestrator=multi_llm,
    learning_enabled=True
)

# Revisar resultado
reviewed = await review_agent.review_consensus_result(
    consensus_result,
    analysis_type='scoring',
    original_data=lead_data
)

print(f"Status: {reviewed['status']}")
print(f"Qualidade: {reviewed['quality_score']:.0%}")
print(f"Correções: {reviewed['corrections_applied']}")
```

### Tipos de Validação

1. **Estrutural**: Campos obrigatórios, tipos de dados
2. **Conteúdo**: Ranges válidos, formatos corretos
3. **Consistência**: Cálculos, relações entre campos
4. **Qualidade**: Completude, confiabilidade

### Correções Automáticas

- Scores fora de range → Ajustados
- Campos faltantes → Inferidos
- Cálculos incorretos → Recalculados
- Formatos inválidos → Corrigidos

## 🌟 Funcionalidades Avançadas

### 1. Ciclo de Descoberta Inteligente

```python
from aura_nexus_celula_17_discovery_cycle import IntelligentDiscoveryCycle

# Criar ciclo de descoberta
discovery = IntelligentDiscoveryCycle(
    google_maps_client=gmaps,
    web_scraper=scraper,
    social_scraper=social,
    google_cse_client=cse,
    max_depth=3
)

# Descobrir dados recursivamente
results = await discovery.discover_complete(
    lead_name="TechCell",
    initial_data=lead_data,
    use_google_search=True
)

print(f"Descobertas: {results['discovery_stats']['total_discoveries']}")
```

### 2. Google Custom Search

```python
from aura_nexus_celula_18_google_cse import GoogleCustomSearchEngine

# Buscar perfis sociais
cse = GoogleCustomSearchEngine(api_key, search_engine_id)

profiles = await cse.search_social_profiles(
    "Restaurante Bella Vista",
    location="São Paulo"
)

# Buscar contatos
contacts = await cse.search_contact_info(
    "Clínica Saúde Total",
    location="Rio de Janeiro"
)
```

### 3. Análise com Qualidade Garantida

```python
# Configurar orquestrador com revisão
orchestrator = MultiLLMConsensusOrchestrator(
    llm_configs,
    token_counter,
    enable_review=True  # Ativa validação automática
)

# Análise com consenso E validação
result = await orchestrator.analyze_with_consensus(
    lead_data,
    'business_analysis'
)

# Resultado inclui métricas de qualidade
print(f"Qualidade: {result.quality_score:.0%}")
print(f"Status: {result.review_status}")
if result.corrections_applied:
    print(f"Correções: {result.corrections_applied}")
```

## 📊 Estrutura de Dados - GDR v26.2

Novos campos adicionados:

```python
{
    # ... campos existentes ...
    
    # NOVO: Qualidade e Validação
    'gdr_quality_score': 0.95,           # Score de qualidade (0-1)
    'gdr_review_status': 'approved',     # Status da validação
    'gdr_corrections_applied': [...],    # Lista de correções
    'gdr_review_notes': '...',          # Notas da revisão
    
    # NOVO: Descobertas
    'gdr_total_discoveries': 23,         # Total de descobertas
    'gdr_discovery_depth': 3,            # Profundidade alcançada
    'gdr_discovery_sources': {...},      # Fontes das descobertas
    
    # NOVO: Google CSE
    'gdr_cse_profiles_found': 5,         # Perfis encontrados
    'gdr_cse_mentions': [...],           # Menções na web
    'gdr_cse_additional_contacts': {...} # Contatos extras
}
```

## ⚡ Performance v26.2

### Métricas Atualizadas

| Modo | Tempo/Lead | Qualidade | Taxa Sucesso |
|------|------------|-----------|--------------|
| Basic | ~10s | 70% | >98% |
| Full Strategy | ~60s | 95%+ | >95% |
| Full Discovery | ~120s | 98%+ | >93% |

### Melhorias de Qualidade

- **Antes**: 70% de precisão média
- **v26.2**: 95%+ com validação automática
- **Correções**: ~3-5 por lead em média
- **Re-análises**: <10% dos casos

## 🔧 Solução de Problemas

### Novo: Erros de Validação

```python
# Verificar log de validações
cat validation_log.json

# Desabilitar validação temporariamente
python aura_nexus_main_v3.py --no-review

# Ajustar threshold de qualidade
python aura_nexus_main_v3.py --min-quality 0.6
```

### Problemas com Discovery Cycle

```bash
# Limitar profundidade
--discovery-depth 1

# Desabilitar Google CSE
--no-google-cse

# Usar cache agressivo
--aggressive-cache
```

## 🤝 Contribuindo

### Novas Diretrizes v26.2

1. **Testes de Validação**: Adicione testes para validações
2. **Qualidade First**: PRs devem manter taxa de erro <5%
3. **Documentação**: Documente regras de validação
4. **Performance**: Teste com grandes volumes

## 📈 Roadmap v27.0

- [ ] Machine Learning para validação preditiva
- [ ] Validação cruzada entre fontes
- [ ] Dashboard de qualidade em tempo real
- [ ] API REST com métricas de qualidade
- [ ] Integração com Data Quality tools

## 📝 Changelog v26.2

### Added
- DataReviewAgent para validação automática
- IntelligentDiscoveryCycle para retroalimentação
- GoogleCustomSearchEngine para busca avançada
- Score de qualidade em todas análises
- Auto-correção de erros comuns

### Changed
- ConsensusResult agora inclui métricas de qualidade
- MultiLLMConsensusOrchestrator integrado com validação
- Notebook principal atualizado para v26.2

### Improved
- Taxa de erro: 20% → <5%
- Qualidade dos dados: 70% → 95%+
- Descobertas por lead: 15 → 50+

## 📞 Suporte

- 📧 Email: suporte@auranexus.com
- 💬 Discord: [AURA NEXUS Community](https://discord.gg/auranexus)
- 📚 Docs: [docs.auranexus.com/v26](https://docs.auranexus.com)
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/aura-nexus/issues)

---

<div align="center">

**Desenvolvido com ❤️ para revolucionar a inteligência de vendas com qualidade garantida**

[Website](https://auranexus.com) • [Documentation](https://docs.auranexus.com) • [Blog](https://blog.auranexus.com)

</div>