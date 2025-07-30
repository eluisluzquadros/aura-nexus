# -*- coding: utf-8 -*-
"""
AURA NEXUS v24.4 - CÉLULA 00: CONFIGURAÇÕES E CLASSES BASE
Classes fundamentais e configurações do sistema
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import asyncio
from datetime import datetime


import os
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

# ===================================================================================
# CONFIGURAÇÕES GLOBAIS DO SISTEMA
# ===================================================================================

# Configurações de diretórios
BASE_DIR = Path("/content/drive/MyDrive/AURA_NEXUS")
OUTPUT_DIR = BASE_DIR / "outputs"
CACHE_DIR = BASE_DIR / "cache"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Configurações de LLM
LLM_CONFIG = {
    "gemini": {
        "models": {
            "flash": "gemini-1.5-flash",
            "pro": "gemini-1.5-pro"
        },
        "default_model": "gemini-1.5-flash",
        "max_tokens": 8192,
        "temperature": 0.7,
        "timeout": 60
    },
    "claude": {
        "models": {
            "sonnet": "claude-3-sonnet-20240229",
            "haiku": "claude-3-haiku-20240307"
        },
        "default_model": "claude-3-sonnet-20240229",
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60
    },
    "openai": {
        "models": {
            "gpt4": "gpt-4-turbo-preview",
            "gpt35": "gpt-3.5-turbo"
        },
        "default_model": "gpt-3.5-turbo",
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60
    },
    "deepseek": {
        "models": {
            "chat": "deepseek-chat",
            "coder": "deepseek-coder"
        },
        "default_model": "deepseek-chat",
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60,
        "api_base": "https://api.deepseek.com/v1"
    }
}

# Configurações de processamento
PROCESSING_CONFIG = {
    "batch_size": 10,
    "max_concurrent_requests": 5,
    "retry_attempts": 3,
    "retry_delay": 2,
    "checkpoint_frequency": 5,
    "max_workers": 10
}

# Configurações de cache
CACHE_CONFIG = {
    "l1_size": 1000,
    "l2_ttl_days": 7,
    "l3_ttl_days": 30,
    "cache_compression": True
}

# Configurações de scraping
SCRAPING_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ],
    "rate_limit_delay": 1
}

# ===================================================================================
# CLASSE: APIManager
# ===================================================================================

class APIManager:
    """Gerenciador centralizado de APIs e chaves"""
    
    def __init__(self):
        self.api_keys = {}
        self.clients = {}
        self.rate_limiters = {}
        self._load_api_keys()
        self._initialize_clients()
    
    def _load_api_keys(self):
        """Carrega API keys do Colab ou variáveis de ambiente"""
        try:
            from google.colab import userdata
            
            # Lista de chaves necessárias
            required_keys = [
                'GEMINI_API_KEY',
                'ANTHROPIC_API_KEY', 
                'OPENAI_API_KEY',
                'DEEPSEEK_API_KEY',
                'GOOGLE_MAPS_API_KEY',
                'APIFY_API_KEY',
                'APIFY_API_KEY_LINKTREE',
                'GOOGLE_CSE_ID',
                'GOOGLE_CSE_API_KEY'
            ]
            
            # Tenta carregar do Colab userdata
            for key in required_keys:
                try:
                    self.api_keys[key] = userdata.get(key)
                except:
                    # Fallback para variável de ambiente
                    self.api_keys[key] = os.environ.get(key, '')
                    
        except ImportError:
            # Não está no Colab, usar variáveis de ambiente
            self.api_keys = {
                'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY', ''),
                'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY', ''),
                'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
                'DEEPSEEK_API_KEY': os.environ.get('DEEPSEEK_API_KEY', ''),
                'GOOGLE_MAPS_API_KEY': os.environ.get('GOOGLE_MAPS_API_KEY', ''),
                'APIFY_API_KEY': os.environ.get('APIFY_API_KEY', ''),
                'APIFY_API_KEY_LINKTREE': os.environ.get('APIFY_API_KEY_LINKTREE', ''),
                'GOOGLE_CSE_ID': os.environ.get('GOOGLE_CSE_ID', ''),
                'GOOGLE_CSE_API_KEY': os.environ.get('GOOGLE_CSE_API_KEY', '')
            }
    
    def _initialize_clients(self):
        """Inicializa clientes das APIs"""
        # Google Generative AI
        if self.api_keys.get('GEMINI_API_KEY'):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_keys['GEMINI_API_KEY'])
                self.clients['gemini'] = genai
                logging.info("✅ Gemini API configurada")
            except Exception as e:
                logging.error(f"❌ Erro ao configurar Gemini: {e}")
        
        # Anthropic
        if self.api_keys.get('ANTHROPIC_API_KEY'):
            try:
                import anthropic
                self.clients['anthropic'] = anthropic.Anthropic(
                    api_key=self.api_keys['ANTHROPIC_API_KEY']
                )
                logging.info("✅ Anthropic API configurada")
            except Exception as e:
                logging.error(f"❌ Erro ao configurar Anthropic: {e}")
        
        # OpenAI
        if self.api_keys.get('OPENAI_API_KEY'):
            try:
                import openai
                openai.api_key = self.api_keys['OPENAI_API_KEY']
                self.clients['openai'] = openai
                logging.info("✅ OpenAI API configurada")
            except Exception as e:
                logging.error(f"❌ Erro ao configurar OpenAI: {e}")
        
        # DeepSeek
        if self.api_keys.get('DEEPSEEK_API_KEY'):
            try:
                # DeepSeek usa API compatível com OpenAI
                from openai import OpenAI
                self.clients['deepseek'] = OpenAI(
                    api_key=self.api_keys['DEEPSEEK_API_KEY'],
                    base_url="https://api.deepseek.com/v1"
                )
                logging.info("✅ DeepSeek API configurada")
            except Exception as e:
                logging.error(f"❌ Erro ao configurar DeepSeek: {e}")
        
        # Google Maps
        if self.api_keys.get('GOOGLE_MAPS_API_KEY'):
            try:
                import googlemaps
                self.clients['googlemaps'] = googlemaps.Client(
                    key=self.api_keys['GOOGLE_MAPS_API_KEY']
                )
                logging.info("✅ Google Maps API configurada")
            except Exception as e:
                logging.error(f"❌ Erro ao configurar Google Maps: {e}")
        
        # Apify - Cliente Principal
        if self.api_keys.get('APIFY_API_KEY'):
            try:
                from apify_client import ApifyClient
                self.clients['apify_main'] = ApifyClient(self.api_keys['APIFY_API_KEY'])
                logging.info("✅ Apify API principal configurada")
            except Exception as e:
                logging.error(f"❌ Erro ao configurar Apify principal: {e}")
        
        # Apify - Cliente Linktree
        if self.api_keys.get('APIFY_API_KEY_LINKTREE'):
            try:
                from apify_client import ApifyClient
                self.clients['apify_linktree'] = ApifyClient(self.api_keys['APIFY_API_KEY_LINKTREE'])
                logging.info("✅ Apify API Linktree configurada")
            except Exception as e:
                logging.error(f"❌ Erro ao configurar Apify Linktree: {e}")
    
    def get_api_key(self, key_name: str) -> str:
        """Retorna uma API key específica"""
        return self.api_keys.get(key_name, '')
    
    def get_client(self, client_name: str) -> Any:
        """Retorna um cliente de API específico"""
        return self.clients.get(client_name)
    
    def validate_apis(self) -> Dict[str, bool]:
        """Valida quais APIs estão disponíveis"""
        validation = {}
        
        for key_name, key_value in self.api_keys.items():
            validation[key_name] = bool(key_value)
        
        return validation

# ===================================================================================
# CLASSE: MultiLLMConfig
# ===================================================================================

class MultiLLMConfig:
    """Configuração para múltiplos LLMs"""
    
    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager
        self.llm_configs = {}
        self.active_llms = []
        self._setup_llm_configs()
    
    def _setup_llm_configs(self):
        """Configura os LLMs disponíveis"""
        # Gemini
        if self.api_manager.get_api_key('GEMINI_API_KEY'):
            self.llm_configs['gemini'] = {
                'type': 'gemini',
                'client': self.api_manager.get_client('gemini'),
                'config': LLM_CONFIG['gemini'],
                'weight': 0.4
            }
            self.active_llms.append('gemini')
        
        # Claude
        if self.api_manager.get_api_key('ANTHROPIC_API_KEY'):
            self.llm_configs['claude'] = {
                'type': 'claude',
                'client': self.api_manager.get_client('anthropic'),
                'config': LLM_CONFIG['claude'],
                'weight': 0.3
            }
            self.active_llms.append('claude')
        
        # OpenAI
        if self.api_manager.get_api_key('OPENAI_API_KEY'):
            self.llm_configs['openai'] = {
                'type': 'openai',
                'client': self.api_manager.get_client('openai'),
                'config': LLM_CONFIG['openai'],
                'weight': 0.2
            }
            self.active_llms.append('openai')
        
        # DeepSeek
        if self.api_manager.get_api_key('DEEPSEEK_API_KEY'):
            self.llm_configs['deepseek'] = {
                'type': 'deepseek',
                'client': self.api_manager.get_client('deepseek'),
                'config': LLM_CONFIG['deepseek'],
                'weight': 0.2
            }
            self.active_llms.append('deepseek')
        
        # Normalizar pesos
        if self.active_llms:
            total_weight = sum(self.llm_configs[llm]['weight'] for llm in self.active_llms)
            for llm in self.active_llms:
                self.llm_configs[llm]['weight'] /= total_weight
        
        logging.info(f"✅ LLMs ativos: {self.active_llms}")
    
    def get_llm_config(self, llm_name: str) -> Dict[str, Any]:
        """Retorna configuração de um LLM específico"""
        return self.llm_configs.get(llm_name, {})
    
    def get_active_llms(self) -> List[str]:
        """Retorna lista de LLMs ativos"""
        return self.active_llms
    
    def get_weights(self) -> Dict[str, float]:
        """Retorna pesos dos LLMs"""
        return {llm: self.llm_configs[llm]['weight'] for llm in self.active_llms}

# ===================================================================================
# CLASSE: StandardizedScoringSystem
# ===================================================================================

@dataclass
class ScoringCriteria:
    """Critério de pontuação"""
    name: str
    weight: float
    min_value: float = 0.0
    max_value: float = 100.0

class StandardizedScoringSystem:
    """Sistema de pontuação padronizado para leads"""
    
    def __init__(self):
        self.criteria = self._setup_scoring_criteria()
        self.score_ranges = self._setup_score_ranges()
    
    def _setup_scoring_criteria(self) -> List[ScoringCriteria]:
        """Define critérios de pontuação"""
        return [
            ScoringCriteria("completude_dados", 0.20),
            ScoringCriteria("relevancia_conteudo", 0.25),
            ScoringCriteria("presenca_digital", 0.15),
            ScoringCriteria("engagement_reviews", 0.15),
            ScoringCriteria("informacoes_contato", 0.15),
            ScoringCriteria("potencial_negocio", 0.10)
        ]
    
    def _setup_score_ranges(self) -> Dict[str, tuple]:
        """Define faixas de pontuação"""
        return {
            "excelente": (85, 100),
            "muito_bom": (70, 84),
            "bom": (55, 69),
            "regular": (40, 54),
            "fraco": (0, 39)
        }
    
    def calculate_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula score final do lead"""
        scores = {}
        
        # Completude dos dados
        scores['completude_dados'] = self._score_data_completeness(lead_data)
        
        # Relevância do conteúdo
        scores['relevancia_conteudo'] = lead_data.get('content_relevance_score', 0)
        
        # Presença digital
        scores['presenca_digital'] = self._score_digital_presence(lead_data)
        
        # Engagement de reviews
        scores['engagement_reviews'] = self._score_review_engagement(lead_data)
        
        # Informações de contato
        scores['informacoes_contato'] = self._score_contact_info(lead_data)
        
        # Potencial de negócio
        scores['potencial_negocio'] = self._score_business_potential(lead_data)
        
        # Calcular score final ponderado
        final_score = 0
        for criteria in self.criteria:
            score = scores.get(criteria.name, 0)
            final_score += score * criteria.weight
        
        # Determinar categoria
        category = self._get_score_category(final_score)
        
        return {
            'final_score': round(final_score, 2),
            'category': category,
            'detailed_scores': scores,
            'timestamp': datetime.now().isoformat()
        }
    
    def _score_data_completeness(self, lead_data: Dict) -> float:
        """Pontua completude dos dados"""
        required_fields = [
            'nome_empresa', 'endereco', 'cidade', 'estado',
            'telefone', 'website', 'email', 'horario_funcionamento'
        ]
        
        filled_fields = sum(1 for field in required_fields if lead_data.get(field))
        return (filled_fields / len(required_fields)) * 100
    
    def _score_digital_presence(self, lead_data: Dict) -> float:
        """Pontua presença digital"""
        score = 0
        
        if lead_data.get('website'): score += 25
        if lead_data.get('facebook'): score += 20
        if lead_data.get('instagram'): score += 20
        if lead_data.get('whatsapp'): score += 20
        if lead_data.get('reviews_count', 0) > 10: score += 15
        
        return min(score, 100)
    
    def _score_review_engagement(self, lead_data: Dict) -> float:
        """Pontua engajamento em reviews"""
        reviews_count = lead_data.get('reviews_count', 0)
        rating = lead_data.get('rating', 0)
        
        if reviews_count == 0:
            return 0
        
        # Fórmula: (rating/5 * 50) + (min(reviews_count, 100)/100 * 50)
        rating_score = (rating / 5) * 50
        count_score = (min(reviews_count, 100) / 100) * 50
        
        return rating_score + count_score
    
    def _score_contact_info(self, lead_data: Dict) -> float:
        """Pontua informações de contato"""
        score = 0
        
        if lead_data.get('telefone'): score += 30
        if lead_data.get('whatsapp'): score += 30
        if lead_data.get('email'): score += 20
        if lead_data.get('contato_responsavel'): score += 20
        
        return score
    
    def _score_business_potential(self, lead_data: Dict) -> float:
        """Pontua potencial de negócio"""
        # Baseado em análise de IA
        return lead_data.get('ai_business_potential_score', 50)
    
    def _get_score_category(self, score: float) -> str:
        """Retorna categoria baseada no score"""
        for category, (min_score, max_score) in self.score_ranges.items():
            if min_score <= score <= max_score:
                return category
        return "indefinido"

# ===================================================================================
# FUNÇÕES UTILITÁRIAS
# ===================================================================================

def create_directories():
    """Cria estrutura de diretórios necessária"""
    directories = [OUTPUT_DIR, CACHE_DIR, CHECKPOINT_DIR, LOGS_DIR, DATA_DIR]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Criar subdiretórios
    (OUTPUT_DIR / "enriched").mkdir(exist_ok=True)
    (OUTPUT_DIR / "reports").mkdir(exist_ok=True)
    (CACHE_DIR / "l1_memory").mkdir(exist_ok=True)
    (CACHE_DIR / "l2_file").mkdir(exist_ok=True)
    (CACHE_DIR / "l3_persistent").mkdir(exist_ok=True)
    
    logging.info("✅ Estrutura de diretórios criada")

def setup_logging(log_level=logging.INFO):
    """Configura sistema de logging"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Criar logger
    logger = logging.getLogger("AURA_NEXUS")
    logger.setLevel(log_level)
    
    # Handler para arquivo
    log_file = LOGS_DIR / f"aura_nexus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Adicionar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def validate_environment() -> Dict[str, bool]:
    """Valida o ambiente de execução"""
    validation = {
        "google_colab": False,
        "google_drive": False,
        "gpu_available": False,
        "apis_configured": False
    }
    
    # Verificar Google Colab
    try:
        import google.colab
        validation["google_colab"] = True
    except:
        pass
    
    # Verificar Google Drive
    if validation["google_colab"]:
        try:
            from google.colab import drive
            validation["google_drive"] = os.path.exists("/content/drive")
        except:
            pass
    
    # Verificar GPU
    try:
        import torch
        validation["gpu_available"] = torch.cuda.is_available()
    except:
        pass
    
    # Verificar APIs
    api_manager = APIManager()
    api_validation = api_manager.validate_apis()
    validation["apis_configured"] = any(api_validation.values())
    
    return validation

# ===================================================================================
# CONFIGURAÇÃO INICIAL
# ===================================================================================

def initialize_system():
    """Inicializa o sistema AURA NEXUS"""
    print("🚀 Inicializando AURA NEXUS v24.4...")
    
    # Criar diretórios
    create_directories()
    
    # Configurar logging
    logger = setup_logging()
    
    # Validar ambiente
    env_validation = validate_environment()
    logger.info(f"Validação do ambiente: {env_validation}")
    
    # Inicializar API Manager
    api_manager = APIManager()
    api_validation = api_manager.validate_apis()
    
    # Mostrar status das APIs
    print("\n📊 Status das APIs:")
    for api, is_configured in api_validation.items():
        status = "✅" if is_configured else "❌"
        print(f"{status} {api}")
    
    # Inicializar configurações de LLM
    llm_config = MultiLLMConfig(api_manager)
    
    # Inicializar sistema de scoring
    scoring_system = StandardizedScoringSystem()
    
    print("\n✅ Sistema inicializado com sucesso!")
    
    return {
        'api_manager': api_manager,
        'llm_config': llm_config,
        'scoring_system': scoring_system,
        'logger': logger
    }

# ===================================================================================
# EXEMPLO DE USO
# ===================================================================================

if __name__ == "__main__":
    # Inicializar sistema
    system = initialize_system()
    
    # Exemplo de uso do scoring system
    exemplo_lead = {
        'nome_empresa': 'Empresa Teste',
        'endereco': 'Rua Teste, 123',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'telefone': '11999999999',
        'website': 'www.teste.com',
        'whatsapp': '11999999999',
        'rating': 4.5,
        'reviews_count': 50,
        'content_relevance_score': 85
    }
    
    score_result = system['scoring_system'].calculate_score(exemplo_lead)
    print(f"\n📊 Score do lead exemplo: {score_result['final_score']} ({score_result['category']})")