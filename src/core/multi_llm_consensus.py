import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import time
import statistics
import re
import hashlib
from collections import defaultdict
import numpy as np
try:
    import tiktoken
except ImportError:
    tiktoken = None

# Imports de outras células
from aura_nexus_celula_02 import LLMAnalysisResult, ConsensusResult
from aura_nexus_celula_19_data_review import DataReviewAgent

# Configurar logger
logger = logging.getLogger("AURA_NEXUS.MultiLLM")

# ===================================================================================
# CÉLULA 3: SISTEMA MULTI-LLM AVANÇADO
# ===================================================================================

class UniversalTokenCounter:
    """Contador universal de tokens para múltiplos LLMs"""
    
    def __init__(self):
        self.encoders = {}
        self._setup_encoders()
        
    def _setup_encoders(self):
        """Configura encoders para cada LLM"""
        try:
            self.encoders['openai'] = tiktoken.encoding_for_model("gpt-4")
            self.encoders['claude'] = tiktoken.encoding_for_model("gpt-4")  # Aproximação
            self.encoders['deepseek'] = tiktoken.encoding_for_model("gpt-4")  # DeepSeek usa tokenização similar
        except:
            self.encoders['default'] = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str, llm_name: str = 'default') -> Dict[str, int]:
        """Conta tokens para um LLM específico"""
        encoder = self.encoders.get(llm_name, self.encoders.get('default'))
        
        if not encoder:
            # Estimativa simples: ~4 caracteres por token
            estimated = len(text) // 4
            return {'input': estimated, 'output': 0, 'total': estimated}
        
        try:
            tokens = len(encoder.encode(text))
            return {'input': tokens, 'output': 0, 'total': tokens}
        except:
            estimated = len(text) // 4
            return {'input': estimated, 'output': 0, 'total': estimated}
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, llm_name: str) -> float:
        """Calcula custo estimado"""
        pricing = {
            'gemini': {'input': 0.00025, 'output': 0.00125},  # Por 1K tokens
            'claude': {'input': 0.008, 'output': 0.024},
            'chatgpt': {'input': 0.0005, 'output': 0.0015},
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'deepseek': {'input': 0.0001, 'output': 0.0002}  # DeepSeek pricing
        }
        
        rates = pricing.get(llm_name, {'input': 0.001, 'output': 0.002})
        cost = (input_tokens * rates['input'] + output_tokens * rates['output']) / 1000
        
        return round(cost, 6)


class MultiLLMConsensusOrchestrator:
    """Orquestrador avançado com consenso entre múltiplos LLMs"""
    
    def __init__(self, llm_configs: Dict[str, Any], token_counter: UniversalTokenCounter, 
                 enable_review: bool = True):
        self.llm_configs = llm_configs
        self.token_counter = token_counter
        self.enable_review = enable_review
        
        # Configurações
        self.min_llms_for_consensus = 2
        self.max_score_variation = 0.2
        self.timeout_per_llm = 30
        
        # Pesos dos LLMs
        self.llm_weights = {
            'gemini': 1.0,
            'claude': 1.0,
            'chatgpt': 0.9,
            'gpt-4o-mini': 0.8,
            'deepseek': 0.95
        }
        
        # Cache de resultados
        self.results_cache = {}
        
        # Inicializar agente de revisão
        if self.enable_review:
            self.review_agent = DataReviewAgent(
                consensus_orchestrator=self,
                learning_enabled=True
            )
        else:
            self.review_agent = None
        
    async def analyze_with_consensus(self, 
                                   data: Dict[str, Any], 
                                   analysis_type: str,
                                   llms_to_use: Optional[List[str]] = None) -> ConsensusResult:
        """Executa análise com múltiplos LLMs e gera consenso"""
        start_time = time.time()
        
        # Verificar cache
        cache_key = self._generate_cache_key(data, analysis_type)
        if cache_key in self.results_cache:
            cached = self.results_cache[cache_key]
            logger.info(f"Resultado encontrado no cache para {analysis_type}")
            return cached
        
        # Determinar LLMs disponíveis
        available_llms = llms_to_use or self._get_available_llms()
        if len(available_llms) < self.min_llms_for_consensus:
            logger.warning(f"Apenas {len(available_llms)} LLMs disponíveis")
        
        # Gerar prompt
        prompt = self._generate_analysis_prompt(data, analysis_type)
        
        # Executar análises em paralelo
        individual_results = await self._run_parallel_analyses(
            prompt, available_llms, analysis_type
        )
        
        # Filtrar resultados bem-sucedidos
        successful_results = [r for r in individual_results if r.success]
        
        if not successful_results:
            return self._create_fallback_result(individual_results, time.time() - start_time)
        
        # Calcular consenso
        consensus_result = await self._calculate_consensus(
            successful_results, analysis_type
        )
        
        # Finalizar resultado
        consensus_result.total_time = time.time() - start_time
        consensus_result.total_cost = sum(r.cost for r in individual_results)
        consensus_result.participating_llms = [r.llm_name for r in successful_results]
        
        # Aplicar revisão de dados se habilitado
        if self.enable_review and self.review_agent:
            logger.info("📋 Aplicando revisão e validação de dados...")
            
            # Revisar resultado do consenso
            review_result = await self.review_agent.review_consensus_result(
                consensus_result,
                analysis_type,
                data
            )
            
            # Atualizar consenso com resultado revisado
            if review_result['status'] in ['approved', 'auto_corrected', 're_analyzed']:
                consensus_result.final_analysis = review_result['analysis']
                consensus_result.quality_score = review_result.get('quality_score', 1.0)
                consensus_result.review_status = review_result['status']
                consensus_result.review_notes = review_result.get('review_notes', '')
                
                # Adicionar correções aplicadas se houver
                if corrections := review_result.get('corrections_applied'):
                    consensus_result.corrections_applied = corrections
                
                logger.info(f"✅ Revisão concluída: Status={review_result['status']}, "
                          f"Qualidade={review_result.get('quality_score', 0):.2f}")
            else:
                logger.warning(f"⚠️ Revisão requer atenção manual: {review_result['status']}")
                consensus_result.review_status = 'manual_review_required'
                consensus_result.review_issues = review_result.get('issues', [])
        
        # Cachear resultado
        self.results_cache[cache_key] = consensus_result
        
        return consensus_result
    
    def _get_available_llms(self) -> List[str]:
        """Retorna LLMs disponíveis e configurados"""
        # Retorna todos os LLMs configurados como disponíveis
        return list(self.llm_configs.keys())
    
    def _generate_analysis_prompt(self, data: Dict[str, Any], analysis_type: str) -> str:
        """Gera prompt específico para o tipo de análise"""
        prompts = {
            'business_analysis': self._prompt_business_analysis,
            'review_sentiment': self._prompt_review_sentiment,
            'contact_extraction': self._prompt_contact_extraction,
            'scoring': self._prompt_scoring,
            'sales_approach': self._prompt_sales_approach
        }
        
        prompt_generator = prompts.get(analysis_type, self._prompt_generic)
        return prompt_generator(data)
    
    def _prompt_business_analysis(self, data: Dict[str, Any]) -> str:
        """Prompt para análise de negócio"""
        return f"""Analise o seguinte perfil de negócio e retorne APENAS um JSON válido:

DADOS DO NEGÓCIO:
{json.dumps(data, indent=2, ensure_ascii=False)}

RETORNE UM JSON COM EXATAMENTE ESTES CAMPOS:
{{
    "resumo_qualitativo": "Resumo de 2-3 frases sobre o negócio",
    "pontos_fortes": ["lista", "de", "pontos", "fortes"],
    "oportunidades": ["lista", "de", "oportunidades"],
    "score_potencial": 0-100,
    "justificativa_score": "Explicação do score",
    "recomendacoes": ["lista", "de", "recomendações"]
}}

IMPORTANTE: Retorne APENAS o JSON, sem explicações adicionais."""

    def _prompt_scoring(self, data: Dict[str, Any]) -> str:
        """Prompt para scoring padronizado"""
        return f"""Avalie este lead e calcule um score de 0-100 baseado nos critérios abaixo.

DADOS DO LEAD:
{json.dumps(data, indent=2, ensure_ascii=False)}

CRITÉRIOS DE PONTUAÇÃO:
- WhatsApp disponível: +25 pontos
- Telefone disponível: +15 pontos  
- Email disponível: +10 pontos
- Website próprio: +15 pontos
- Alta presença social (>1000 seguidores): +20 pontos
- Reputação excelente (≥4.5 estrelas): +15 pontos

RETORNE APENAS UM JSON:
{{
    "score_final": 0-100,
    "criterios_atendidos": {{
        "whatsapp": true/false,
        "telefone": true/false,
        "email": true/false,
        "website": true/false,
        "presenca_social": true/false,
        "reputacao": true/false
    }},
    "pontos_detalhados": {{
        "whatsapp": 0-25,
        "telefone": 0-15,
        "email": 0-10,
        "website": 0-15,
        "presenca_social": 0-20,
        "reputacao": 0-15
    }},
    "justificativa": "Explicação concisa do score"
}}"""

    def _prompt_review_sentiment(self, data: Dict[str, Any]) -> str:
        """Prompt para análise de sentimento"""
        return f"""Analise as reviews abaixo e determine o sentimento geral.

REVIEWS:
{json.dumps(data.get('reviews', []), indent=2, ensure_ascii=False)}

RETORNE APENAS UM JSON:
{{
    "sentimento_geral": "MUITO_POSITIVO/POSITIVO/NEUTRO/NEGATIVO/MUITO_NEGATIVO",
    "score_sentimento": 0-100,
    "aspectos_positivos": ["lista de aspectos"],
    "aspectos_negativos": ["lista de aspectos"],
    "palavras_chave": ["palavras mais frequentes"],
    "resumo": "Resumo de 1-2 linhas"
}}"""

    def _prompt_sales_approach(self, data: Dict[str, Any]) -> str:
        """Prompt para abordagem de vendas"""
        return f"""Crie uma estratégia de vendas personalizada para este negócio.

DADOS:
Nome: {data.get('name')}
Tipo: {data.get('type', 'Comércio/Serviço')}
Rating: {data.get('rating', 0)}★
Reviews: {data.get('reviews_count', 0)}
Presença Digital: {data.get('digital_presence', 'Básica')}

RETORNE APENAS UM JSON:
{{
    "abordagem_inicial": "Como iniciar o contato",
    "pontos_de_valor": ["benefícios a destacar"],
    "objecoes_comuns": ["possíveis objeções"],
    "proposta_valor": "Proposta principal em 1-2 linhas",
    "gatilhos_mentais": ["gatilhos a explorar"],
    "tom_comunicacao": "formal/informal/consultivo"
}}"""

    def _prompt_contact_extraction(self, data: Dict[str, Any]) -> str:
        """Prompt para extração de contatos"""
        return f"""Extraia TODOS os contatos do texto abaixo.

TEXTO:
{data.get('text', '')}

RETORNE APENAS UM JSON:
{{
    "telefones": ["lista de telefones encontrados"],
    "whatsapp": ["números whatsapp"],
    "emails": ["lista de emails"],
    "websites": ["lista de websites"],
    "redes_sociais": {{
        "instagram": "url ou username",
        "facebook": "url ou username",
        "linkedin": "url ou username"
    }}
}}"""

    def _prompt_generic(self, data: Dict[str, Any]) -> str:
        """Prompt genérico para análises"""
        return f"""Analise os dados fornecidos e retorne um JSON estruturado.

DADOS:
{json.dumps(data, indent=2, ensure_ascii=False)}

Retorne um JSON com sua análise completa."""

    async def _run_parallel_analyses(self, 
                                   prompt: str, 
                                   llms: List[str],
                                   analysis_type: str) -> List[LLMAnalysisResult]:
        """Executa análises em paralelo com timeout"""
        tasks = []
        
        for llm_name in llms:
            if llm_name in self.llm_configs and self.llm_configs[llm_name].get('available'):
                task = self._analyze_with_single_llm(prompt, llm_name, analysis_type)
                tasks.append(task)
        
        # Executar com timeout
        results = []
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_tasks:
            if isinstance(result, Exception):
                logger.error(f"Erro na análise: {str(result)}")
                results.append(
                    LLMAnalysisResult(
                        llm_name="unknown",
                        analysis={},
                        raw_response="",
                        processing_time=0,
                        tokens_used=0,
                        cost=0,
                        success=False,
                        error=str(result)
                    )
                )
            else:
                results.append(result)
        
        return results

    async def _analyze_with_single_llm(self, 
                                      prompt: str, 
                                      llm_name: str,
                                      analysis_type: str) -> LLMAnalysisResult:
        """Analisa com um único LLM"""
        start_time = time.time()
        
        try:
            # Chamar LLM específico
            response = await self._call_llm(llm_name, prompt)
            
            if response.get('success'):
                content = response['content']
                
                # Extrair JSON da resposta
                analysis = self._extract_json_from_response(content)
                
                # Contar tokens
                tokens = self.token_counter.count_tokens(prompt + content, llm_name)
                cost = self.token_counter.calculate_cost(
                    tokens['input'], tokens['output'], llm_name
                )
                
                return LLMAnalysisResult(
                    llm_name=llm_name,
                    analysis=analysis,
                    raw_response=content,
                    processing_time=time.time() - start_time,
                    tokens_used=tokens['total'],
                    cost=cost,
                    success=True,
                    confidence=self._calculate_response_confidence(analysis, analysis_type)
                )
            else:
                raise Exception(response.get('error', 'Unknown error'))
                
        except Exception as e:
            logger.error(f"Erro ao analisar com {llm_name}: {str(e)}")
            return LLMAnalysisResult(
                llm_name=llm_name,
                analysis={},
                raw_response="",
                processing_time=time.time() - start_time,
                tokens_used=0,
                cost=0,
                success=False,
                error=str(e)
            )

    async def _call_llm(self, llm_name: str, prompt: str) -> Dict[str, Any]:
        """Chama LLM específico com implementação real"""
        config = self.llm_configs.get(llm_name, {})
        
        try:
            if config['type'] == 'gemini':
                response = await asyncio.to_thread(
                    config['client'].generate_content,
                    prompt,
                    generation_config={
                        'temperature': 0.1,
                        'top_p': 0.95,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                return {
                    'success': True,
                    'content': response.text.strip()
                }
            
            elif config['type'] == 'claude':
                response = await asyncio.to_thread(
                    config['client'].messages.create,
                    model="claude-3-sonnet-20240229",
                    max_tokens=4096,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                return {
                    'success': True,
                    'content': response.content[0].text.strip()
                }
            
            elif config['type'] == 'openai':
                response = await asyncio.to_thread(
                    config['client'].chat.completions.create,
                    model="gpt-4o-mini",
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return {
                    'success': True,
                    'content': response.choices[0].message.content.strip()
                }
            
            elif config['type'] == 'deepseek':
                response = await asyncio.to_thread(
                    config['client'].chat.completions.create,
                    model="deepseek-chat",
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return {
                    'success': True,
                    'content': response.choices[0].message.content.strip()
                }
            
            else:
                return {
                    'success': False,
                    'error': f'LLM type {config.get("type")} not implemented'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extrai JSON da resposta do LLM com múltiplas estratégias"""
        if not response:
            return {}
        
        # Tentar parse direto
        try:
            return json.loads(response)
        except:
            pass
        
        # Remover marcadores de código
        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        try:
            return json.loads(cleaned.strip())
        except:
            pass
        
        # Buscar JSON no texto
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
        
        # Tentar extração mais agressiva
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(response[start_idx:end_idx+1])
            except:
                pass
        
        logger.warning(f"Não foi possível extrair JSON da resposta: {response[:200]}")
        return {}

    def _calculate_response_confidence(self, analysis: Dict[str, Any], analysis_type: str) -> float:
        """Calcula confiança na resposta do LLM"""
        if not analysis:
            return 0.1
        
        confidence = 1.0
        
        # Campos obrigatórios por tipo
        required_fields = {
            'scoring': ['score_final', 'justificativa'],
            'business_analysis': ['resumo_qualitativo', 'score_potencial'],
            'review_sentiment': ['sentimento_geral', 'score_sentimento'],
            'sales_approach': ['abordagem_inicial', 'proposta_valor']
        }
        
        fields = required_fields.get(analysis_type, [])
        for field in fields:
            if field not in analysis:
                confidence -= 0.2
        
        # Verificar completude
        if len(analysis) < 3:
            confidence -= 0.3
        
        return max(0.1, confidence)

    async def _calculate_consensus(self, 
                                 results: List[LLMAnalysisResult],
                                 analysis_type: str) -> ConsensusResult:
        """Calcula consenso entre resultados com múltiplas estratégias"""
        if len(results) == 1:
            return ConsensusResult(
                final_analysis=results[0].analysis,
                individual_results=results,
                agreement_score=1.0,
                consensus_method='single_llm',
                divergences=[],
                total_cost=results[0].cost,
                total_time=results[0].processing_time,
                participating_llms=[results[0].llm_name],
                quality_score=1.0,
                review_status='pending'
            )
        
        # Calcular score de concordância
        agreement_score = self._calculate_agreement_score(results, analysis_type)
        
        # Identificar divergências
        divergences = self._identify_divergences(results, analysis_type)
        
        # Escolher método de consenso baseado no agreement score
        if agreement_score > 0.8:
            final_analysis = self._consensus_by_average(results)
            consensus_method = 'high_agreement_average'
        elif agreement_score > 0.6:
            final_analysis = self._consensus_by_weighted_voting(results)
            consensus_method = 'weighted_voting'
        else:
            final_analysis = self._consensus_by_highest_confidence(results)
            consensus_method = 'highest_confidence'
        
        return ConsensusResult(
            final_analysis=final_analysis,
            individual_results=results,
            agreement_score=agreement_score,
            consensus_method=consensus_method,
            divergences=divergences,
            total_cost=sum(r.cost for r in results),
            total_time=max(r.processing_time for r in results),
            participating_llms=[r.llm_name for r in results],
            quality_score=1.0,
            review_status='pending'
        )

    def _calculate_agreement_score(self, results: List[LLMAnalysisResult], analysis_type: str) -> float:
        """Calcula score de acordo entre LLMs usando Cohen's Kappa quando aplicável"""
        if len(results) < 2:
            return 1.0
        
        # Tentar usar sklearn se disponível
        try:
            from sklearn.metrics import cohen_kappa_score
            use_kappa = True
        except ImportError:
            use_kappa = False
            logger.debug("sklearn não disponível, usando cálculo simplificado")
        
        if analysis_type == 'scoring':
            scores = [r.analysis.get('score_final', 0) for r in results if r.analysis.get('score_final') is not None]
            if not scores:
                return 0.0
            
            mean_score = np.mean(scores)
            if mean_score == 0:
                return 0.0
            
            max_deviation = max(abs(s - mean_score) for s in scores) / mean_score
            agreement = 1.0 - min(max_deviation, 1.0)
            
        elif analysis_type == 'review_sentiment':
            sentiments = [r.analysis.get('sentimento_geral', 'NEUTRO') for r in results]
            
            unique_sentiments = list(set(sentiments))
            if len(unique_sentiments) == 1:
                agreement = 1.0
            else:
                if use_kappa and len(results) >= 2:
                    # Calcular Cohen's Kappa entre pares de LLMs
                    kappa_scores = []
                    for i in range(len(sentiments)):
                        for j in range(i+1, len(sentiments)):
                            try:
                                # Cohen's Kappa requer pelo menos 2 categorias
                                kappa = cohen_kappa_score([sentiments[i]], [sentiments[j]])
                                kappa_scores.append(kappa)
                            except:
                                pass
                    
                    if kappa_scores:
                        agreement = np.mean(kappa_scores)
                        # Normalizar para 0-1 (kappa pode ser negativo)
                        agreement = (agreement + 1) / 2
                    else:
                        # Fallback para cálculo simples
                        sentiment_values = {
                            'MUITO_NEGATIVO': 0,
                            'NEGATIVO': 1,
                            'NEUTRO': 2,
                            'POSITIVO': 3,
                            'MUITO_POSITIVO': 4
                        }
                        values = [sentiment_values.get(s, 2) for s in sentiments]
                        max_diff = max(values) - min(values)
                        agreement = 1.0 - (max_diff / 4.0)
                else:
                    # Cálculo original
                    sentiment_values = {
                        'MUITO_NEGATIVO': 0,
                        'NEGATIVO': 1,
                        'NEUTRO': 2,
                        'POSITIVO': 3,
                        'MUITO_POSITIVO': 4
                    }
                    values = [sentiment_values.get(s, 2) for s in sentiments]
                    max_diff = max(values) - min(values)
                    agreement = 1.0 - (max_diff / 4.0)
        
        else:
            # Para outros tipos, usar similaridade de campos
            all_keys = set()
            for r in results:
                all_keys.update(r.analysis.keys())
            
            if not all_keys:
                return 0.0
            
            common_keys = all_keys
            for r in results:
                common_keys = common_keys.intersection(r.analysis.keys())
            
            agreement = len(common_keys) / len(all_keys) if all_keys else 0
        
        return max(0.0, min(1.0, agreement))

    def _identify_divergences(self, results: List[LLMAnalysisResult], analysis_type: str) -> List[Dict[str, Any]]:
        """Identifica principais divergências entre LLMs"""
        divergences = []
        
        if analysis_type == 'scoring':
            scores = [(r.llm_name, r.analysis.get('score_final', 0)) for r in results]
            if scores:
                mean_score = np.mean([s[1] for s in scores])
                
                for llm_name, score in scores:
                    deviation = abs(score - mean_score)
                    if deviation > 10:
                        divergences.append({
                            'type': 'score_deviation',
                            'llm': llm_name,
                            'value': score,
                            'mean': mean_score,
                            'deviation': deviation
                        })
        
        elif analysis_type == 'review_sentiment':
            sentiments = [(r.llm_name, r.analysis.get('sentimento_geral', 'NEUTRO')) for r in results]
            sentiment_counts = defaultdict(list)
            
            for llm_name, sentiment in sentiments:
                sentiment_counts[sentiment].append(llm_name)
            
            if len(sentiment_counts) > 1:
                for sentiment, llms in sentiment_counts.items():
                    if len(llms) < len(results) / 2:
                        divergences.append({
                            'type': 'sentiment_minority',
                            'sentiment': sentiment,
                            'llms': llms
                        })
        
        return divergences

    def _consensus_by_average(self, results: List[LLMAnalysisResult]) -> Dict[str, Any]:
        """Consenso por média simples"""
        consensus = {}
        
        # Coletar todos os campos
        all_fields = set()
        for r in results:
            all_fields.update(r.analysis.keys())
        
        for field in all_fields:
            values = [r.analysis.get(field) for r in results if field in r.analysis]
            
            if not values:
                continue
            
            # Números: média
            if all(isinstance(v, (int, float)) for v in values):
                consensus[field] = round(np.mean(values), 2)
            
            # Strings: mais comum
            elif all(isinstance(v, str) for v in values):
                from collections import Counter
                consensus[field] = Counter(values).most_common(1)[0][0]
            
            # Listas: união
            elif all(isinstance(v, list) for v in values):
                combined = []
                for v in values:
                    combined.extend(v)
                # Remover duplicatas mantendo ordem
                seen = set()
                consensus[field] = [x for x in combined if not (x in seen or seen.add(x))]
            
            # Dicionários: merge
            elif all(isinstance(v, dict) for v in values):
                merged = {}
                for v in values:
                    merged.update(v)
                consensus[field] = merged
            
            # Default: primeiro valor
            else:
                consensus[field] = values[0]
        
        return consensus

    def _consensus_by_weighted_voting(self, results: List[LLMAnalysisResult]) -> Dict[str, Any]:
        """Consenso por votação ponderada"""
        consensus = {}
        
        # Calcular valores ponderados
        weighted_values = defaultdict(lambda: defaultdict(float))
        
        for r in results:
            weight = self.llm_weights.get(r.llm_name, 0.5) * r.confidence
            
            for field, value in r.analysis.items():
                if isinstance(value, (int, float)):
                    weighted_values[field]['sum'] += value * weight
                    weighted_values[field]['weight'] += weight
                elif isinstance(value, str):
                    weighted_values[field][value] += weight
                elif isinstance(value, list):
                    for item in value:
                        weighted_values[field][str(item)] += weight
        
        # Consolidar resultados
        for field, values in weighted_values.items():
            if 'sum' in values and 'weight' in values:
                consensus[field] = round(values['sum'] / values['weight'], 2)
            else:
                # Encontrar valor com maior peso
                if values:
                    best_value = max(values.items(), key=lambda x: x[1] if x[0] not in ['sum', 'weight'] else 0)
                    consensus[field] = best_value[0]
        
        return consensus

    def _consensus_by_highest_confidence(self, results: List[LLMAnalysisResult]) -> Dict[str, Any]:
        """Consenso usando resultado de maior confiança"""
        # Ordenar por confiança ponderada
        sorted_results = sorted(
            results,
            key=lambda r: r.confidence * self.llm_weights.get(r.llm_name, 0.5),
            reverse=True
        )
        
        return sorted_results[0].analysis if sorted_results else {}

    def _generate_cache_key(self, data: Dict[str, Any], analysis_type: str) -> str:
        """Gera chave de cache para resultado"""
        # Criar representação estável dos dados
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{analysis_type}_{data_hash}"

    def _create_fallback_result(self, results: List[LLMAnalysisResult], elapsed_time: float) -> ConsensusResult:
        """Cria resultado fallback quando todas as análises falham"""
        return ConsensusResult(
            final_analysis={
                'error': 'Todas as análises falharam',
                'score_final': 0,
                'justificativa': 'Não foi possível analisar devido a erros nos LLMs'
            },
            individual_results=results,
            agreement_score=0.0,
            consensus_method='fallback',
            divergences=[],
            total_cost=sum(r.cost for r in results),
            total_time=elapsed_time,
            participating_llms=[],
            quality_score=0.0,
            review_status='failed'
        )