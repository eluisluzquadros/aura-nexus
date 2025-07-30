# AURA NEXUS - Sistema Avancado de Enriquecimento de Leads

## Overview

AURA NEXUS e um sistema modular para enriquecimento automatizado de leads empresariais.

### Features Principais

- Multi-API Integration (Google Maps, OpenAI, Apify, etc.)
- Multi-LLM Consensus (GPT, Claude, Gemini)
- Social Media Scraping (Instagram, Facebook, LinkedIn)
- Data Review Agent (Validacao automatica)
- Discovery Cycle (Busca recursiva)

## Quick Start

```bash
# Instalar
pip install -r requirements.txt

# Configurar
cp .env.example .env
# Editar .env com suas chaves

# Executar
python scripts/process_leads.py --input leads.xlsx
```

## Documentacao

- [Instalacao](docs/guides/installation.md)
- [Configuracao](docs/guides/configuration.md)
- [Arquitetura](docs/architecture/system_design.md)

## Licenca

MIT License
