# Changelog

Todas as mudanças importantes deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [31.0.0] - 2025-01-30

### Adicionado
- Estrutura profissional de projeto para Git
- Multi-LLM Consensus com DataReviewAgent integrado
- Sistema completo de 11 features no modo FULL_STRATEGY
- Social Media Scraping com suporte Apify dual
- Documentação completa e plano de ação
- Notebooks v30 e v31 preservados

### Corrigido
- Removido override problemático do process_lead
- Restauradas todas as features originais
- Corrigido mapeamento de campos sociais
- APIs corretamente conectadas ao processor

### Alterado
- Reorganização completa do código em estrutura modular
- Separação clara entre core, features e infrastructure
- Migração de células para módulos Python apropriados

## [30.0.0] - 2025-01-29

### Problemas Identificados
- Override incorreto do process_lead
- Apenas 3 de 11 features executando
- Taxa de execução: 27%

## [29.0.0] - 2025-01-28

### Estado Inicial
- Taxa de sucesso: 0%
- Processamento de apenas 5/34 leads
- Features não executando corretamente