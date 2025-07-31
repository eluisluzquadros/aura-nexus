# -*- coding: utf-8 -*-
"""
AURA NEXUS - Gerenciador de APIs
Centraliza o gerenciamento de todas as APIs externas
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import googlemaps
import openai
from anthropic import Anthropic
import google.generativeai as genai

# Carrega variáveis de ambiente
load_dotenv()

logger = logging.getLogger("AURA_NEXUS.APIManager")


class RateLimiter:
    """Controla rate limits por API"""
    
    def __init__(self, max_per_minute: int = 60):
        self.max_per_minute = max_per_minute
        self.calls = []
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Espera se necessário para respeitar rate limit"""
        async with self._lock:
            now = datetime.now()
            # Remove chamadas antigas (> 1 minuto)
            self.calls = [call for call in self.calls if now - call < timedelta(minutes=1)]
            
            if len(self.calls) >= self.max_per_minute:
                # Calcula tempo de espera
                oldest_call = min(self.calls)
                wait_time = 60 - (now - oldest_call).total_seconds()
                if wait_time > 0:
                    logger.warning(f"⏳ Rate limit atingido. Aguardando {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    # Limpa lista após esperar
                    self.calls = []
            
            # Registra nova chamada
            self.calls.append(now)


class APIManager:
    """Gerencia todas as APIs externas do sistema"""
    
    def __init__(self):
        self.apis = {}
        self.rate_limiters = {}
        self.session = None
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializa todas as APIs configuradas"""
        if self.is_initialized:
            return
            
        logger.info("🚀 Inicializando APIs...")
        
        # Criar sessão aiohttp
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AURA-NEXUS/1.0'}
        )
        
        # Google Maps
        if os.getenv('GOOGLE_MAPS_API_KEY'):
            self.apis['google_maps'] = googlemaps.Client(
                key=os.getenv('GOOGLE_MAPS_API_KEY')
            )
            self.rate_limiters['google_maps'] = RateLimiter(
                int(os.getenv('GOOGLE_MAPS_RPM', 60))
            )
            logger.info("✅ Google Maps API configurada")
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.apis['openai'] = openai
            self.rate_limiters['openai'] = RateLimiter(
                int(os.getenv('OPENAI_RPM', 50))
            )
            logger.info("✅ OpenAI API configurada")
        
        # Anthropic Claude
        if os.getenv('ANTHROPIC_API_KEY'):
            self.apis['anthropic'] = Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
            self.rate_limiters['anthropic'] = RateLimiter(
                int(os.getenv('ANTHROPIC_RPM', 40))
            )
            logger.info("✅ Anthropic API configurada")
        
        # Google Gemini
        if os.getenv('GOOGLE_AI_API_KEY'):
            genai.configure(api_key=os.getenv('GOOGLE_AI_API_KEY'))
            self.apis['gemini'] = genai
            self.rate_limiters['gemini'] = RateLimiter(50)
            logger.info("✅ Google Gemini API configurada")
            
        # DeepSeek
        if os.getenv('DEEPSEEK_API_KEY'):
            self.apis['deepseek'] = {
                'api_key': os.getenv('DEEPSEEK_API_KEY'),
                'base_url': 'https://api.deepseek.com/v1'
            }
            self.rate_limiters['deepseek'] = RateLimiter(60)
            logger.info("✅ DeepSeek API configurada")
        
        # Google Custom Search
        if os.getenv('GOOGLE_CSE_API_KEY') and os.getenv('GOOGLE_CSE_CX'):
            self.apis['google_cse'] = {
                'api_key': os.getenv('GOOGLE_CSE_API_KEY'),
                'cx': os.getenv('GOOGLE_CSE_CX')
            }
            self.rate_limiters['google_cse'] = RateLimiter(
                int(os.getenv('GOOGLE_CSE_RPM', 100))
            )
            logger.info("✅ Google Custom Search API configurada")
        
        # Apify
        if os.getenv('APIFY_API_TOKEN'):
            try:
                from apify_client import ApifyClient
                
                # Create main Apify client
                apify_client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
                
                self.apis['apify'] = {
                    'client': apify_client,
                    'token': os.getenv('APIFY_API_TOKEN'),
                    'instagram_actor': os.getenv('APIFY_INSTAGRAM_ACTOR_ID', 'apify/instagram-profile-scraper'),
                    'facebook_actor': os.getenv('APIFY_FACEBOOK_ACTOR_ID', 'curious_coder/facebook-profile-scraper'),
                    'linkedin_actor': os.getenv('APIFY_LINKEDIN_ACTOR_ID', 'apify/linkedin-profile-scraper')
                }
                self.rate_limiters['apify'] = RateLimiter(30)
                logger.info("✅ Apify API configurada com cliente")
            except ImportError:
                logger.warning("⚠️ apify-client não encontrado. Instale com: pip install apify-client")
                self.apis['apify'] = {
                    'token': os.getenv('APIFY_API_TOKEN'),
                    'instagram_actor': os.getenv('APIFY_INSTAGRAM_ACTOR_ID', 'apify/instagram-profile-scraper'),
                    'facebook_actor': os.getenv('APIFY_FACEBOOK_ACTOR_ID', 'curious_coder/facebook-profile-scraper'),
                    'client': None
                }
                self.rate_limiters['apify'] = RateLimiter(30)
                logger.info("✅ Apify API configurada (sem cliente)")
        
        self.is_initialized = True
        logger.info(f"✅ {len(self.apis)} APIs inicializadas com sucesso!")
    
    async def close(self):
        """Fecha conexões abertas"""
        if self.session:
            await self.session.close()
    
    def get_api(self, api_name: str) -> Any:
        """Retorna cliente da API solicitada"""
        if api_name not in self.apis:
            raise ValueError(f"API '{api_name}' não configurada")
        return self.apis[api_name]
    
    def get_client(self, client_name: str) -> Any:
        """Retorna cliente específico (para compatibilidade com SocialMediaScraper)"""
        if client_name == 'apify_main' and 'apify' in self.apis:
            return self.apis['apify'].get('client')
        elif client_name == 'apify_linktree' and 'apify' in self.apis:
            return self.apis['apify'].get('client')  # Use same client for now
        return None
    
    async def call_with_rate_limit(self, api_name: str, func, *args, **kwargs):
        """Executa chamada respeitando rate limit"""
        if api_name not in self.rate_limiters:
            # Se não tem rate limiter, executa direto
            return await self._execute_async(func, *args, **kwargs)
        
        # Espera se necessário
        await self.rate_limiters[api_name].wait_if_needed()
        
        # Executa
        return await self._execute_async(func, *args, **kwargs)
    
    async def _execute_async(self, func, *args, **kwargs):
        """Executa função de forma assíncrona"""
        # Se a função já é assíncrona
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        
        # Se é síncrona, executa em thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    
    # === APIs Específicas ===
    
    async def search_place_google_maps(self, query: str, location: str = None) -> Optional[Dict]:
        """Busca lugar no Google Maps"""
        if 'google_maps' not in self.apis:
            logger.warning("⚠️ Google Maps API não configurada")
            return None
        
        try:
            gmaps = self.apis['google_maps']
            
            # Buscar lugar
            result = await self.call_with_rate_limit(
                'google_maps',
                lambda: gmaps.places(
                    query=query,
                    language='pt-BR',
                    region='br'
                )
            )
            
            if result['results']:
                return result['results'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar no Google Maps: {e}")
            return None
    
    async def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Obtém detalhes de um lugar do Google Maps"""
        if 'google_maps' not in self.apis:
            return None
        
        try:
            gmaps = self.apis['google_maps']
            
            result = await self.call_with_rate_limit(
                'google_maps',
                lambda: gmaps.place(
                    place_id=place_id,
                    language='pt-BR',
                    fields=[
                        'name', 'formatted_address', 'formatted_phone_number',
                        'website', 'rating', 'user_ratings_total', 'opening_hours',
                        'photo', 'type', 'geometry', 'business_status'
                    ]
                )
            )
            
            return result.get('result')
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter detalhes do lugar: {e}")
            return None
    
    async def search_google_cse(self, query: str, num: int = 10) -> List[Dict]:
        """Busca usando Google Custom Search"""
        if 'google_cse' not in self.apis:
            logger.warning("⚠️ Google CSE não configurado")
            return []
        
        try:
            cse = self.apis['google_cse']
            url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': cse['api_key'],
                'cx': cse['cx'],
                'q': query,
                'num': num,
                'hl': 'pt-BR',
                'gl': 'br'
            }
            
            # Rate limit
            await self.rate_limiters['google_cse'].wait_if_needed()
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                else:
                    logger.error(f"❌ Google CSE erro: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Erro no Google CSE: {e}")
            return []
    
    async def complete_openai(self, prompt: str, model: str = "gpt-3.5-turbo", **kwargs) -> Optional[str]:
        """Gera texto usando OpenAI"""
        if 'openai' not in self.apis:
            return None
        
        try:
            await self.rate_limiters['openai'].wait_if_needed()
            
            # Criar cliente OpenAI
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)
            
            # Executar chamada
            completion = await self._execute_async(
                lambda: client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Erro OpenAI: {e}")
            return None
    
    async def complete_anthropic(self, prompt: str, model: str = "claude-3-haiku-20240307", **kwargs) -> Optional[str]:
        """Gera texto usando Anthropic Claude"""
        if 'anthropic' not in self.apis:
            return None
        
        try:
            await self.rate_limiters['anthropic'].wait_if_needed()
            
            client = self.apis['anthropic']
            response = await self._execute_async(
                client.messages.create,
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                **kwargs
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"❌ Erro Anthropic: {e}")
            return None
    
    async def complete_gemini(self, prompt: str, model_name: str = "gemini-pro", **kwargs) -> Optional[str]:
        """Gera texto usando Google Gemini"""
        if 'gemini' not in self.apis:
            return None
        
        try:
            await self.rate_limiters['gemini'].wait_if_needed()
            
            model = genai.GenerativeModel(model_name)
            response = await self._execute_async(
                model.generate_content,
                prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Erro Gemini: {e}")
            return None
            
    async def complete_deepseek(self, prompt: str, model: str = "deepseek-chat", **kwargs) -> Optional[str]:
        """Gera texto usando DeepSeek"""
        if 'deepseek' not in self.apis:
            return None
        
        try:
            await self.rate_limiters['deepseek'].wait_if_needed()
            
            deepseek_config = self.apis['deepseek']
            
            # Use OpenAI client with DeepSeek endpoint
            from openai import OpenAI
            client = OpenAI(
                api_key=deepseek_config['api_key'],
                base_url=deepseek_config['base_url']
            )
            
            completion = await self._execute_async(
                lambda: client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Erro DeepSeek: {e}")
            return None
    
    def get_available_apis(self) -> List[str]:
        """Retorna lista de APIs disponíveis"""
        return list(self.apis.keys())
    
    def get_api_status(self) -> Dict[str, Any]:
        """Retorna status das APIs"""
        status = {
            'initialized': self.is_initialized,
            'available_apis': self.get_available_apis(),
            'rate_limits': {}
        }
        
        for api_name, limiter in self.rate_limiters.items():
            status['rate_limits'][api_name] = {
                'max_per_minute': limiter.max_per_minute,
                'current_calls': len(limiter.calls)
            }
        
        return status
    
    async def scrape_with_apify(self, actor_id: str, run_input: Dict[str, Any], timeout: int = 120) -> Optional[List[Dict]]:
        """Executa scraping usando Apify Actor"""
        if 'apify' not in self.apis or not self.apis['apify'].get('client'):
            logger.warning("⚠️ Cliente Apify não disponível")
            return None
        
        try:
            await self.rate_limiters['apify'].wait_if_needed()
            
            client = self.apis['apify']['client']
            
            # Execute actor
            run = await self._execute_async(
                client.actor(actor_id).call,
                run_input=run_input,
                timeout_secs=timeout
            )
            
            # Get results
            items = await self._execute_async(
                lambda: list(client.dataset(run["defaultDatasetId"]).iterate_items())
            )
            
            logger.info(f"✅ Apify scraping completado: {len(items)} itens")
            return items
            
        except Exception as e:
            logger.error(f"❌ Erro no scraping Apify: {e}")
            return None