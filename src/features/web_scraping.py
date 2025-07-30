import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

# ===================================================================================
# CÉLULA 6: SCRAPING AVANÇADO
# ===================================================================================

class AdvancedWebScraper:
    """Sistema avançado de web scraping multi-fonte"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_manager = config.get('api_manager')
        self.crawler = config.get('crawler')
        self.content_validator = ContentRelevanceValidator()
        self.contact_extractor = config.get('contact_extractor')
        
        # Estatísticas
        self.stats = {
            'total_attempts': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'validation_failures': 0
        }
    
    async def scrape_website(self, url: str, lead_info: Dict[str, Any]) -> ScrapingResult:
        """Scraping principal de website"""
        self.stats['total_attempts'] += 1
        
        # Validar URL
        url_validation = self.content_validator.validate_url(url, lead_info)
        if not url_validation['is_valid']:
            self.stats['validation_failures'] += 1
            return ScrapingResult(
                url=url,
                content={},
                scraper_used='none',
                success=False,
                error=url_validation['reason']
            )
        
        # Tentar múltiplos scrapers em ordem
        scrapers = [
            ('crawl4ai', self._scrape_with_crawl4ai),
            ('requests', self._scrape_with_requests),
            ('google_cache', self._scrape_google_cache)
        ]
        
        for scraper_name, scraper_func in scrapers:
            try:
                result = await scraper_func(url, lead_info)
                
                if result.success:
                    # Validar conteúdo
                    content_text = result.content.get('text', '')
                    validation = self.content_validator.validate_content(content_text, lead_info)
                    
                    if validation['is_relevant']:
                        result.validation_score = validation['score']
                        self.stats['successful_scrapes'] += 1
                        return result
                    else:
                        logger.info(f"Conteúdo não relevante de {scraper_name}: {validation['reason']}")
                        
            except Exception as e:
                logger.error(f"Erro no scraper {scraper_name}: {e}")
                continue
        
        # Se todos falharam
        self.stats['failed_scrapes'] += 1
        return ScrapingResult(
            url=url,
            content={},
            scraper_used='none',
            success=False,
            error="Todos os scrapers falharam"
        )
    
    async def _scrape_with_crawl4ai(self, url: str, lead_info: Dict[str, Any]) -> ScrapingResult:
        """Scraping com Crawl4AI (mais poderoso)"""
        if not self.crawler:
            raise Exception("Crawler não configurado")
        
        try:
            # Executar crawling
            result = await self.crawler.arun(
                url=url,
                word_count_threshold=100,
                bypass_cache=True,
                screenshot=False,
                verbose=False
            )
            
            if result.success:
                # Extrair contatos
                contacts = await self.contact_extractor.extract_all_contacts(result.markdown)
                
                # Extrair metadados
                metadata = self._extract_metadata(result.html)
                
                return ScrapingResult(
                    url=url,
                    content={
                        'text': result.markdown,
                        'title': result.title,
                        'contacts': contacts,
                        'metadata': metadata,
                        'links': self._extract_social_links(result.html)
                    },
                    scraper_used='crawl4ai',
                    success=True
                )
            else:
                raise Exception("Crawling falhou")
                
        except Exception as e:
            raise Exception(f"Crawl4AI erro: {str(e)}")
    
    async def _scrape_with_requests(self, url: str, lead_info: Dict[str, Any]) -> ScrapingResult:
        """Scraping com requests (mais rápido)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = await asyncio.to_thread(
                requests.get,
                url,
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Remover scripts e styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extrair texto
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Extrair contatos
                contacts = await self.contact_extractor.extract_all_contacts(text)
                
                # Extrair metadados
                metadata = self._extract_metadata_from_soup(soup)
                
                return ScrapingResult(
                    url=url,
                    content={
                        'text': text,
                        'title': soup.title.string if soup.title else '',
                        'contacts': contacts,
                        'metadata': metadata,
                        'links': self._extract_social_links_from_soup(soup)
                    },
                    scraper_used='requests',
                    success=True
                )
            else:
                raise Exception(f"Status code: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Requests erro: {str(e)}")
    
    async def _scrape_google_cache(self, url: str, lead_info: Dict[str, Any]) -> ScrapingResult:
        """Tenta obter conteúdo do cache do Google"""
        try:
            cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
            return await self._generate_fallback_analysis(lead_info)
    
    async def _check_streetview_availability(self, location: Dict[str, float]) -> bool:
        """Verifica se Street View está disponível"""
        try:
            params = {
                'location': f"{location['lat']},{location['lng']}",
                'key': self.api_key
            }
            
            response = await asyncio.to_thread(
                requests.get,
                self.metadata_url,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'OK'
            
            return False
            
        except Exception as e:
            logger.debug(f"Erro ao verificar Street View: {e}")
            return False
    
    async def _download_streetview_image(self, location: Dict[str, float], 
                                       max_retries: int = 3) -> Optional[bytes]:
        """Baixa imagem do Street View com retry"""
        params = {
            'size': '640x480',
            'location': f"{location['lat']},{location['lng']}",
            'key': self.api_key,
            'fov': 90,
            'pitch': 0
        }
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    requests.get,
                    f"{self.base_url}",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200 and len(response.content) > 5000:
                    return response.content
                
                # Tentar ângulos diferentes
                params['heading'] = 90 * (attempt + 1)
                
            except Exception as e:
                logger.debug(f"Tentativa {attempt + 1} falhou: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        return None
    
    async def _analyze_image_with_ai(self, image_data: bytes, 
                                   lead_info: Dict[str, Any]) -> str:
        """Analisa imagem com IA (se disponível)"""
        if not self.multi_llm or not self.multi_llm.active_llm:
            return await self._generate_visual_description(image_data, lead_info)
        
        # Preparar prompt para análise
        prompt = f"""Analise esta imagem de fachada de estabelecimento e forneça uma descrição concisa.

Informações do estabelecimento:
- Nome: {lead_info.get('name', 'Não informado')}
- Tipo: {lead_info.get('business_type', 'Comércio/Serviço')}
- Endereço: {lead_info.get('address', 'Não informado')}

Descreva em 2-3 frases:
1. Estado geral da fachada (conservação, modernidade)
2. Tipo de estabelecimento aparente
3. Impressão geral sobre o negócio

Seja objetivo e profissional."""

        try:
            # Converter imagem para base64 se necessário
            import base64
            image_base64 = base64.b64encode(image_data).decode()
            
            # Chamar LLM com visão (se suportar)
            response = await self.multi_llm.generate_content(
                prompt,
                image_data=image_base64 if self.multi_llm.llm_configs[self.multi_llm.active_llm].get('supports_vision') else None
            )
            
            if response.content:
                return response.content
            else:
                return await self._generate_visual_description(image_data, lead_info)
                
        except Exception as e:
            logger.error(f"Erro na análise com IA: {e}")
            return await self._generate_visual_description(image_data, lead_info)
    
    async def _generate_visual_description(self, image_data: bytes, 
                                         lead_info: Dict[str, Any]) -> str:
        """Gera descrição visual básica (sem IA)"""
        # Análise básica da imagem
        try:
            from PIL import Image
            import io
            
            # Abrir imagem
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size
            
            # Análise de cores dominantes (simplificada)
            img_small = img.resize((50, 50))
            colors = img_small.getcolors(maxcolors=100)
            
            if colors:
                # Verificar brilho médio
                total_brightness = sum(
                    count * (0.299*r + 0.587*g + 0.114*b) 
                    for count, (r, g, b) in colors[:10]
                ) / sum(count for count, _ in colors[:10])
                
                if total_brightness > 180:
                    appearance = "clara e bem iluminada"
                elif total_brightness > 100:
                    appearance = "tonalidade neutra"
                else:
                    appearance = "tonalidade escura"
            else:
                appearance = "aparência padrão"
            
        except:
            appearance = "características visuais padrão"
        
        # Gerar descrição baseada em dados
        business_type = lead_info.get('business_type', 'Estabelecimento comercial')
        rating = lead_info.get('rating', 0)
        
        if rating >= 4.5:
            reputation = "com excelente reputação local"
        elif rating >= 4.0:
            reputation = "bem avaliado pela comunidade"
        else:
            reputation = "em desenvolvimento"
        
        return (
            f"{business_type} localizado em {lead_info.get('address', 'endereço não especificado')}. "
            f"Fachada {appearance}, {reputation}. "
            f"Análise visual via Street View disponível para inspeção detalhada."
        )
    
    async def _generate_fallback_analysis(self, lead_info: Dict[str, Any]) -> str:
        """Gera análise alternativa sem imagem"""
        analysis_parts = []
        
        # Tipo de negócio
        business_type = lead_info.get('business_type', 'Comércio/Serviço')
        analysis_parts.append(f"{business_type}")
        
        # Reputação
        if rating := lead_info.get('rating'):
            if rating >= 4.5:
                analysis_parts.append("estabelecimento com excelente reputação")
            elif rating >= 4.0:
                analysis_parts.append("estabelecimento com boa reputação")
            else:
                analysis_parts.append("estabelecimento em desenvolvimento")
        
        # Volume de clientes
        if reviews := lead_info.get('user_ratings_total'):
            if reviews > 100:
                analysis_parts.append("alto fluxo de clientes")
            elif reviews > 50:
                analysis_parts.append("fluxo moderado de clientes")
            else:
                analysis_parts.append("base de clientes em construção")
        
        # Localização
        if address := lead_info.get('address'):
            parts = address.split(',')
            if len(parts) > 2:
                area = parts[-3].strip()
                analysis_parts.append(f"localizado em {area}")
        
        # Montar análise final
        base_analysis = ". ".join(analysis_parts) if analysis_parts else "Dados insuficientes para análise"
        
        return f"{base_analysis}. [Street View não disponível para análise visual]"