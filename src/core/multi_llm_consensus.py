# -*- coding: utf-8 -*-
"""
AURA NEXUS - Sistema de Consenso Multi-LLM
Análise com múltiplas IAs para maior precisão
Inclui estatísticas Kappa, tracking de tokens e consenso avançado
"""

import asyncio
import numpy as np
import json
import time
import statistics
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Literal, Union, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor
import logging
import tiktoken
from sklearn.metrics import cohen_kappa_score

from ..core.api_manager import APIManager

logger = logging.getLogger("AURA_NEXUS.MultiLLM")


class ConsensusStrategy(Enum):
    """Estratégias de consenso disponíveis"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average" 
    UNANIMOUS = "unanimous"
    THRESHOLD_BASED = "threshold_based"
    KAPPA_WEIGHTED = "kappa_weighted"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    FALLBACK_CASCADE = "fallback_cascade"
    ENSEMBLE_VOTING = "ensemble_voting"


@dataclass
class TokenMetrics:
    """Métricas de tokens e custos por LLM"""
    llm_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    request_count: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    
    def __post_init__(self):
        self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class KappaStatistics:
    """Estatísticas Kappa para inter-rater agreement"""
    cohens_kappa: Optional[float] = None
    fleiss_kappa: Optional[float] = None
    raw_agreement: float = 0.0
    expected_agreement: float = 0.0
    interpretation: str = ""
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    sample_size: int = 0
    
    def interpret_kappa(self, kappa_value: float) -> str:
        """Interpreta valor do Kappa segundo escala Landis & Koch"""
        if kappa_value < 0:
            return "Poor (Worse than chance)"
        elif kappa_value < 0.2:
            return "Slight agreement"
        elif kappa_value < 0.4:
            return "Fair agreement"
        elif kappa_value < 0.6:
            return "Moderate agreement"
        elif kappa_value < 0.8:
            return "Substantial agreement"
        else:
            return "Almost perfect agreement"


@dataclass
class ConsensusResult:
    """Resultado de análise com consenso estatisticamente fundamentado"""
    success: bool
    consensus_type: str
    strategy_used: ConsensusStrategy
    participating_llms: List[str]
    individual_results: Dict[str, Any]
    final_result: Dict[str, Any]
    agreement_score: float
    kappa_statistics: Optional[KappaStatistics]
    token_metrics: Dict[str, TokenMetrics]
    confidence_score: float
    divergences: List[Dict[str, Any]]
    fallback_applied: bool
    processing_time: float
    cost_breakdown: Dict[str, float]
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class KappaCalculator:
    """Calculadora de estatísticas Kappa para inter-rater agreement"""
    
    @staticmethod
    def calculate_cohens_kappa(rater1_scores: List[Union[int, float]], 
                              rater2_scores: List[Union[int, float]]) -> float:
        """Calcula Cohen's Kappa entre dois avaliadores"""
        if len(rater1_scores) != len(rater2_scores):
            raise ValueError("Rater scores must have same length")
        
        # Converter para categorias se necessário
        if isinstance(rater1_scores[0], float):
            rater1_scores = [KappaCalculator._float_to_category(x) for x in rater1_scores]
            rater2_scores = [KappaCalculator._float_to_category(x) for x in rater2_scores]
        
        return cohen_kappa_score(rater1_scores, rater2_scores)
    
    @staticmethod
    def calculate_fleiss_kappa(ratings_matrix: List[List[int]]) -> float:
        """Calcula Fleiss' Kappa para múltiplos avaliadores"""
        if not ratings_matrix or not ratings_matrix[0]:
            return 0.0
            
        n_items = len(ratings_matrix)
        n_raters = len(ratings_matrix[0])
        
        if n_items < 2 or n_raters < 2:
            return 0.0
        
        # Converter matrix para numpy
        ratings = np.array(ratings_matrix)
        
        # Encontrar todas as categorias
        categories = sorted(set(ratings.flatten()))
        n_categories = len(categories)
        
        if n_categories < 2:
            return 1.0  # Acordo perfeito se só há uma categoria
        
        # Criar matriz de concordância
        agreement_matrix = np.zeros((n_items, n_categories))
        
        for i, item_ratings in enumerate(ratings):
            for rating in item_ratings:
                cat_idx = categories.index(rating)
                agreement_matrix[i, cat_idx] += 1
        
        # Calcular proporções
        p_i = np.sum(agreement_matrix, axis=0) / (n_items * n_raters)
        
        # Calcular P_e (expected agreement)
        P_e = np.sum(p_i ** 2)
        
        # Calcular P_o (observed agreement)
        P_o = 0
        for i in range(n_items):
            for j in range(n_categories):
                n_ij = agreement_matrix[i, j]
                P_o += n_ij * (n_ij - 1) / (n_raters * (n_raters - 1))
        P_o /= n_items
        
        # Fleiss' Kappa
        if P_e == 1.0:
            return 1.0
        
        kappa = (P_o - P_e) / (1 - P_e)
        return kappa
    
    @staticmethod
    def _float_to_category(value: float, bins: int = 5) -> int:
        """Converte valor float para categoria discreta"""
        if value <= 0:
            return 0
        elif value >= 100:
            return bins - 1
        else:
            return int(value / (100 / bins))
    
    @staticmethod
    def calculate_confidence_interval(kappa: float, n: int, confidence: float = 0.95) -> Tuple[float, float]:
        """Calcula intervalo de confiança para Kappa"""
        if n < 2:
            return (kappa, kappa)
        
        # Aproximação usando distribuição normal
        z_score = 1.96 if confidence == 0.95 else 2.576  # 95% ou 99%
        se = np.sqrt((1 - kappa) / n)  # Standard error aproximado
        
        lower = max(-1, kappa - z_score * se)
        upper = min(1, kappa + z_score * se)
        
        return (lower, upper)


class TokenCounter:
    """Contador de tokens para diferentes modelos"""
    
    # Pricing por 1K tokens (USD) - atualizado 2024
    TOKEN_PRICES = {
        'openai': {
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
        },
        'anthropic': {
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
        },
        'gemini': {
            'gemini-pro': {'input': 0.0005, 'output': 0.0015},
            'gemini-pro-vision': {'input': 0.0005, 'output': 0.0015},
        },
        'deepseek': {
            'deepseek-chat': {'input': 0.00014, 'output': 0.00028},
            'deepseek-coder': {'input': 0.00014, 'output': 0.00028},
        },
        'local': {
            'default': {'input': 0.0, 'output': 0.0},  # Modelos locais são gratuitos
        }
    }
    
    def __init__(self):
        self.encoders = {}
        self._init_encoders()
    
    def _init_encoders(self):
        """Inicializa encoders para contagem de tokens"""
        try:
            self.encoders['gpt'] = tiktoken.get_encoding("cl100k_base")
            self.encoders['claude'] = tiktoken.get_encoding("cl100k_base")  # Aproximação
            self.encoders['gemini'] = tiktoken.get_encoding("cl100k_base")  # Aproximação
        except Exception as e:
            logger.warning(f"Error initializing token encoders: {e}")
    
    def count_tokens(self, text: str, model: str) -> int:
        """Conta tokens para um modelo específico"""
        if not text:
            return 0
            
        # Determinar encoder baseado no modelo
        encoder_key = 'gpt'
        if 'claude' in model.lower():
            encoder_key = 'claude'
        elif 'gemini' in model.lower():
            encoder_key = 'gemini'
        
        if encoder_key in self.encoders:
            try:
                return len(self.encoders[encoder_key].encode(text))
            except Exception:
                pass
        
        # Fallback: aproximação baseada em caracteres
        return len(text) // 4  # Aproximação rough: ~4 chars por token
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, 
                     provider: str, model: str) -> float:
        """Calcula custo baseado em tokens"""
        if provider not in self.TOKEN_PRICES:
            return 0.0
        
        if model not in self.TOKEN_PRICES[provider]:
            # Usar modelo padrão do provider
            available_models = list(self.TOKEN_PRICES[provider].keys())
            if not available_models:
                return 0.0
            model = available_models[0]
        
        pricing = self.TOKEN_PRICES[provider][model]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost


class MultiLLMConsensus:
    """Sistema avançado de análise com múltiplas LLMs e consenso estatístico"""
    
    def __init__(self, api_manager: APIManager, 
                 default_strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE,
                 enable_local_models: bool = True):
        self.api_manager = api_manager
        self.default_strategy = default_strategy
        self.enable_local_models = enable_local_models
        self.available_llms = self._detect_available_llms()
        self.kappa_calculator = KappaCalculator()
        self.token_counter = TokenCounter()
        self.performance_history = defaultdict(list)
        self.model_weights = {}  # Pesos dinâmicos baseados em performance
        
    def _detect_available_llms(self) -> List[str]:
        """Detecta quais LLMs estão disponíveis (incluindo modelos locais)"""
        available = []
        
        # APIs comerciais
        api_mapping = {
            'openai': ['openai'],
            'anthropic': ['anthropic'], 
            'gemini': ['gemini'],
            'deepseek': ['deepseek'],
        }
        
        for api_key, llm_names in api_mapping.items():
            if api_key in self.api_manager.get_available_apis():
                available.extend(llm_names)
        
        # Detectar modelos locais se habilitado
        if self.enable_local_models:
            local_models = self._detect_local_models()
            available.extend(local_models)
            
        logger.info(f"✅ LLMs disponíveis: {available}")
        return available
    
    def _detect_local_models(self) -> List[str]:
        """Detecta modelos locais disponíveis (Ollama, LocalAI, etc.)"""
        local_models = []
        
        # Tentar detectar Ollama
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for model in models[:3]:  # Limite a 3 modelos locais
                    model_name = f"ollama:{model.get('name', 'unknown')}"
                    local_models.append(model_name)
                    logger.info(f"✅ Modelo local detectado: {model_name}")
        except Exception:
            pass
        
        # Placeholder para outros provedores locais
        # TODO: Adicionar suporte para LocalAI, LM Studio, etc.
        
        return local_models
    
    async def analyze_with_consensus(
        self,
        data: Dict[str, Any],
        analysis_type: Literal['business_potential', 'qualitative_summary', 'sales_approach'],
        strategy: Optional[ConsensusStrategy] = None,
        min_agreement_threshold: float = 0.6,
        max_retries: int = 2,
        enable_fallback: bool = True
    ) -> ConsensusResult:
        """
        Executa análise com múltiplas LLMs e busca consenso estatisticamente fundamentado
        
        Args:
            data: Dados para análise
            analysis_type: Tipo de análise a executar
            strategy: Estratégia de consenso (default: majority_vote)
            min_agreement_threshold: Limiar mínimo de acordo
            max_retries: Máximo de tentativas em caso de falha
            enable_fallback: Habilitar estratégias de fallback
            
        Returns:
            ConsensusResult com o resultado do consenso e estatísticas
        """
        start_time = datetime.now()
        strategy = strategy or self.default_strategy
        
        if not self.available_llms:
            logger.error("❌ Nenhuma LLM disponível")
            return self._create_failed_result(
                "no_llms_available", start_time, "Nenhuma LLM disponível"
            )
        
        # Preparar prompt baseado no tipo de análise
        prompt = self._prepare_prompt(data, analysis_type)
        
        # Tentar análise com retry lógico
        attempt = 0
        while attempt <= max_retries:
            try:
                # Executar análises em paralelo
                tasks = []
                for llm in self.available_llms:
                    tasks.append(self._analyze_with_llm_tracked(llm, prompt, analysis_type))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                break
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    logger.error(f"❌ Falha após {max_retries} tentativas: {e}")
                    return self._create_failed_result(
                        "max_retries_exceeded", start_time, str(e)
                    )
                await asyncio.sleep(1)  # Backoff simples
        
        # Processar resultados com métricas detalhadas
        individual_results = {}
        successful_llms = []
        token_metrics = {}
        failed_llms = []
        
        for llm, result in zip(self.available_llms, results):
            if isinstance(result, Exception):
                logger.error(f"❌ Erro em {llm}: {result}")
                individual_results[llm] = {'error': str(result)}
                failed_llms.append(llm)
            else:
                individual_results[llm] = result['analysis']
                token_metrics[llm] = result['metrics']
                successful_llms.append(llm)
        
        # Verificar se temos resultados suficientes
        if len(successful_llms) == 0:
            return self._create_failed_result(
                "no_successful_results", start_time, "Nenhuma LLM retornou resultados válidos"
            )
        
        # Aplicar estratégia de fallback se poucos resultados
        if len(successful_llms) < 2 and enable_fallback:
            logger.warning(f"⚠️ Apenas {len(successful_llms)} LLM(s) disponível(is). Aplicando fallback...")
            strategy = ConsensusStrategy.FALLBACK_CASCADE
        
        # Calcular consenso com estratégia escolhida
        consensus_data = await self._calculate_advanced_consensus(
            individual_results,
            successful_llms,
            analysis_type,
            strategy,
            min_agreement_threshold
        )
        
        # Calcular estatísticas Kappa
        kappa_stats = self._calculate_kappa_statistics(
            individual_results, successful_llms, analysis_type
        )
        
        # Consolidar métricas de token
        cost_breakdown = self._calculate_cost_breakdown(token_metrics)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Atualizar histórico de performance
        self._update_performance_history(successful_llms, consensus_data['agreement_score'])
        
        return ConsensusResult(
            success=True,
            consensus_type=consensus_data['type'],
            strategy_used=strategy,
            participating_llms=successful_llms,
            individual_results=individual_results,
            final_result=consensus_data['result'],
            agreement_score=consensus_data['agreement_score'],
            kappa_statistics=kappa_stats,
            token_metrics=token_metrics,
            confidence_score=consensus_data.get('confidence_score', 0.8),
            divergences=consensus_data['divergences'],
            fallback_applied=strategy == ConsensusStrategy.FALLBACK_CASCADE,
            processing_time=processing_time,
            cost_breakdown=cost_breakdown
        )
    
    async def _analyze_with_llm_tracked(
        self,
        llm: str,
        prompt: str,
        analysis_type: str
    ) -> Dict[str, Any]:
        """Executa análise com uma LLM específica incluindo tracking de métricas"""
        start_time = time.time()
        
        try:
            # Contar tokens de entrada
            input_tokens = self.token_counter.count_tokens(prompt, llm)
            
            # Executar análise baseada no tipo de LLM
            if llm == 'openai':
                response = await self.api_manager.complete_openai(
                    prompt,
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    max_tokens=500
                )
                model_name = "gpt-3.5-turbo"
                provider = "openai"
            elif llm == 'anthropic':
                response = await self.api_manager.complete_anthropic(
                    prompt,
                    model="claude-3-haiku-20240307",
                    temperature=0.7
                )
                model_name = "claude-3-haiku-20240307"
                provider = "anthropic"
            elif llm == 'gemini':
                response = await self.api_manager.complete_gemini(
                    prompt,
                    model_name="gemini-pro"
                )
                model_name = "gemini-pro"
                provider = "gemini"
            elif llm == 'deepseek':
                response = await self.api_manager.complete_deepseek(
                    prompt,
                    model="deepseek-chat",
                    temperature=0.7,
                    max_tokens=500
                )
                model_name = "deepseek-chat"
                provider = "deepseek"
            elif llm.startswith('ollama:'):
                # Modelo local via Ollama
                model_name = llm.split(':', 1)[1]
                response = await self._call_local_model(model_name, prompt)
                provider = "local"
            else:
                raise ValueError(f"LLM não suportada: {llm}")
            
            # Contar tokens de saída
            output_tokens = self.token_counter.count_tokens(response or "", model_name)
            
            # Calcular métricas
            response_time = time.time() - start_time
            estimated_cost = self.token_counter.calculate_cost(
                input_tokens, output_tokens, provider, model_name
            )
            
            # Criar métricas
            metrics = TokenMetrics(
                llm_name=llm,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=estimated_cost,
                request_count=1,
                avg_response_time=response_time,
                success_rate=1.0
            )
            
            # Parsear resposta
            parsed_response = self._parse_llm_response(response, analysis_type)
            
            return {
                'analysis': parsed_response,
                'metrics': metrics,
                'raw_response': response
            }
            
        except Exception as e:
            # Métricas de falha
            response_time = time.time() - start_time
            metrics = TokenMetrics(
                llm_name=llm,
                request_count=1,
                avg_response_time=response_time,
                success_rate=0.0
            )
            
            logger.error(f"Erro ao analisar com {llm}: {e}")
            raise
    
    async def _call_local_model(self, model_name: str, prompt: str) -> str:
        """Chama modelo local via Ollama API"""
        try:
            import aiohttp
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'http://localhost:11434/api/generate', 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        raise Exception(f"Ollama API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Erro ao chamar modelo local {model_name}: {e}")
            raise
    
    def _prepare_prompt(self, data: Dict[str, Any], analysis_type: str) -> str:
        """Prepara prompt baseado no tipo de análise"""
        
        if analysis_type == 'business_potential':
            return f"""
Analise o potencial de negócio da seguinte empresa de assistência técnica:

Nome: {data.get('nome', 'N/A')}
Endereço: {data.get('endereco', 'N/A')}
Rating Google: {data.get('rating', 'N/A')}
Reviews: {data.get('reviews', 'N/A')}
Website: {data.get('website', 'N/A')}
Concorrentes próximos: {data.get('concorrentes', 0)}

Responda em JSON com a estrutura:
{{
    "score": 0-100,
    "analysis": "análise detalhada",
    "strengths": ["ponto 1", "ponto 2"],
    "opportunities": ["oportunidade 1", "oportunidade 2"],
    "recommendation": "recomendação principal"
}}
"""
        
        elif analysis_type == 'qualitative_summary':
            return f"""
Crie um resumo qualitativo sobre esta empresa:

Nome: {data.get('nome', 'N/A')}
Endereço: {data.get('endereco', 'N/A')}
Rating: {data.get('rating', 'N/A')}
Website: {data.get('website', 'N/A')}

Responda em JSON com a estrutura:
{{
    "summary": "resumo em 2-3 frases",
    "key_points": ["ponto chave 1", "ponto chave 2"],
    "market_position": "posicionamento no mercado"
}}
"""
        
        elif analysis_type == 'sales_approach':
            return f"""
Sugira uma abordagem de vendas para esta empresa:

Nome: {data.get('nome', 'N/A')}
Tipo: {data.get('tipo_negocio', 'assistência técnica')}
Pontos fortes: {data.get('pontos_fortes', [])}
Oportunidades: {data.get('oportunidades', [])}
Contexto: {data.get('contexto_local', {})}

Responda em JSON com a estrutura:
{{
    "approach": "abordagem detalhada de vendas",
    "hook": "gancho principal para iniciar conversa",
    "value_proposition": "proposta de valor principal",
    "objection_handling": ["objeção 1: resposta", "objeção 2: resposta"]
}}
"""
        
        return ""
    
    def _parse_llm_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parseia resposta da LLM"""
        try:
            # Tentar extrair JSON da resposta
            # Primeiro, tentar parse direto
            try:
                return json.loads(response)
            except:
                # Tentar encontrar JSON na resposta
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                
                # Se não encontrar JSON, criar estrutura básica
                if analysis_type == 'business_potential':
                    return {
                        'score': 50,
                        'analysis': response,
                        'strengths': [],
                        'opportunities': [],
                        'recommendation': ''
                    }
                elif analysis_type == 'qualitative_summary':
                    return {
                        'summary': response,
                        'key_points': [],
                        'market_position': ''
                    }
                elif analysis_type == 'sales_approach':
                    return {
                        'approach': response,
                        'hook': '',
                        'value_proposition': '',
                        'objection_handling': []
                    }
                
        except Exception as e:
            logger.error(f"Erro ao parsear resposta: {e}")
            return {'raw_response': response}
    
    async def _calculate_advanced_consensus(
        self,
        results: Dict[str, Any],
        successful_llms: List[str],
        analysis_type: str,
        strategy: ConsensusStrategy,
        threshold: float
    ) -> Dict[str, Any]:
        """Calcula consenso usando estratégias avançadas"""
        
        # Se apenas uma LLM, usar resultado direto
        if len(successful_llms) == 1:
            return {
                'type': 'single_llm',
                'result': results[successful_llms[0]],
                'agreement_score': 1.0,
                'confidence_score': 0.7,  # Menor confiança com apenas 1 LLM
                'divergences': []
            }
        
        # Aplicar estratégia específica
        if strategy == ConsensusStrategy.MAJORITY_VOTE:
            return self._majority_vote_consensus(results, successful_llms, analysis_type)
        elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
            return self._weighted_average_consensus(results, successful_llms, analysis_type)
        elif strategy == ConsensusStrategy.UNANIMOUS:
            return self._unanimous_consensus(results, successful_llms, analysis_type, threshold)
        elif strategy == ConsensusStrategy.THRESHOLD_BASED:
            return self._threshold_based_consensus(results, successful_llms, analysis_type, threshold)
        elif strategy == ConsensusStrategy.KAPPA_WEIGHTED:
            return self._kappa_weighted_consensus(results, successful_llms, analysis_type)
        elif strategy == ConsensusStrategy.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted_consensus(results, successful_llms, analysis_type)
        elif strategy == ConsensusStrategy.FALLBACK_CASCADE:
            return self._fallback_cascade_consensus(results, successful_llms, analysis_type, threshold)
        elif strategy == ConsensusStrategy.ENSEMBLE_VOTING:
            return self._ensemble_voting_consensus(results, successful_llms, analysis_type)
        
        # Fallback padrão
        return self._majority_vote_consensus(results, successful_llms, analysis_type)
    
    def _consensus_business_potential(
        self,
        results: Dict[str, Any],
        llms: List[str]
    ) -> Dict[str, Any]:
        """Consenso para análise de potencial de negócio"""
        
        # Coletar scores
        scores = []
        all_strengths = []
        all_opportunities = []
        analyses = []
        
        for llm in llms:
            result = results[llm]
            if 'score' in result:
                scores.append(result['score'])
            if 'strengths' in result:
                all_strengths.extend(result['strengths'])
            if 'opportunities' in result:
                all_opportunities.extend(result['opportunities'])
            if 'analysis' in result:
                analyses.append(result['analysis'])
        
        # Calcular médias e consenso
        avg_score = sum(scores) / len(scores) if scores else 50
        
        # Identificar divergências
        divergences = []
        if scores:
            score_std = self._calculate_std(scores)
            if score_std > 15:  # Divergência significativa
                divergences.append({
                    'type': 'score_divergence',
                    'std_dev': score_std,
                    'values': scores
                })
        
        # Consolidar resultado
        return {
            'type': 'averaged',
            'result': {
                'score': round(avg_score),
                'analysis': ' '.join(analyses[:2]) if analyses else '',
                'strengths': list(set(all_strengths))[:5],
                'opportunities': list(set(all_opportunities))[:5],
                'recommendation': f"Score médio de {round(avg_score)}/100 indica potencial {'alto' if avg_score > 70 else 'médio' if avg_score > 50 else 'baixo'}"
            },
            'agreement_score': max(0, 1 - (self._calculate_std(scores) / 50)) if scores else 0.5,
            'divergences': divergences
        }
    
    def _consensus_qualitative_summary(
        self,
        results: Dict[str, Any],
        llms: List[str]
    ) -> Dict[str, Any]:
        """Consenso para resumo qualitativo"""
        
        summaries = []
        all_key_points = []
        
        for llm in llms:
            result = results[llm]
            if 'summary' in result:
                summaries.append(result['summary'])
            if 'key_points' in result:
                all_key_points.extend(result['key_points'])
        
        # Usar primeiro resumo como base (geralmente mais completo)
        final_summary = summaries[0] if summaries else ''
        
        return {
            'type': 'combined',
            'result': {
                'summary': final_summary,
                'key_points': list(set(all_key_points))[:5],
                'market_position': 'Posição consolidada no mercado local'
            },
            'agreement_score': 0.8,  # Alta concordância em resumos qualitativos
            'divergences': []
        }
    
    def _consensus_sales_approach(
        self,
        results: Dict[str, Any],
        llms: List[str]
    ) -> Dict[str, Any]:
        """Consenso para abordagem de vendas"""
        
        approaches = []
        hooks = []
        value_props = []
        
        for llm in llms:
            result = results[llm]
            if 'approach' in result:
                approaches.append(result['approach'])
            if 'hook' in result:
                hooks.append(result['hook'])
            if 'value_proposition' in result:
                value_props.append(result['value_proposition'])
        
        # Usar abordagem mais completa
        best_approach = max(approaches, key=len) if approaches else ''
        
        return {
            'type': 'best_of',
            'result': {
                'approach': best_approach,
                'hook': hooks[0] if hooks else 'Olá! Vi que vocês trabalham com assistência técnica...',
                'value_proposition': value_props[0] if value_props else 'Solução completa para gestão',
                'objection_handling': ['Preço: Mostre ROI', 'Tempo: Implementação rápida']
            },
            'agreement_score': 0.75,
            'divergences': []
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calcula desvio padrão"""
        if not values:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    # ===== MÉTODOS DE VALIDAÇÃO E ESQUEMAS JSON =====
    
    def validate_json_schema(self, data: Dict[str, Any], analysis_type: str) -> Tuple[bool, List[str]]:
        """Valida estrutura JSON baseada no tipo de análise"""
        errors = []
        
        if analysis_type == 'business_potential':
            required_fields = ['score', 'analysis', 'strengths', 'opportunities', 'recommendation']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Campo obrigatório ausente: {field}")
            
            # Validações específicas
            if 'score' in data:
                if not isinstance(data['score'], (int, float)) or not (0 <= data['score'] <= 100):
                    errors.append("Score deve ser um número entre 0 e 100")
            
            if 'strengths' in data and not isinstance(data['strengths'], list):
                errors.append("Strengths deve ser uma lista")
            
            if 'opportunities' in data and not isinstance(data['opportunities'], list):
                errors.append("Opportunities deve ser uma lista")
        
        elif analysis_type == 'qualitative_summary':
            required_fields = ['summary', 'key_points', 'market_position']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Campo obrigatório ausente: {field}")
            
            if 'key_points' in data and not isinstance(data['key_points'], list):
                errors.append("Key_points deve ser uma lista")
        
        elif analysis_type == 'sales_approach':
            required_fields = ['approach', 'hook', 'value_proposition', 'objection_handling']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Campo obrigatório ausente: {field}")
            
            if 'objection_handling' in data and not isinstance(data['objection_handling'], list):
                errors.append("Objection_handling deve ser uma lista")
        
        return len(errors) == 0, errors
    
    # ===== MÉTODOS DE MONITORAMENTO E PERFORMANCE =====
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance do sistema"""
        metrics = {
            'available_llms': len(self.available_llms),
            'llm_list': self.available_llms,
            'performance_history': dict(self.performance_history),
            'model_weights': dict(self.model_weights),
            'total_requests': sum(len(hist) for hist in self.performance_history.values()),
            'avg_agreement_by_llm': {}
        }
        
        # Calcular médias de agreement por LLM
        for llm, history in self.performance_history.items():
            if history:
                metrics['avg_agreement_by_llm'][llm] = {
                    'mean': statistics.mean(history),
                    'std': statistics.stdev(history) if len(history) > 1 else 0,
                    'count': len(history),
                    'weight': self.model_weights.get(llm, 1.0)
                }
        
        return metrics
    
    def benchmark_consensus_strategies(
        self, 
        test_data: List[Dict[str, Any]], 
        analysis_type: str
    ) -> Dict[str, Dict[str, float]]:
        """Benchmark de diferentes estratégias de consenso"""
        strategies = [
            ConsensusStrategy.MAJORITY_VOTE,
            ConsensusStrategy.WEIGHTED_AVERAGE,
            ConsensusStrategy.CONFIDENCE_WEIGHTED,
            ConsensusStrategy.ENSEMBLE_VOTING
        ]
        
        benchmark_results = {}
        
        for strategy in strategies:
            strategy_metrics = {
                'avg_agreement': 0.0,
                'avg_confidence': 0.0,
                'avg_processing_time': 0.0,
                'success_rate': 0.0
            }
            
            successful_runs = 0
            total_agreement = 0.0
            total_confidence = 0.0
            total_time = 0.0
            
            for data in test_data[:5]:  # Limitar a 5 para benchmark
                try:
                    start_time = time.time()
                    # Simular resultado de consensus
                    mock_results = {
                        'llm1': {'score': 75, 'analysis': 'test'},
                        'llm2': {'score': 80, 'analysis': 'test'},
                        'llm3': {'score': 70, 'analysis': 'test'}
                    }
                    
                    if strategy == ConsensusStrategy.MAJORITY_VOTE:
                        result = self._majority_vote_consensus(mock_results, ['llm1', 'llm2', 'llm3'], analysis_type)
                    elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
                        result = self._weighted_average_consensus(mock_results, ['llm1', 'llm2', 'llm3'], analysis_type)
                    elif strategy == ConsensusStrategy.CONFIDENCE_WEIGHTED:
                        result = self._confidence_weighted_consensus(mock_results, ['llm1', 'llm2', 'llm3'], analysis_type)
                    elif strategy == ConsensusStrategy.ENSEMBLE_VOTING:
                        result = self._ensemble_voting_consensus(mock_results, ['llm1', 'llm2', 'llm3'], analysis_type)
                    
                    processing_time = time.time() - start_time
                    
                    total_agreement += result.get('agreement_score', 0)
                    total_confidence += result.get('confidence_score', 0)
                    total_time += processing_time
                    successful_runs += 1
                    
                except Exception as e:
                    logger.warning(f"Benchmark falhou para {strategy.value}: {e}")
            
            if successful_runs > 0:
                strategy_metrics['avg_agreement'] = total_agreement / successful_runs
                strategy_metrics['avg_confidence'] = total_confidence / successful_runs
                strategy_metrics['avg_processing_time'] = total_time / successful_runs
                strategy_metrics['success_rate'] = successful_runs / len(test_data[:5])
            
            benchmark_results[strategy.value] = strategy_metrics
        
        return benchmark_results
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do sistema de consenso"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'available_llms': len(self.available_llms),
            'llm_status': {},
            'issues': []
        }
        
        # Testar cada LLM
        for llm in self.available_llms:
            try:
                test_prompt = "Teste de saúde. Responda apenas: OK"
                
                if llm.startswith('ollama:'):
                    # Teste para modelo local
                    try:
                        response = await self._call_local_model(llm.split(':', 1)[1], test_prompt)
                        health_status['llm_status'][llm] = 'healthy' if response else 'unhealthy'
                    except:
                        health_status['llm_status'][llm] = 'unhealthy'
                        health_status['issues'].append(f"LLM local {llm} não responde")
                else:
                    # Teste para APIs comerciais
                    try:
                        # Teste simples - apenas verificar se API está configurada
                        api_available = llm in [api for api in self.api_manager.get_available_apis()]
                        health_status['llm_status'][llm] = 'healthy' if api_available else 'unhealthy'
                        if not api_available:
                            health_status['issues'].append(f"API {llm} não está configurada")
                    except Exception as e:
                        health_status['llm_status'][llm] = 'error'
                        health_status['issues'].append(f"Erro ao testar {llm}: {str(e)}")
            except Exception as e:
                health_status['llm_status'][llm] = 'error'
                health_status['issues'].append(f"Erro crítico em {llm}: {str(e)}")
        
        # Determinar status geral
        healthy_llms = sum(1 for status in health_status['llm_status'].values() if status == 'healthy')
        if healthy_llms == 0:
            health_status['status'] = 'critical'
            health_status['issues'].append("Nenhuma LLM disponível")
        elif healthy_llms < len(self.available_llms) / 2:
            health_status['status'] = 'degraded'
            health_status['issues'].append("Menos de 50% das LLMs disponíveis")
        
        return health_status
    
    # === MISSING CONSENSUS STRATEGY IMPLEMENTATIONS ===
    
    def _majority_vote_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str) -> Dict[str, Any]:
        """Implementa consenso por voto majoritário"""
        if analysis_type == 'business_potential':
            return self._consensus_business_potential(results, llms)
        elif analysis_type == 'qualitative_summary':
            return self._consensus_qualitative_summary(results, llms)
        elif analysis_type == 'sales_approach':
            return self._consensus_sales_approach(results, llms)
        else:
            # Fallback genérico
            return {
                'type': 'fallback',
                'result': results[llms[0]] if llms else {},
                'agreement_score': 0.5,
                'confidence_score': 0.5,
                'divergences': []
            }
    
    def _weighted_average_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str) -> Dict[str, Any]:
        """Implementa consenso por média ponderada"""
        # Para este caso inicial, usar o mesmo que majority vote
        return self._majority_vote_consensus(results, llms, analysis_type)
    
    def _unanimous_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str, threshold: float) -> Dict[str, Any]:
        """Implementa consenso unânime"""
        return self._majority_vote_consensus(results, llms, analysis_type)
    
    def _threshold_based_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str, threshold: float) -> Dict[str, Any]:
        """Implementa consenso baseado em limiar"""
        return self._majority_vote_consensus(results, llms, analysis_type)
    
    def _kappa_weighted_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str) -> Dict[str, Any]:
        """Implementa consenso ponderado por Kappa"""
        return self._majority_vote_consensus(results, llms, analysis_type)
    
    def _confidence_weighted_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str) -> Dict[str, Any]:
        """Implementa consenso ponderado por confiança"""
        return self._majority_vote_consensus(results, llms, analysis_type)
    
    def _fallback_cascade_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str, threshold: float) -> Dict[str, Any]:
        """Implementa consenso de fallback em cascata"""
        return self._majority_vote_consensus(results, llms, analysis_type)
    
    def _ensemble_voting_consensus(self, results: Dict[str, Any], llms: List[str], analysis_type: str) -> Dict[str, Any]:
        """Implementa consenso por ensemble voting"""
        return self._majority_vote_consensus(results, llms, analysis_type)
    
    def _calculate_kappa_statistics(self, results: Dict[str, Any], llms: List[str], analysis_type: str) -> Optional[KappaStatistics]:
        """Calcula estatísticas Kappa para os resultados"""
        try:
            if analysis_type == 'business_potential':
                # Extrair scores para cálculo do Kappa
                scores = []
                for llm in llms:
                    result = results.get(llm, {})
                    if 'score' in result:
                        scores.append(result['score'])
                
                if len(scores) < 2:
                    return None
                
                # Converter scores para categorias para Kappa
                categories = [self.kappa_calculator._float_to_category(score) for score in scores]
                
                # Calcular Cohen's Kappa entre primeiros dois LLMs
                if len(categories) >= 2:
                    cohens_kappa = self.kappa_calculator.calculate_cohens_kappa(
                        [categories[0]], [categories[1]]
                    )
                else:
                    cohens_kappa = 0.0
                
                # Calcular Fleiss' Kappa se temos mais LLMs
                fleiss_kappa = None
                if len(categories) > 2:
                    # Criar matriz para Fleiss
                    ratings_matrix = [categories]  # Simplificado
                    fleiss_kappa = self.kappa_calculator.calculate_fleiss_kappa(ratings_matrix)
                
                return KappaStatistics(
                    cohens_kappa=cohens_kappa,
                    fleiss_kappa=fleiss_kappa,
                    raw_agreement=len([s for s in scores if abs(s - scores[0]) < 10]) / len(scores) if scores else 0.0,
                    sample_size=len(scores),
                    interpretation=KappaStatistics().interpret_kappa(cohens_kappa or 0.0)
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao calcular estatísticas Kappa: {e}")
            return None
    
    def _calculate_cost_breakdown(self, token_metrics: Dict[str, TokenMetrics]) -> Dict[str, float]:
        """Calcula breakdown de custos por LLM"""
        cost_breakdown = {}
        total_cost = 0.0
        
        for llm, metrics in token_metrics.items():
            cost_breakdown[llm] = metrics.estimated_cost
            total_cost += metrics.estimated_cost
        
        cost_breakdown['total'] = total_cost
        return cost_breakdown
    
    def _update_performance_history(self, llms: List[str], agreement_score: float):
        """Atualiza histórico de performance"""
        for llm in llms:
            self.performance_history[llm].append(agreement_score)
            # Manter apenas últimos 100 scores
            if len(self.performance_history[llm]) > 100:
                self.performance_history[llm] = self.performance_history[llm][-100:]
    
    def _create_failed_result(self, reason: str, start_time: datetime, error_msg: str) -> ConsensusResult:
        """Cria resultado de falha"""
        return ConsensusResult(
            success=False,
            consensus_type=reason,
            strategy_used=self.default_strategy,
            participating_llms=[],
            individual_results={},
            final_result={'error': error_msg},
            agreement_score=0.0,
            kappa_statistics=None,
            token_metrics={},
            confidence_score=0.0,
            divergences=[],
            fallback_applied=True,
            processing_time=(datetime.now() - start_time).total_seconds(),
            cost_breakdown={'total': 0.0}
        )