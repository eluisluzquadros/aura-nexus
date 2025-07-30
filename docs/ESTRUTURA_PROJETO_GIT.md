# 📁 ESTRUTURA DO PROJETO AURA NEXUS PARA GIT

## 🎯 Estrutura Proposta

```
aura-nexus/
├── 📁 src/                          # Código fonte principal
│   ├── 📁 core/                     # Células principais
│   │   ├── __init__.py
│   │   ├── api_manager.py           # Célula 00
│   │   ├── response_models.py       # Célula 02
│   │   ├── multi_llm_consensus.py   # Célula 03
│   │   ├── lead_processor.py        # Célula 10
│   │   └── orchestrator.py          # Célula 11
│   │
│   ├── 📁 features/                 # Features específicas
│   │   ├── __init__.py
│   │   ├── contact_extraction.py    # Célula 04
│   │   ├── web_scraping.py          # Célula 06
│   │   ├── review_analysis.py       # Célula 07
│   │   ├── social_scraping.py       # Célula 16
│   │   ├── discovery_cycle.py       # Célula 17
│   │   ├── google_cse.py            # Célula 18
│   │   └── data_review_agent.py     # Célula 19
│   │
│   ├── 📁 infrastructure/           # Infraestrutura
│   │   ├── __init__.py
│   │   ├── cache_system.py          # Célula 08
│   │   ├── checkpoint_manager.py    # Célula 09
│   │   ├── performance_monitor.py   # Performance
│   │   └── logging_config.py        # Logs
│   │
│   └── 📁 utils/                    # Utilitários
│       ├── __init__.py
│       ├── validators.py
│       ├── formatters.py
│       └── constants.py
│
├── 📁 notebooks/                    # Jupyter Notebooks
│   ├── 01_quickstart.ipynb         # Tutorial inicial
│   ├── 02_full_example.ipynb       # Exemplo completo
│   ├── 03_api_configuration.ipynb  # Config de APIs
│   └── 📁 legacy/                   # Notebooks antigos
│       ├── AURA_NEXUS_v30.ipynb
│       └── AURA_NEXUS_v31.ipynb
│
├── 📁 scripts/                      # Scripts executáveis
│   ├── process_leads.py             # Script principal
│   ├── test_apis.py                 # Testar APIs
│   ├── export_results.py            # Exportar resultados
│   └── setup_environment.py         # Setup inicial
│
├── 📁 tests/                        # Testes unitários
│   ├── 📁 unit/
│   │   ├── test_api_manager.py
│   │   ├── test_lead_processor.py
│   │   └── test_multi_llm.py
│   │
│   ├── 📁 integration/
│   │   ├── test_full_pipeline.py
│   │   └── test_api_integration.py
│   │
│   └── 📁 fixtures/                 # Dados de teste
│       └── sample_leads.xlsx
│
├── 📁 docs/                         # Documentação
│   ├── 📁 api/                      # Documentação da API
│   ├── 📁 guides/                   # Guias
│   │   ├── installation.md
│   │   ├── configuration.md
│   │   └── troubleshooting.md
│   │
│   ├── 📁 architecture/             # Arquitetura
│   │   ├── system_design.md
│   │   ├── data_flow.md
│   │   └── components.md
│   │
│   └── 📁 features/                 # Features detalhadas
│       ├── multi_llm_consensus.md
│       ├── social_scraping.md
│       └── data_review_agent.md
│
├── 📁 config/                       # Configurações
│   ├── default_config.yaml          # Config padrão
│   ├── feature_modes.yaml           # Modos de features
│   └── api_endpoints.yaml           # Endpoints das APIs
│
├── 📁 data/                         # Dados (não versionados)
│   ├── 📁 input/                    # Planilhas de entrada
│   ├── 📁 output/                   # Resultados
│   ├── 📁 cache/                    # Cache
│   └── 📁 logs/                     # Logs
│
├── 📁 docker/                       # Docker configs
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 📁 .github/                      # GitHub Actions
│   └── 📁 workflows/
│       ├── tests.yml
│       ├── lint.yml
│       └── deploy.yml
│
├── .gitignore                       # Ignorar arquivos
├── .env.example                     # Exemplo de variáveis
├── requirements.txt                 # Dependências Python
├── setup.py                         # Setup do pacote
├── README.md                        # README principal
├── CHANGELOG.md                     # Histórico de mudanças
├── LICENSE                          # Licença
└── pyproject.toml                   # Config do projeto
```

## 🚀 Plano de Migração

### Fase 1: Preparação (1 dia)
1. **Backup completo** do projeto atual
2. **Criar novo diretório** com estrutura limpa
3. **Identificar** código de produção vs experimental

### Fase 2: Reorganização (2-3 dias)
1. **Separar células** em módulos Python apropriados
2. **Refatorar imports** para nova estrutura
3. **Criar __init__.py** com exports corretos
4. **Mover notebooks** para pasta específica

### Fase 3: Documentação (1-2 dias)
1. **README.md principal** com overview completo
2. **Documentação de cada módulo**
3. **Guias de instalação e uso**
4. **Exemplos práticos**

### Fase 4: Testes (2-3 dias)
1. **Criar testes unitários** básicos
2. **Testes de integração** do pipeline
3. **CI/CD** com GitHub Actions

### Fase 5: Git Setup (1 dia)
1. **Inicializar repositório**
2. **Configurar .gitignore**
3. **Primeiro commit** organizado
4. **Criar branches** de desenvolvimento

## 📝 .gitignore Recomendado

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Dados e logs
data/output/
data/cache/
data/logs/
*.log
*.xlsx
!data/fixtures/*.xlsx

# Segurança
.env
*.key
credentials.json
service_account.json

# OS
.DS_Store
Thumbs.db

# Temporários
temp/
tmp/
*.tmp
```

## 🔧 Configuração Inicial

### 1. requirements.txt
```txt
# Core
pandas>=1.5.0
numpy>=1.19.0
openpyxl>=3.0.0

# APIs
googlemaps>=4.10.0
openai>=1.0.0
anthropic>=0.18.0
google-generativeai>=0.4.0
apify-client>=1.5.0

# Web Scraping
beautifulsoup4>=4.12.0
lxml>=4.9.0
aiohttp>=3.8.0

# Utils
python-dotenv>=1.0.0
pyyaml>=6.0
validators>=0.20.0
phonenumbers>=8.13.0

# ML/Data Science
scikit-learn>=1.0.0
tiktoken>=0.5.0

# Development
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

### 2. README.md Principal
```markdown
# 🌟 AURA NEXUS - Sistema Avançado de Enriquecimento de Leads

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)

## 🎯 Overview

AURA NEXUS é um sistema de enriquecimento de leads que utiliza múltiplas APIs e técnicas de IA para coletar e analisar dados de empresas.

### ✨ Features Principais

- 🔍 **Multi-API Integration**: Google Maps, OpenAI, Apify, etc.
- 🤖 **Multi-LLM Consensus**: Análise com múltiplas IAs
- 📱 **Social Media Scraping**: Instagram, Facebook, LinkedIn
- ✅ **Data Review Agent**: Validação automática de dados
- 🔄 **Discovery Cycle**: Busca recursiva inteligente

## 🚀 Quick Start

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/aura-nexus.git
cd aura-nexus

# Instalar dependências
pip install -r requirements.txt

# Configurar APIs
cp .env.example .env
# Editar .env com suas chaves

# Executar
python scripts/process_leads.py --input data/input/leads.xlsx
```

## 📖 Documentação

- [Guia de Instalação](docs/guides/installation.md)
- [Configuração de APIs](docs/guides/configuration.md)
- [Arquitetura do Sistema](docs/architecture/system_design.md)
- [Troubleshooting](docs/guides/troubleshooting.md)

## 🤝 Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

## 📄 Licença

Este projeto está sob a licença MIT - veja [LICENSE](LICENSE) para detalhes.
```

## 🎯 Benefícios da Nova Estrutura

1. **Organização Clara**: Separação entre código, docs, testes
2. **Manutenibilidade**: Fácil localizar e modificar componentes
3. **Escalabilidade**: Estrutura preparada para crescimento
4. **Profissionalismo**: Padrões da indústria
5. **CI/CD Ready**: Preparado para automação
6. **Colaboração**: Fácil para novos desenvolvedores

## 📋 Próximos Passos

1. **Decidir** sobre a estrutura proposta
2. **Criar** novo repositório Git
3. **Migrar** código gradualmente
4. **Testar** cada componente
5. **Documentar** durante o processo
6. **Publicar** no GitHub