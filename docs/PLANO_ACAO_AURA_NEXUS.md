# 📋 PLANO DE AÇÃO - AURA NEXUS v29
**Data:** 30/01/2025  
**Status:** ⚠️ CORREÇÕES URGENTES NECESSÁRIAS

---

## 🎯 OBJETIVO PRINCIPAL
Corrigir o sistema para processar 100% dos leads e executar TODAS as features de enriquecimento de contatos, com foco principal em telefones, emails e redes sociais.

---

## 🚨 PROBLEMAS CRÍTICOS A RESOLVER

### 1. **[P0] Processamento Ignora Leads com Google ID**
- **Problema:** Sistema pula COMPLETAMENTE leads que já têm Google Maps ID
- **Impacto:** 29 de 34 leads (85%) não são processados
- **Solução:** Modificar lógica para pular APENAS a API do Google Maps

### 2. **[P0] Features de Enriquecimento Não Executam**
- **Problema:** Apenas Google Maps API é executada
- **Impacto:** Sem coleta de contatos (objetivo principal)
- **Solução:** Garantir execução de TODAS as features ativas

### 3. **[P1] Distribuição Incorreta de Features por Modo**
- **Problema:** Enriquecimento de contatos está no modo PREMIUM
- **Impacto:** Modo BASIC não cumpre objetivo principal
- **Solução:** Reorganizar features conforme requisitos

### 4. **[P1] Taxa de Sucesso Sempre 0%**
- **Problema:** Contador de sucesso não funciona
- **Impacto:** Impossível medir efetividade
- **Solução:** Corrigir lógica de contabilização

---

## 📝 PLANO DE CORREÇÕES IMEDIATAS

### FASE 1: Correções Críticas (1-2 dias)

#### 1.1 Corrigir Orchestrator (célula_11_v4.py)
```python
# ANTES (ERRADO):
if row.get('gdr_ja_enriquecido_google', False) and skip_already_enriched:
    logger.info(f"⏭️ Lead {lead_data['nome_empresa']} já possui dados do Google")
    enriched = self._format_existing_data(row)
    results.append(enriched)
    continue  # PULA TODO O PROCESSAMENTO

# DEPOIS (CORRETO):
if row.get('gdr_ja_enriquecido_google', False):
    lead_data['skip_google_api'] = True  # Pula APENAS Google Maps API
    logger.info(f"⏭️ Lead {lead_data['nome_empresa']} - pulando apenas Google Maps API")

# Processa TODAS as outras features normalmente
enriched = await self.processor.process_lead(lead_data)
results.append(enriched)
```

#### 1.2 Reorganizar Features por Modo
```python
FEATURE_MODES = {
    'basic': {
        'google_details',      # Dados básicos Google Maps
        'google_cse',          # Google Search - descoberta de links
        'web_scraping',        # Crawl4AI - extração de contatos
        'social_scraping',     # Apify - Instagram/Facebook/Linktree
        'contact_extraction'   # Consolidação de contatos
    },
    'full_strategy': {
        # Tudo do basic +
        'reviews_analysis',    # Análise de avaliações
        'competitor_analysis', # Identificação de concorrentes
        'ai_analysis',         # Multi-LLM para insights
        'sales_approach',      # Estratégias de venda
        'discovery_cycle',     # Busca profunda recursiva (MOVIDO DO PREMIUM)
        'advanced_metrics'     # Métricas de consenso (MOVIDO DO PREMIUM)
    },
    'premium': {
        # Tudo do full +
        'facade_analysis'      # Google Street View (OPCIONAL)
        # Premium agora foca apenas em análise visual avançada
    }
}

# Configuração para modo Premium
premium_config = {
    'enable_facade_analysis': True,  # Pode ser False para pular Street View
    'facade_analysis_options': {
        'skip_if_no_address': True,
        'max_images': 4,
        'analyze_storefront': True,
        'analyze_signage': True
    }
}
```

#### 1.3 Garantir Execução das Features
```python
async def _process_lead(self, lead_data):
    # 1. Google Maps (se não tiver skip_google_api)
    if 'google_details' in self.active_features and not lead_data.get('skip_google_api'):
        await self._get_google_details()
    
    # 2. SEMPRE executar enriquecimento de contatos
    if 'google_cse' in self.active_features:
        await self._search_google_cse()  # Buscar links
    
    if 'web_scraping' in self.active_features:
        await self._scrape_website()  # Extrair contatos do site
    
    if 'social_scraping' in self.active_features:
        await self._scrape_social_media()  # Instagram/Facebook
    
    # 3. Consolidar todos os contatos encontrados
    await self._consolidate_contacts()
```

---

### FASE 2: Melhorias e Otimizações (3-5 dias)

#### 2.1 Implementar Sistema de Retry
- Retry automático para APIs que falharem
- Backoff exponencial para rate limits
- Fallback entre APIs similares

#### 2.2 Criar Testes Automatizados
- Testes unitários para cada célula
- Testes de integração end-to-end
- Testes de carga com 100+ leads

#### 2.3 Melhorar Logging e Debugging
- Log detalhado de cada feature executada
- Tempo de execução por feature
- Relatório de falhas por API

#### 2.4 Otimizar Performance
- Processamento paralelo de features independentes
- Cache mais agressivo para dados estáticos
- Batch requests onde possível

---

### FASE 3: Novas Funcionalidades (6-10 dias)

#### 3.1 Interface de Monitoramento
- Dashboard web para acompanhar processamento
- Estatísticas em tempo real
- Alertas de falhas

#### 3.2 API REST
- Endpoints para processar leads individuais
- Webhook para notificações
- Integração com CRMs

#### 3.3 Exportação Avançada
- Templates customizáveis
- Múltiplos formatos (JSON, CSV, XML)
- Integração direta com Google Sheets

---

## 📊 MÉTRICAS DE SUCESSO

### Após Correções da Fase 1:
- ✅ 100% dos leads processados (34/34)
- ✅ Taxa de sucesso > 80%
- ✅ Todas as features executando
- ✅ Tempo médio: 2-5s por lead

### Após Fase 2:
- ✅ 95%+ de uptime
- ✅ < 5% de falhas em APIs
- ✅ Cobertura de testes > 80%
- ✅ Performance 2x mais rápida

### Após Fase 3:
- ✅ Interface web funcional
- ✅ API REST documentada
- ✅ 3+ integrações com CRMs

---

## 🔧 COMANDOS PARA TESTAR CORREÇÕES

### 1. Testar com 1 lead específico
```python
python test_single_lead.py --cnpj="12345678000190" --mode="basic" --force-all-features
```

### 2. Testar processamento completo
```python
python aura_nexus_v30.py \
    --file="base-leads_amostra_v2.xlsx" \
    --mode="basic" \
    --force-process-all \
    --skip-google-api-only \
    --debug
```

### 3. Validar features executadas
```python
python validate_features.py --check-logs --show-execution-time
```

---

## 📅 CRONOGRAMA

| Fase | Duração | Início | Fim | Status |
|------|---------|--------|-----|--------|
| Fase 1 - Correções Críticas | 2 dias | 30/01 | 31/01 | 🔴 Não Iniciado |
| Fase 2 - Melhorias | 3 dias | 01/02 | 03/02 | ⏸️ Aguardando |
| Fase 3 - Novas Features | 5 dias | 05/02 | 09/02 | ⏸️ Aguardando |

---

## ✅ PRÓXIMOS PASSOS IMEDIATOS

1. **[AGORA]** Criar branch `fix/process-all-leads`
2. **[AGORA]** Implementar correção no Orchestrator
3. **[HOJE]** Reorganizar features por modo
4. **[HOJE]** Criar script de teste isolado
5. **[AMANHÃ]** Testar com planilha completa
6. **[AMANHÃ]** Validar todas as features executando

---

## 🚀 RESULTADO ESPERADO

Após implementar as correções da Fase 1, o sistema deve:

1. **Processar 100% dos leads** (não pular baseado em Google ID)
2. **Executar TODAS as features de enriquecimento**
3. **Coletar dados de contato** de múltiplas fontes
4. **Mostrar taxa de sucesso real** (>80%)
5. **Gerar relatório completo** com todos os dados

---

**Última Atualização:** 30/01/2025 00:45  
**Responsável:** Time de Desenvolvimento AURA NEXUS