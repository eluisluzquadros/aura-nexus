# -*- coding: utf-8 -*-
"""
AURA NEXUS v24.4 - CÉLULA 16: SOCIAL MEDIA SCRAPING
Scraping especializado para redes sociais usando Apify
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

logger = logging.getLogger("AURA_NEXUS.SocialScraper")

# ===================================================================================
# CLASSE: SocialMediaScraper
# ===================================================================================

class SocialMediaScraper:
    """Scraper especializado para redes sociais usando Apify"""
    
    # Configurações dos actors Apify
    APIFY_ACTORS = {
        'instagram': {
            'actor_id': 'apify/instagram-profile-scraper',
            'default_client': 'apify_main'
        },
        'facebook': {
            'actor_id': 'curious_coder/facebook-profile-scraper',
            'default_client': 'apify_main'
        },
        'linkedin': {
            'actor_id': 'apify/linkedin-profile-scraper',
            'default_client': 'apify_main'
        },
        'linktree': {
            'actor_id': 'apify/linktree-scraper',
            'default_client': 'apify_linktree'  # Cliente dedicado
        },
        'tiktok': {
            'actor_id': 'apify/tiktok-profile-scraper',
            'default_client': 'apify_main'
        }
    }
    
    def __init__(self, api_manager: Any):
        """
        Inicializa o scraper social
        
        Args:
            api_manager: Instância do APIManager com clientes Apify
        """
        self.api_manager = api_manager
        self.clients = self._setup_clients()
        self.discovered_urls = {}
        
        # Estatísticas
        self.stats = {
            'total_attempts': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'cache_hits': 0,
            'by_platform': {}
        }
        
        logger.info(f"✅ SocialMediaScraper inicializado com {len(self.clients)} clientes")
    
    def _setup_clients(self) -> Dict[str, Any]:
        """Configura clientes Apify disponíveis"""
        clients = {}
        
        # Cliente principal
        if self.api_manager.get_client('apify_main'):
            clients['apify_main'] = self.api_manager.get_client('apify_main')
            logger.info("✅ Cliente Apify principal disponível")
        
        # Cliente Linktree
        if self.api_manager.get_client('apify_linktree'):
            clients['apify_linktree'] = self.api_manager.get_client('apify_linktree')
            logger.info("✅ Cliente Apify Linktree disponível")
        
        return clients
    
    def get_client_for_platform(self, platform: str) -> Optional[Any]:
        """
        Retorna o cliente apropriado para a plataforma
        
        Args:
            platform: Nome da plataforma (instagram, facebook, etc)
            
        Returns:
            Cliente Apify ou None se não disponível
        """
        actor_config = self.APIFY_ACTORS.get(platform, {})
        client_name = actor_config.get('default_client', 'apify_main')
        
        return self.clients.get(client_name)
    
    async def scrape_instagram(self, url: str) -> Dict[str, Any]:
        """
        Scraping de perfil do Instagram
        
        Args:
            url: URL do perfil Instagram
            
        Returns:
            Dict com dados do perfil
        """
        self.stats['total_attempts'] += 1
        
        # Extrair username
        username_match = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", url)
        if not username_match:
            logger.warning(f"URL Instagram inválida: {url}")
            return {'error': 'URL inválida'}
        
        username = username_match.group(1)
        
        # Verificar cliente
        client = self.get_client_for_platform('instagram')
        if not client:
            return {'error': 'Cliente Apify não disponível'}
        
        try:
            logger.info(f"🔍 Scraping Instagram: @{username}")
            
            # Configurar actor
            run_input = {
                "usernames": [username],
                "resultsLimit": 1,
                "proxyConfiguration": {"useApifyProxy": True},
                "searchType": "user",
                "addParentData": True
            }
            
            # Executar actor
            actor_id = self.APIFY_ACTORS['instagram']['actor_id']
            run = await asyncio.to_thread(
                client.actor(actor_id).call,
                run_input=run_input
            )
            
            # Obter resultados
            items = await asyncio.to_thread(
                list,
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )
            
            if items:
                data = items[0]
                
                # Processar dados
                processed_data = {
                    'username': data.get('username', username),
                    'full_name': data.get('fullName', ''),
                    'biography': data.get('biography', ''),
                    'follower_count': data.get('followersCount', 0),
                    'following_count': data.get('followingCount', 0),
                    'posts_count': data.get('postsCount', 0),
                    'is_verified': data.get('isVerified', False),
                    'is_business': data.get('isBusinessAccount', False),
                    'business_category': data.get('businessCategoryName', ''),
                    'external_url': data.get('externalUrl', ''),
                    'profile_pic_url': data.get('profilePicUrl', ''),
                    'email': self._extract_email_from_bio(data.get('biography', '')),
                    'phone': self._extract_phone_from_bio(data.get('biography', '')),
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Descobrir links
                if processed_data['external_url']:
                    self._mark_url_discovered('website', processed_data['external_url'])
                
                self.stats['successful_scrapes'] += 1
                self._update_platform_stats('instagram', 'success')
                
                logger.info(f"✅ Instagram scraped: @{username} ({processed_data['follower_count']} seguidores)")
                
                return processed_data
            
            return {'error': 'Nenhum dado encontrado'}
            
        except Exception as e:
            self.stats['failed_scrapes'] += 1
            self._update_platform_stats('instagram', 'failure')
            logger.error(f"❌ Erro ao scraping Instagram {url}: {str(e)}")
            return {'error': str(e)}
    
    async def scrape_facebook(self, url: str) -> Dict[str, Any]:
        """
        Scraping de página/perfil do Facebook
        
        Args:
            url: URL da página Facebook
            
        Returns:
            Dict com dados da página
        """
        self.stats['total_attempts'] += 1
        
        # Verificar cliente
        client = self.get_client_for_platform('facebook')
        if not client:
            return {'error': 'Cliente Apify não disponível'}
        
        try:
            logger.info(f"🔍 Scraping Facebook: {url}")
            
            # Configurar actor
            run_input = {
                "profileUrls": [url],
                "proxy": {"useApifyProxy": True},
                "minDelay": 2,
                "maxDelay": 10,
                "resultsLimit": 1,
                "deepScrape": True
            }
            
            # Executar actor
            actor_id = self.APIFY_ACTORS['facebook']['actor_id']
            run = await asyncio.to_thread(
                client.actor(actor_id).call,
                run_input=run_input,
                timeout_secs=120
            )
            
            # Obter resultados
            items = await asyncio.to_thread(
                list,
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )
            
            if items:
                data = items[0]
                
                # Processar dados
                processed_data = {
                    'name': data.get('name', ''),
                    'category': data.get('category', ''),
                    'description': data.get('about', ''),
                    'likes': data.get('likes', 0),
                    'followers': data.get('followers', 0),
                    'rating': data.get('rating', 0),
                    'rating_count': data.get('ratingCount', 0),
                    'is_verified': data.get('isVerified', False),
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                    'website': data.get('website', ''),
                    'address': data.get('address', ''),
                    'hours': data.get('hours', ''),
                    'price_range': data.get('priceRange', ''),
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Descobrir links
                if processed_data['website']:
                    self._mark_url_discovered('website', processed_data['website'])
                
                self.stats['successful_scrapes'] += 1
                self._update_platform_stats('facebook', 'success')
                
                logger.info(f"✅ Facebook scraped: {processed_data['name']} ({processed_data['followers']} seguidores)")
                
                return processed_data
            
            return {'error': 'Nenhum dado encontrado'}
            
        except Exception as e:
            self.stats['failed_scrapes'] += 1
            self._update_platform_stats('facebook', 'failure')
            logger.error(f"❌ Erro ao scraping Facebook {url}: {str(e)}")
            return {'error': str(e)}
    
    async def scrape_linktree(self, url: str) -> Dict[str, Any]:
        """
        Scraping de página Linktree
        
        Args:
            url: URL do Linktree
            
        Returns:
            Dict com dados e links
        """
        self.stats['total_attempts'] += 1
        
        # Verificar cliente (preferir cliente dedicado)
        client = self.get_client_for_platform('linktree')
        if not client:
            return {'error': 'Cliente Apify não disponível'}
        
        try:
            logger.info(f"🔍 Scraping Linktree: {url}")
            
            # Configurar actor
            run_input = {
                "urls_or_usernames": [url],
                "proxyConfiguration": {"useApifyProxy": True}
            }
            
            # Executar actor
            actor_id = self.APIFY_ACTORS['linktree']['actor_id']
            run = await asyncio.to_thread(
                client.actor(actor_id).call,
                run_input=run_input
            )
            
            # Obter resultados
            items = await asyncio.to_thread(
                list,
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )
            
            if items:
                data = items[0]
                
                # Processar dados
                processed_data = {
                    'username': data.get('username', ''),
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'profile_picture': data.get('profilePicture', ''),
                    'links': [],
                    'social_links': {},
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Processar links
                for link in data.get('links', []):
                    link_data = {
                        'title': link.get('title', ''),
                        'url': link.get('url', ''),
                        'type': link.get('type', 'link')
                    }
                    processed_data['links'].append(link_data)
                    
                    # Descobrir e categorizar links
                    self._categorize_and_discover_link(link_data['url'])
                
                # Processar links sociais
                for social in data.get('socialLinks', []):
                    platform = self._identify_social_platform(social.get('url', ''))
                    if platform:
                        processed_data['social_links'][platform] = social.get('url', '')
                        self._mark_url_discovered(platform, social.get('url', ''))
                
                self.stats['successful_scrapes'] += 1
                self._update_platform_stats('linktree', 'success')
                
                logger.info(f"✅ Linktree scraped: {processed_data['username']} ({len(processed_data['links'])} links)")
                
                return processed_data
            
            return {'error': 'Nenhum dado encontrado'}
            
        except Exception as e:
            self.stats['failed_scrapes'] += 1
            self._update_platform_stats('linktree', 'failure')
            logger.error(f"❌ Erro ao scraping Linktree {url}: {str(e)}")
            return {'error': str(e)}
    
    async def scrape_linkedin(self, url: str) -> Dict[str, Any]:
        """
        Scraping de página LinkedIn (limitado)
        
        Args:
            url: URL da página LinkedIn
            
        Returns:
            Dict com dados básicos
        """
        self.stats['total_attempts'] += 1
        
        # LinkedIn tem limitações, retornar dados básicos
        logger.warning("⚠️ LinkedIn scraping tem limitações devido a políticas da plataforma")
        
        # Extrair nome da empresa da URL
        company_match = re.search(r"linkedin\.com/company/([^/]+)", url)
        
        if company_match:
            company_slug = company_match.group(1)
            
            self._update_platform_stats('linkedin', 'limited')
            
            return {
                'company_slug': company_slug,
                'url': url,
                'note': 'LinkedIn scraping limitado - considere usar API oficial',
                'scraped_at': datetime.now().isoformat()
            }
        
        return {'error': 'URL LinkedIn inválida'}
    
    async def scrape_tiktok(self, url: str) -> Dict[str, Any]:
        """
        Scraping de perfil TikTok
        
        Args:
            url: URL do perfil TikTok
            
        Returns:
            Dict com dados do perfil
        """
        self.stats['total_attempts'] += 1
        
        # Extrair username
        username_match = re.search(r"tiktok\.com/@([^/?]+)", url)
        if not username_match:
            logger.warning(f"URL TikTok inválida: {url}")
            return {'error': 'URL inválida'}
        
        username = username_match.group(1)
        
        # Verificar cliente
        client = self.get_client_for_platform('tiktok')
        if not client:
            return {'error': 'Cliente Apify não disponível'}
        
        try:
            logger.info(f"🔍 Scraping TikTok: @{username}")
            
            # Configurar actor
            run_input = {
                "profiles": [username],
                "resultsPerPage": 1,
                "proxyConfiguration": {"useApifyProxy": True}
            }
            
            # Executar actor
            actor_id = self.APIFY_ACTORS['tiktok']['actor_id']
            run = await asyncio.to_thread(
                client.actor(actor_id).call,
                run_input=run_input
            )
            
            # Obter resultados
            items = await asyncio.to_thread(
                list,
                client.dataset(run["defaultDatasetId"]).iterate_items()
            )
            
            if items:
                data = items[0]
                
                # Processar dados
                processed_data = {
                    'username': data.get('username', username),
                    'nickname': data.get('nickname', ''),
                    'bio': data.get('signature', ''),
                    'follower_count': data.get('fans', 0),
                    'following_count': data.get('following', 0),
                    'video_count': data.get('video', 0),
                    'heart_count': data.get('heart', 0),
                    'is_verified': data.get('verified', False),
                    'avatar_url': data.get('avatarMedium', ''),
                    'scraped_at': datetime.now().isoformat()
                }
                
                self.stats['successful_scrapes'] += 1
                self._update_platform_stats('tiktok', 'success')
                
                logger.info(f"✅ TikTok scraped: @{username} ({processed_data['follower_count']} seguidores)")
                
                return processed_data
            
            return {'error': 'Nenhum dado encontrado'}
            
        except Exception as e:
            self.stats['failed_scrapes'] += 1
            self._update_platform_stats('tiktok', 'failure')
            logger.error(f"❌ Erro ao scraping TikTok {url}: {str(e)}")
            return {'error': str(e)}
    
    async def scrape_social_url(self, url: str) -> Dict[str, Any]:
        """
        Scraping automático baseado na URL
        
        Args:
            url: URL da rede social
            
        Returns:
            Dict com dados apropriados para a plataforma
        """
        platform = self._identify_social_platform(url)
        
        if not platform:
            logger.warning(f"Plataforma não identificada para URL: {url}")
            return {'error': 'Plataforma não suportada'}
        
        # Mapear para método apropriado
        scrapers = {
            'instagram': self.scrape_instagram,
            'facebook': self.scrape_facebook,
            'linktree': self.scrape_linktree,
            'linkedin': self.scrape_linkedin,
            'tiktok': self.scrape_tiktok
        }
        
        scraper = scrapers.get(platform)
        if scraper:
            return await scraper(url)
        
        return {'error': f'Scraper não implementado para {platform}'}
    
    def _identify_social_platform(self, url: str) -> Optional[str]:
        """Identifica a plataforma social pela URL"""
        patterns = {
            'instagram': r'instagram\.com',
            'facebook': r'facebook\.com|fb\.com',
            'linkedin': r'linkedin\.com',
            'linktree': r'linktr\.ee|linktree\.com',
            'tiktok': r'tiktok\.com',
            'twitter': r'twitter\.com|x\.com',
            'youtube': r'youtube\.com'
        }
        
        for platform, pattern in patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        
        return None
    
    def _extract_email_from_bio(self, bio: str) -> str:
        """Extrai email da bio"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, bio)
        return match.group(0) if match else ''
    
    def _extract_phone_from_bio(self, bio: str) -> str:
        """Extrai telefone da bio"""
        # Padrão brasileiro
        phone_pattern = r'(?:\+?55\s?)?(?:\(?\d{2}\)?[\s-]?)?\d{4,5}[\s-]?\d{4}'
        match = re.search(phone_pattern, bio)
        return match.group(0) if match else ''
    
    def _mark_url_discovered(self, platform: str, url: str):
        """Marca URL como descoberta"""
        if platform not in self.discovered_urls:
            self.discovered_urls[platform] = []
        
        if url and url not in self.discovered_urls[platform]:
            self.discovered_urls[platform].append(url)
            logger.info(f"🔗 URL descoberta [{platform}]: {url}")
    
    def _categorize_and_discover_link(self, url: str):
        """Categoriza e marca link como descoberto"""
        platform = self._identify_social_platform(url)
        
        if platform:
            self._mark_url_discovered(platform, url)
        else:
            # Verificar se é website
            if url and not any(social in url.lower() for social in ['whatsapp', 'wa.me', 'bit.ly']):
                self._mark_url_discovered('website', url)
    
    def _update_platform_stats(self, platform: str, status: str):
        """Atualiza estatísticas por plataforma"""
        if platform not in self.stats['by_platform']:
            self.stats['by_platform'][platform] = {
                'attempts': 0,
                'successes': 0,
                'failures': 0
            }
        
        self.stats['by_platform'][platform]['attempts'] += 1
        
        if status == 'success':
            self.stats['by_platform'][platform]['successes'] += 1
        elif status == 'failure':
            self.stats['by_platform'][platform]['failures'] += 1
    
    def get_discovered_urls(self) -> Dict[str, List[str]]:
        """Retorna todas as URLs descobertas"""
        return self.discovered_urls.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de scraping"""
        stats = self.stats.copy()
        
        # Calcular taxa de sucesso
        if stats['total_attempts'] > 0:
            stats['success_rate'] = stats['successful_scrapes'] / stats['total_attempts']
        else:
            stats['success_rate'] = 0
        
        return stats

# ===================================================================================
# FUNÇÃO: Processar múltiplas URLs sociais
# ===================================================================================

async def process_social_urls(scraper: SocialMediaScraper, urls: List[str]) -> Dict[str, Any]:
    """
    Processa múltiplas URLs sociais em paralelo
    
    Args:
        scraper: Instância do SocialMediaScraper
        urls: Lista de URLs para processar
        
    Returns:
        Dict com resultados agregados
    """
    results = {
        'scraped_data': {},
        'discovered_urls': {},
        'errors': [],
        'summary': {}
    }
    
    # Criar tasks assíncronas
    tasks = []
    for url in urls:
        platform = scraper._identify_social_platform(url)
        if platform:
            task = asyncio.create_task(scraper.scrape_social_url(url))
            tasks.append((url, platform, task))
        else:
            results['errors'].append({
                'url': url,
                'error': 'Plataforma não identificada'
            })
    
    # Executar em paralelo
    for url, platform, task in tasks:
        try:
            data = await task
            
            if 'error' not in data:
                if platform not in results['scraped_data']:
                    results['scraped_data'][platform] = []
                results['scraped_data'][platform].append(data)
            else:
                results['errors'].append({
                    'url': url,
                    'platform': platform,
                    'error': data['error']
                })
                
        except Exception as e:
            results['errors'].append({
                'url': url,
                'platform': platform,
                'error': str(e)
            })
    
    # Agregar URLs descobertas
    results['discovered_urls'] = scraper.get_discovered_urls()
    
    # Criar resumo
    results['summary'] = {
        'total_urls': len(urls),
        'successful': len([d for p in results['scraped_data'].values() for d in p]),
        'failed': len(results['errors']),
        'platforms_scraped': list(results['scraped_data'].keys()),
        'new_urls_discovered': sum(len(urls) for urls in results['discovered_urls'].values())
    }
    
    return results

# ===================================================================================
# EXEMPLO DE USO
# ===================================================================================

async def example_social_scraping():
    """Exemplo de uso do scraper social"""
    
    # Simular API manager
    class MockAPIManager:
        def get_client(self, name):
            return None  # Em produção, retornaria cliente real
    
    # Criar scraper
    api_manager = MockAPIManager()
    scraper = SocialMediaScraper(api_manager)
    
    # URLs de exemplo
    urls = [
        "https://instagram.com/exemplo",
        "https://facebook.com/exemplo",
        "https://linktr.ee/exemplo",
        "https://tiktok.com/@exemplo"
    ]
    
    # Processar URLs
    results = await process_social_urls(scraper, urls)
    
    # Mostrar resultados
    print("\n📊 RESULTADOS DO SCRAPING SOCIAL:")
    print(f"Total processado: {results['summary']['total_urls']}")
    print(f"Sucesso: {results['summary']['successful']}")
    print(f"Falhas: {results['summary']['failed']}")
    print(f"URLs descobertas: {results['summary']['new_urls_discovered']}")
    
    # Estatísticas detalhadas
    stats = scraper.get_statistics()
    print("\n📈 ESTATÍSTICAS:")
    print(json.dumps(stats, indent=2))
    
    return results

if __name__ == "__main__":
    print("🔍 AURA NEXUS - Social Media Scraper")
    print("=" * 50)
    
    # Para executar:
    # asyncio.run(example_social_scraping())