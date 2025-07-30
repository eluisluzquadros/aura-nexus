import json
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

# ===================================================================================
# CÉLULA 2: CONFIGURAÇÃO E CLASSES BASE
# ===================================================================================

# Classes de dados base
@dataclass
class LLMResponse:
    """Resposta de LLM"""
    content: str
    llm_used: str
    tokens_used: Optional[int] = None
    latency: Optional[float] = None
    error: Optional[str] = None
    raw_response: Optional[Dict] = None
    confidence: float = 1.0

@dataclass
class LLMAnalysisResult:
    """Resultado de análise de um LLM"""
    llm_name: str
    analysis: Dict[str, Any]
    raw_response: str
    processing_time: float
    tokens_used: int
    cost: float
    success: bool
    error: Optional[str] = None
    confidence: float = 1.0

@dataclass
class ConsensusResult:
    """Resultado do consenso entre LLMs"""
    final_analysis: Dict[str, Any]
    individual_results: List[LLMAnalysisResult]
    agreement_score: float
    consensus_method: str
    divergences: List[Dict[str, Any]]
    total_cost: float
    total_time: float
    participating_llms: List[str]
    quality_score: float = 1.0
    review_status: str = 'pending'
    review_notes: str = ''
    corrections_applied: List[str] = field(default_factory=list)
    review_issues: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    
    @property
    def final_result(self):
        """Alias para compatibilidade com código que usa final_result"""
        return self.final_analysis

@dataclass
class PerformanceMetric:
    """Métrica de performance"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class CacheEntry:
    """Entrada de cache com metadados"""
    key: str
    value: Any
    level: str
    created_at: datetime
    accessed_at: datetime
    access_count: int = 1
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None
    tags: Set[str] = field(default_factory=set)

@dataclass
class ScrapingResult:
    """Resultado de scraping"""
    url: str
    content: Dict[str, Any]
    scraper_used: str
    success: bool
    error: Optional[str] = None
    validation_score: float = 0.0

# Colunas GDR completas
GDR_COLUMNS = [
    'id_ld', 'gdr_nome', 'gdr_endereco', 'gdr_score_sinergia', 'gdr_motivo_score',
    'gdr_telefone_1', 'gdr_telefone_2', 'gdr_telefone_3', 'gdr_whatsapp',
    'gdr_email_1', 'gdr_email_2', 'gdr_website', 'gdr_rating_google',
    'gdr_total_reviews_google', 'gdr_latitude', 'gdr_longitude',
    'gdr_url_facebook', 'gdr_url_instagram', 'gdr_url_linktree',
    'gdr_fb_followers', 'gdr_insta_followers', 'gdr_analise_reviews',
    'gdr_analise_fachada', 'gdr_resumo_qualitativo', 'gdr_potencial_geomarketing',
    'gdr_abordagem_sugerida', 'gdr_llm_usado', 'gdr_raw_data_json',
    'gdr_data_processamento', 'gdr_tempo_processamento',
    # Métricas de consenso
    'gdr_consensus_method', 'gdr_agreement_score', 'gdr_participating_llms',
    'gdr_consensus_divergences', 'gdr_quality_score', 'gdr_review_status',
    # Métricas de custo e tokens
    'gdr_total_tokens', 'gdr_total_cost'
]