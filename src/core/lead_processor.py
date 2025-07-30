# -*- coding: utf-8 -*-
"""
AURA NEXUS v24.4 - CÉLULA 10 v2: PROCESSADOR DE LEADS MELHORADO
Suporte para modos de análise: basic vs full_strategy
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger("AURA_NEXUS.LeadProcessor")

# ===================================================================================
# CLASSE: LeadProcessor V2
# ===================================================================================

class LeadProcessor:
    """Processador principal de leads com suporte a diferentes modos"""
    
    # Modos de análise disponíveis
    ANALYSIS_MODES = {
        'basic': {
            'description': 'Coleta básica de dados sem IA',
            'features': ['google_details', 'contact_extraction']
        },
        'full_strategy': {
            'description': 'Análise completa com IA e insights',
            'features': ['google_details', 'contact_extraction', 'reviews_analysis',
                        'web_scraping', 'social_scraping', 'ai_analysis', 
                        'competitor_analysis', 'sales_approach']
        },
        'premium': {
            'description': 'Análise premium com TODAS as funcionalidades ativadas',
            'features': ['google_details', 'contact_extraction', 'reviews_analysis',
                        'web_scraping', 'social_scraping', 'facade_analysis', 'ai_analysis', 
                        'competitor_analysis', 'sales_approach', 'google_cse', 'discovery_cycle',
                        'street_view_analysis', 'drive_cache', 'advanced_metrics']
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o processador
        
        Args:
            config: Configurações incluindo modo de análise
        """
        self.config = config
        
        # Modo de análise
        self.analysis_mode = config.get('ANALYSIS_MODE', 'full_strategy')
        if self.analysis_mode not in self.ANALYSIS_MODES:
            logger.warning(f"Modo '{self.analysis_mode}' não reconhecido. Usando 'full_strategy'")
            self.analysis_mode = 'full_strategy'
        
        # Componentes do sistema
        self.multi_llm = config.get('multi_llm_orchestrator')
        self.api_manager = config.get('api_manager')
        self.cache = config.get('cache')
        self.scoring_system = config.get('scoring_system')
        self.performance_monitor = config.get('performance_monitor')
        self.contact_extractor = config.get('contact_extractor')
        self.content_validator = config.get('content_validator')
        self.web_scraper = config.get('web_scraper')
        self.reviews_analyzer = config.get('reviews_analyzer')
        self.facade_analyzer = config.get('facade_analyzer')
        self.street_view_analyzer = config.get('street_view_analyzer')
        self.social_scraper = config.get('social_scraper')
        
        # Cliente Google Maps
        self.gmaps = self.api_manager.get_client('googlemaps') if self.api_manager else None
        self.gmaps_client = self.gmaps  # Alias para compatibilidade
        
        # Google Custom Search Engine
        self.google_cse_client = None
        if config.get('enable_google_cse', True):
            try:
                from aura_nexus_celula_18_google_cse import GoogleCustomSearchEngine
                cse_api_key = os.getenv('GOOGLE_CSE_API_KEY')
                cse_id = os.getenv('GOOGLE_CSE_ID')
                
                if cse_api_key and cse_id:
                    self.google_cse_client = GoogleCustomSearchEngine(
                        api_key=cse_api_key,
                        search_engine_id=cse_id
                    )
                    logger.info("✅ Google Custom Search Engine ativado")
                else:
                    logger.debug("Google CSE não configurado (faltam API keys)")
            except ImportError:
                logger.debug("Módulo Google CSE não disponível")
        
        # Features ativas baseadas no modo
        self.active_features = set(self.ANALYSIS_MODES[self.analysis_mode]['features'])
        
        # Override manual de features
        if self.analysis_mode == 'full_strategy':
            # Remover facade_analysis do modo full (agora é exclusivo premium)
            self.active_features.discard('facade_analysis')
            self.active_features.discard('web_scraping') if not config.get('enable_scraping', True) else None
        
        elif self.analysis_mode == 'premium':
            # Modo premium força todas as features
            logger.info("🌟 Modo PREMIUM ativado - TODAS as funcionalidades habilitadas")
            self.active_features.add('facade_analysis')
            self.active_features.add('google_cse')
            self.active_features.add('discovery_cycle')
            
            # Ativar cache do Drive se disponível
            if config.get('enable_drive_cache', True) and self.cache:
                try:
                    self.cache.enable_drive_cache = True
                    logger.info("☁️ Cache do Google Drive ativado")
                except:
                    pass
        
        logger.info(f"📋 Modo de análise: {self.analysis_mode}")
        logger.info(f"✨ Features ativas: {self.active_features}")
    
    async def process_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um lead de acordo com o modo configurado
        
        Args:
            lead_data: Dados do lead
            
        Returns:
            Dict com dados enriquecidos (GDR)
        """
        # Timer principal
        if self.performance_monitor:
            main_timer = self.performance_monitor.start_timer('lead_processing')
        
        # Inicializar GDR
        self.gdr = self._initialize_gdr(lead_data)
        self.lead_data = lead_data
        
        try:
            # Validação inicial
            if not self._validate_lead_data():
                raise ValueError("Dados do lead inválidos")
            
            # Executar processamento baseado no modo
            if self.analysis_mode == 'basic':
                await self._process_basic()
            elif self.analysis_mode == 'premium':
                await self._process_premium()
            else:
                await self._process_full_strategy()
            
            # Finalizar processamento
            self._finalize_processing()
            
            # Parar timer
            if self.performance_monitor:
                elapsed = self.performance_monitor.stop_timer(main_timer)
                self.gdr['gdr_tempo_processamento'] = round(elapsed, 2)
            
            logger.info(f"✅ Lead processado: {self.gdr.get('gdr_nome')} [{self.analysis_mode}]")
            
            return self.gdr
            
        except Exception as e:
            if self.performance_monitor:
                self.performance_monitor.stop_timer(main_timer)
            
            logger.error(f"❌ Erro ao processar lead: {str(e)}")
            self.gdr['gdr_erro_processamento'] = str(e)
            self.gdr['gdr_status'] = 'erro'
            
            return self.gdr
    
    async def _process_basic(self):
        """Processamento modo BASIC - apenas coleta de dados"""
        logger.info("🔍 Executando análise BASIC")
        
        # 1. Buscar detalhes do Google
        if 'google_details' in self.active_features:
            await self._get_google_details()
        
        # 2. Extrair contatos
        if 'contact_extraction' in self.active_features:
            await self._extract_contacts_basic()
        
        # 3. Calcular score básico
        self._calculate_basic_score()
    
    async def _process_premium(self):
        """Processamento modo PREMIUM - TODAS as funcionalidades"""
        logger.info("🌟 Executando análise PREMIUM com TODAS as funcionalidades")
        
        # Executar todas as análises do full_strategy primeiro
        await self._process_full_strategy()
        
        # Adicionar funcionalidades premium exclusivas
        
        # 1. Google Custom Search Engine
        if 'google_cse' in self.active_features and self.google_cse_client:
            logger.info("🔍 Executando Google Custom Search...")
            try:
                # Buscar informações adicionais
                search_query = f"{self.gdr.get('gdr_nome')} {self.gdr.get('gdr_cidade', '')}"
                cse_results = await self.google_cse_client.search_business(search_query)
                
                if cse_results:
                    self.gdr['gdr_cse_results'] = len(cse_results)
                    self.gdr['gdr_cse_data'] = json.dumps(cse_results[:3])  # Top 3 resultados
                    
                    # Extrair URLs adicionais encontradas
                    for result in cse_results:
                        if 'instagram.com' in result.get('link', ''):
                            if not self.gdr.get('gdr_url_instagram'):
                                self.gdr['gdr_url_instagram'] = result['link']
                        elif 'facebook.com' in result.get('link', ''):
                            if not self.gdr.get('gdr_url_facebook'):
                                self.gdr['gdr_url_facebook'] = result['link']
                                
                    logger.info(f"✅ Google CSE: {len(cse_results)} resultados encontrados")
                    
            except Exception as e:
                logger.error(f"Erro no Google CSE: {str(e)}")
        
        # 2. Discovery Cycle Inteligente
        if 'discovery_cycle' in self.active_features:
            logger.info("🔄 Executando Discovery Cycle...")
            try:
                from aura_nexus_celula_17_discovery_cycle import enhance_lead_processor_with_discovery_cycle
                enhanced_data = await enhance_lead_processor_with_discovery_cycle(self, self.lead_data)
                
                # Integrar dados descobertos
                if enhanced_data:
                    self.gdr.update(enhanced_data.get('gdr_updates', {}))
                    logger.info("✅ Discovery Cycle completado com sucesso")
                    
            except Exception as e:
                logger.error(f"Erro no Discovery Cycle: {str(e)}")
        
        # 3. Métricas avançadas de consenso
        if 'advanced_metrics' in self.active_features:
            # Adicionar cálculo de métricas avançadas
            self._calculate_advanced_metrics()
        
        logger.info("✨ Análise PREMIUM concluída")
    
    async def _process_full_strategy(self):
        """Processamento modo FULL_STRATEGY - análise completa"""
        logger.info("🚀 Executando análise FULL STRATEGY")
        
        # 1. Buscar detalhes do Google
        if 'google_details' in self.active_features:
            await self._get_google_details()
        
        # 2. Análise de reviews
        if 'reviews_analysis' in self.active_features and self.reviews_analyzer:
            await self._analyze_reviews()
        
        # 3. Extração avançada de contatos
        if 'contact_extraction' in self.active_features:
            await self._extract_contacts_advanced()
        
        # 4. Web scraping
        if 'web_scraping' in self.active_features and self.web_scraper:
            await self._perform_web_scraping()
        
        # 5. Social scraping
        if 'social_scraping' in self.active_features and self.social_scraper:
            await self._perform_social_scraping()
        
        # 6. Análise de fachada
        if 'facade_analysis' in self.active_features:
            await self._analyze_facade()
        
        # 7. Análise com IA
        if 'ai_analysis' in self.active_features and self.multi_llm:
            await self._run_ai_analysis()
        
        # 8. Análise de concorrentes
        if 'competitor_analysis' in self.active_features:
            await self._analyze_competitors()
        
        # 9. Calcular score avançado
        await self._calculate_advanced_score()
        
        # 10. Gerar abordagem de vendas
        if 'sales_approach' in self.active_features and self.multi_llm:
            await self._generate_sales_approach()
    
    def _initialize_gdr(self, lead_data: Dict) -> Dict[str, Any]:
        """Inicializa estrutura GDR (Golden Data Record)"""
        return {
            # Identificação
            'gdr_id': lead_data.get('id', ''),
            'gdr_nome': lead_data.get('nome_empresa', lead_data.get('name', '')),
            'gdr_razao_social': lead_data.get('razao_social', ''),
            
            # Localização
            'gdr_endereco': lead_data.get('endereco', lead_data.get('address', '')),
            'gdr_bairro': lead_data.get('bairro', ''),
            'gdr_cidade': lead_data.get('cidade', lead_data.get('city', '')),
            'gdr_estado': lead_data.get('estado', lead_data.get('state', '')),
            'gdr_cep': lead_data.get('cep', ''),
            'gdr_latitude': lead_data.get('latitude', 0),
            'gdr_longitude': lead_data.get('longitude', 0),
            
            # Contatos
            'gdr_telefone_1': '',
            'gdr_telefone_2': '',
            'gdr_whatsapp': '',
            'gdr_email_1': '',
            'gdr_email_2': '',
            'gdr_website': lead_data.get('website', ''),
            
            # Google
            'gdr_google_place_id': lead_data.get('google_place_id', ''),
            'gdr_google_maps_url': '',
            'gdr_rating_google': 0,
            'gdr_total_reviews_google': 0,
            
            # Redes sociais
            'gdr_url_facebook': '',
            'gdr_url_instagram': '',
            'gdr_url_linkedin': '',
            
            # Análises
            'gdr_analise_reviews': '',
            'gdr_analise_fachada': '',
            'gdr_concorrentes_proximos': '',
            'gdr_geradores_trafego': '',
            
            # Insights
            'gdr_resumo_qualitativo': '',
            'gdr_potencial_geomarketing': '',
            'gdr_abordagem_sugerida': '',
            
            # Scores
            'gdr_score': 0,
            'gdr_score_categoria': '',
            'gdr_motivo_score': '',
            
            # Metadados
            'gdr_modo_analise': self.analysis_mode,
            'gdr_data_processamento': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'gdr_fonte_dados': lead_data.get('fonte_dados', 'spreadsheet'),
            'gdr_status': 'processando'
        }
    
    def _validate_lead_data(self) -> bool:
        """Valida dados mínimos do lead"""
        nome = self.gdr.get('gdr_nome', '').strip()
        
        if not nome:
            logger.error("Lead sem nome")
            return False
        
        # Precisa de endereço ou place_id
        tem_endereco = bool(self.gdr.get('gdr_endereco', '').strip())
        tem_place_id = bool(self.gdr.get('gdr_google_place_id', '').strip())
        
        if not tem_endereco and not tem_place_id:
            logger.error("Lead sem endereço ou place_id")
            return False
        
        return True
    
    async def _get_google_details(self):
        """Busca detalhes no Google Maps/Places"""
        if not self.gmaps:
            logger.warning("Google Maps API não disponível")
            return
        
        try:
            place_id = self.gdr.get('gdr_google_place_id')
            
            # Se não tem place_id, buscar por nome/endereço
            if not place_id:
                nome = self.gdr.get('gdr_nome')
                endereco = self.gdr.get('gdr_endereco')
                cidade = self.gdr.get('gdr_cidade')
                
                query = f"{nome} {endereco} {cidade}".strip()
                
                # Buscar lugar
                places_result = await asyncio.to_thread(
                    self.gmaps.places,
                    query=query,
                    language='pt-BR'
                )
                
                if places_result.get('results'):
                    place = places_result['results'][0]
                    place_id = place.get('place_id')
                    self.gdr['gdr_google_place_id'] = place_id
            
            # Buscar detalhes completos
            if place_id:
                details = await asyncio.to_thread(
                    self.gmaps.place,
                    place_id=place_id,
                    fields=[
                        'name', 'formatted_address', 'formatted_phone_number',
                        'website', 'opening_hours', 'rating', 'user_ratings_total',
                        'geometry', 'url', 'business_status'
                    ],
                    language='pt-BR'
                )
                
                result = details.get('result', {})
                
                # Atualizar GDR
                self.gdr['gdr_nome'] = result.get('name', self.gdr['gdr_nome'])
                self.gdr['gdr_endereco'] = result.get('formatted_address', self.gdr['gdr_endereco'])
                self.gdr['gdr_telefone_1'] = result.get('formatted_phone_number', '')
                self.gdr['gdr_website'] = result.get('website', '')
                self.gdr['gdr_rating_google'] = result.get('rating', 0)
                self.gdr['gdr_total_reviews_google'] = result.get('user_ratings_total', 0)
                self.gdr['gdr_google_maps_url'] = result.get('url', '')
                
                # Coordenadas
                geometry = result.get('geometry', {})
                location = geometry.get('location', {})
                self.gdr['gdr_latitude'] = location.get('lat', 0)
                self.gdr['gdr_longitude'] = location.get('lng', 0)
                
                # Horário
                opening_hours = result.get('opening_hours', {})
                self.gdr['gdr_horario_funcionamento'] = ', '.join(
                    opening_hours.get('weekday_text', [])
                )
                
                # Status
                self.gdr['gdr_status_google'] = result.get('business_status', '')
                
                logger.info(f"✅ Detalhes Google obtidos para {self.gdr['gdr_nome']}")
                
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes Google: {str(e)}")
    
    async def _extract_contacts_basic(self):
        """Extração básica de contatos (modo BASIC)"""
        # Apenas formatar telefone existente
        telefone = self.gdr.get('gdr_telefone_1', '')
        
        if telefone and self.contact_extractor:
            # Verificar se é WhatsApp
            numeros = self.contact_extractor.extract_phone_numbers(telefone)
            if numeros:
                self.gdr['gdr_telefone_1'] = numeros[0]['formatted']
                if numeros[0].get('is_mobile'):
                    self.gdr['gdr_whatsapp'] = numeros[0]['formatted']
    
    async def _extract_contacts_advanced(self):
        """Extração avançada de contatos (modo FULL)"""
        if not self.contact_extractor:
            return
        
        # Extrair de múltiplas fontes
        sources = []
        
        # Website
        website = self.gdr.get('gdr_website', '')
        if website:
            sources.append(website)
        
        # Descrição/sobre
        sobre = self.gdr.get('gdr_sobre', '')
        if sobre:
            sources.append(sobre)
        
        # Processar cada fonte
        todos_contatos = {
            'telefones': [],
            'whatsapp': [],
            'emails': []
        }
        
        for source in sources:
            # Telefones
            numeros = self.contact_extractor.extract_phone_numbers(source)
            todos_contatos['telefones'].extend(numeros)
            
            # WhatsApp (links e números)
            if self.contact_extractor.whatsapp_extractor:
                whatsapp = await self.contact_extractor.whatsapp_extractor.extract_from_text(source)
                todos_contatos['whatsapp'].extend(whatsapp)
            
            # E-mails
            emails = self.contact_extractor.extract_emails(source)
            todos_contatos['emails'].extend(emails)
        
        # Atualizar GDR com contatos únicos
        if todos_contatos['telefones']:
            self.gdr['gdr_telefone_1'] = todos_contatos['telefones'][0]['formatted']
            if len(todos_contatos['telefones']) > 1:
                self.gdr['gdr_telefone_2'] = todos_contatos['telefones'][1]['formatted']
        
        if todos_contatos['whatsapp']:
            self.gdr['gdr_whatsapp'] = todos_contatos['whatsapp'][0]
        
        if todos_contatos['emails']:
            self.gdr['gdr_email_1'] = todos_contatos['emails'][0]
            if len(todos_contatos['emails']) > 1:
                self.gdr['gdr_email_2'] = todos_contatos['emails'][1]
    
    async def _analyze_reviews(self):
        """Analisa reviews do Google"""
        if not self.reviews_analyzer or self.gdr.get('gdr_total_reviews_google', 0) == 0:
            return
        
        try:
            # Buscar reviews
            place_id = self.gdr.get('gdr_google_place_id')
            if place_id and self.gmaps:
                # Buscar detalhes com reviews
                details = await asyncio.to_thread(
                    self.gmaps.place,
                    place_id=place_id,
                    fields=['reviews'],
                    language='pt-BR'
                )
                
                reviews = details.get('result', {}).get('reviews', [])
                
                if reviews:
                    # Analisar com IA
                    analise = await self.reviews_analyzer.analyze_reviews(
                        reviews,
                        self.gdr.get('gdr_nome', '')
                    )
                    
                    self.gdr['gdr_analise_reviews'] = analise.get('resumo', '')
                    self.gdr['gdr_sentimento_reviews'] = analise.get('sentimento', '')
                    self.gdr['gdr_temas_reviews'] = ', '.join(analise.get('temas', []))
                    
        except Exception as e:
            logger.error(f"Erro na análise de reviews: {str(e)}")
    
    async def _perform_web_scraping(self):
        """Executa web scraping do site"""
        website = self.gdr.get('gdr_website', '')
        
        if not website or not self.web_scraper:
            return
        
        try:
            # Scraping
            result = await self.web_scraper.scrape_website(
                website,
                {'nome': self.gdr.get('gdr_nome', '')}
            )
            
            if result.success:
                # Validar conteúdo
                if self.content_validator:
                    validation = self.content_validator.validate_content(
                        result.content,
                        {'nome': self.gdr.get('gdr_nome', '')}
                    )
                    
                    if validation['is_relevant']:
                        self.gdr['gdr_conteudo_site'] = result.content[:1000]
                        self.gdr['gdr_relevancia_site'] = validation['relevance_score']
                
                # Extrair metadados
                self.gdr['gdr_meta_description'] = result.metadata.get('description', '')
                self.gdr['gdr_meta_keywords'] = result.metadata.get('keywords', '')
                
                # Extrair contatos do site
                await self._extract_contacts_from_content(result.content)
                
        except Exception as e:
            logger.error(f"Erro no web scraping: {str(e)}")
    
    async def _perform_social_scraping(self):
        """Executa scraping de redes sociais"""
        if not self.social_scraper:
            return
        
        try:
            # Coletar URLs sociais para scraping
            social_urls = []
            
            # URLs já conhecidas no GDR
            if self.gdr.get('gdr_url_facebook'):
                social_urls.append(self.gdr['gdr_url_facebook'])
            if self.gdr.get('gdr_url_instagram'):
                social_urls.append(self.gdr['gdr_url_instagram'])
            if self.gdr.get('gdr_url_linkedin'):
                social_urls.append(self.gdr['gdr_url_linkedin'])
            
            # Buscar URLs adicionais do website
            if self.gdr.get('gdr_website'):
                # O scraper irá descobrir links sociais automaticamente
                pass
            
            if not social_urls:
                logger.info("Nenhuma URL social encontrada para scraping")
                return
            
            # Processar URLs sociais
            from aura_nexus_celula_16 import process_social_urls
            results = await process_social_urls(self.social_scraper, social_urls)
            
            # Processar resultados por plataforma
            if 'scraped_data' in results:
                # Instagram
                if 'instagram' in results['scraped_data'] and results['scraped_data']['instagram']:
                    ig_data = results['scraped_data']['instagram'][0]
                    self.gdr['gdr_instagram_followers'] = ig_data.get('follower_count', 0)
                    self.gdr['gdr_instagram_bio'] = ig_data.get('biography', '')
                    if ig_data.get('email'):
                        self.gdr['gdr_email_instagram'] = ig_data['email']
                    if ig_data.get('external_url'):
                        self.gdr['gdr_website_instagram'] = ig_data['external_url']
                
                # Facebook
                if 'facebook' in results['scraped_data'] and results['scraped_data']['facebook']:
                    fb_data = results['scraped_data']['facebook'][0]
                    self.gdr['gdr_facebook_followers'] = fb_data.get('followers', 0)
                    self.gdr['gdr_facebook_rating'] = fb_data.get('rating', 0)
                    self.gdr['gdr_facebook_category'] = fb_data.get('category', '')
                    if fb_data.get('phone'):
                        self.gdr['gdr_telefone_facebook'] = fb_data['phone']
                
                # Linktree
                if 'linktree' in results['scraped_data'] and results['scraped_data']['linktree']:
                    lt_data = results['scraped_data']['linktree'][0]
                    self.gdr['gdr_linktree_links'] = len(lt_data.get('links', []))
                    # Armazenar links importantes
                    important_links = []
                    for link in lt_data.get('links', [])[:5]:  # Top 5 links
                        important_links.append(f"{link['title']}: {link['url']}")
                    if important_links:
                        self.gdr['gdr_linktree_principais'] = ' | '.join(important_links)
            
            # Atualizar URLs descobertas
            if 'discovered_urls' in results:
                for platform, urls in results['discovered_urls'].items():
                    if urls and platform == 'website' and not self.gdr.get('gdr_website'):
                        self.gdr['gdr_website'] = urls[0]
            
            logger.info(f"✅ Social scraping concluído: {results['summary']['successful']} sucessos")
            
        except Exception as e:
            logger.error(f"Erro no social scraping: {str(e)}")
    
    async def _analyze_facade(self):
        """Analisa fachada com Street View ou inferência"""
        location = {
            'lat': self.gdr.get('gdr_latitude', 0),
            'lng': self.gdr.get('gdr_longitude', 0)
        }
        
        # Verificar se tem coordenadas válidas
        if location['lat'] == 0 or location['lng'] == 0:
            logger.warning("Sem coordenadas para análise de fachada")
            return
        
        try:
            # Preferir Street View se disponível
            if self.street_view_analyzer:
                analysis = await self.street_view_analyzer.analyze_facade(
                    location=location,
                    lead_name=self.gdr.get('gdr_nome', ''),
                    address=self.gdr.get('gdr_endereco', '')
                )
                
                # Extrair dados da análise
                self.gdr['gdr_analise_fachada'] = self._format_facade_analysis(analysis)
                self.gdr['gdr_score_fachada'] = analysis.get('score_visual', 0)
                self.gdr['gdr_metodo_fachada'] = analysis.get('metodo_analise', 'street_view')
                
            # Fallback para análise inferida
            elif self.facade_analyzer:
                analysis = await self.facade_analyzer.analyze_facade(
                    nome=self.gdr.get('gdr_nome', ''),
                    endereco=self.gdr.get('gdr_endereco', ''),
                    tipo_negocio='assistência técnica'
                )
                
                self.gdr['gdr_analise_fachada'] = analysis.get('analise', '')
                self.gdr['gdr_score_fachada'] = analysis.get('score', 0)
                self.gdr['gdr_metodo_fachada'] = 'inferencia'
                
        except Exception as e:
            logger.error(f"Erro na análise de fachada: {str(e)}")
    
    def _format_facade_analysis(self, analysis: Dict) -> str:
        """Formata análise de fachada para texto"""
        parts = []
        
        # Estilo e tamanho
        parts.append(f"Estilo: {analysis.get('estilo_fachada', 'N/A')}")
        parts.append(f"Tamanho: {analysis.get('tamanho_aparente', 'N/A')}")
        parts.append(f"Visibilidade: {analysis.get('visibilidade_marca', 'N/A')}")
        parts.append(f"Conservação: {analysis.get('estado_conservacao', 'N/A')}")
        
        # Elementos visuais
        elementos = analysis.get('elementos_visuais', {})
        if elementos:
            elem_text = []
            if elementos.get('letreiro_iluminado'):
                elem_text.append('letreiro iluminado')
            if elementos.get('vitrine'):
                elem_text.append('vitrine')
            if elementos.get('pintura_recente'):
                elem_text.append('pintura recente')
            
            if elem_text:
                parts.append(f"Destaques: {', '.join(elem_text)}")
        
        # Observações
        obs = analysis.get('observacoes', '')
        if obs:
            parts.append(f"Obs: {obs}")
        
        return ' | '.join(parts)
    
    async def _analyze_competitors(self):
        """Analisa concorrentes próximos"""
        if not self.gmaps:
            return
        
        location = {
            'lat': self.gdr.get('gdr_latitude', 0),
            'lng': self.gdr.get('gdr_longitude', 0)
        }
        
        if location['lat'] == 0 or location['lng'] == 0:
            return
        
        try:
            # Buscar concorrentes (250m)
            competitors = await asyncio.to_thread(
                self.gmaps.places_nearby,
                location=location,
                keyword='assistência celular OR conserto celular',
                radius=250,
                language='pt-BR'
            )
            
            # Buscar geradores de tráfego (300m)  
            traffic = await asyncio.to_thread(
                self.gmaps.places_nearby,
                location=location,
                keyword='banco OR supermercado OR farmácia',
                radius=300,
                language='pt-BR'
            )
            
            # Processar concorrentes
            comp_list = []
            for place in competitors.get('results', [])[:5]:
                if place.get('place_id') != self.gdr.get('gdr_google_place_id'):
                    comp_list.append({
                        'nome': place.get('name'),
                        'rating': place.get('rating', 0),
                        'distancia': self._calculate_distance(location, place.get('geometry', {}).get('location', {}))
                    })
            
            # Processar geradores
            traffic_list = []
            for place in traffic.get('results', [])[:5]:
                traffic_list.append({
                    'nome': place.get('name'),
                    'tipo': ''
                })
            
            # Atualizar GDR
            self.gdr['gdr_total_concorrentes'] = len(comp_list)
            self.gdr['gdr_concorrentes_proximos'] = ', '.join([c['nome'] for c in comp_list])
            self.gdr['gdr_geradores_trafego'] = ', '.join([t['nome'] for t in traffic_list])
            
        except Exception as e:
            logger.error(f"Erro na análise de concorrentes: {str(e)}")
    
    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> int:
        """Calcula distância aproximada em metros"""
        from math import radians, cos, sin, asin, sqrt
        
        # Fórmula haversine simplificada
        lat1, lon1 = radians(loc1.get('lat', 0)), radians(loc1.get('lng', 0))
        lat2, lon2 = radians(loc2.get('lat', 0)), radians(loc2.get('lng', 0))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Raio da Terra em metros
        r = 6371000
        
        return int(c * r)
    
    async def _run_ai_analysis(self):
        """Executa análises com IA"""
        if not self.multi_llm:
            return
        
        try:
            # Preparar dados para análise
            analysis_data = {
                'nome': self.gdr.get('gdr_nome'),
                'endereco': self.gdr.get('gdr_endereco'),
                'rating': self.gdr.get('gdr_rating_google'),
                'reviews': self.gdr.get('gdr_analise_reviews'),
                'website': self.gdr.get('gdr_website'),
                'concorrentes': self.gdr.get('gdr_total_concorrentes', 0)
            }
            
            # Análise de potencial
            potential_result = await self.multi_llm.analyze_with_consensus(
                data=analysis_data,
                analysis_type='business_potential'
            )
            
            if potential_result.success:
                self.gdr['gdr_potencial_geomarketing'] = potential_result.final_result.get('analysis', '')
                self.gdr['gdr_score_potencial'] = potential_result.final_result.get('score', 0)
                
                # Adicionar métricas de consenso
                self.gdr['gdr_consensus_method'] = potential_result.consensus_method
                self.gdr['gdr_agreement_score'] = potential_result.agreement_score
                self.gdr['gdr_participating_llms'] = ', '.join(potential_result.participating_llms)
                self.gdr['gdr_consensus_divergences'] = len(potential_result.divergences)
                self.gdr['gdr_quality_score'] = potential_result.quality_score
                self.gdr['gdr_review_status'] = potential_result.review_status
            
            # Resumo qualitativo
            summary_result = await self.multi_llm.analyze_with_consensus(
                data=analysis_data,
                analysis_type='qualitative_summary'
            )
            
            if summary_result.success:
                self.gdr['gdr_resumo_qualitativo'] = summary_result.final_result.get('summary', '')
                
        except Exception as e:
            logger.error(f"Erro na análise com IA: {str(e)}")
    
    async def _generate_sales_approach(self):
        """Gera abordagem de vendas personalizada"""
        if not self.multi_llm:
            return
        
        try:
            # Dados para abordagem
            approach_data = {
                'nome': self.gdr.get('gdr_nome'),
                'tipo_negocio': 'assistência técnica de celulares',
                'pontos_fortes': self._identify_strengths(),
                'oportunidades': self._identify_opportunities(),
                'contexto_local': {
                    'concorrentes': self.gdr.get('gdr_total_concorrentes', 0),
                    'rating': self.gdr.get('gdr_rating_google', 0)
                }
            }
            
            # Gerar abordagem
            result = await self.multi_llm.analyze_with_consensus(
                data=approach_data,
                analysis_type='sales_approach'
            )
            
            if result.success:
                self.gdr['gdr_abordagem_sugerida'] = result.final_result.get('approach', '')
                self.gdr['gdr_gancho_vendas'] = result.final_result.get('hook', '')
                
                # Atualizar métricas de consenso se ainda não existirem
                if 'gdr_consensus_method' not in self.gdr:
                    self.gdr['gdr_consensus_method'] = result.consensus_method
                    self.gdr['gdr_agreement_score'] = result.agreement_score
                    self.gdr['gdr_participating_llms'] = ', '.join(result.participating_llms)
                    self.gdr['gdr_consensus_divergences'] = len(result.divergences)
                
        except Exception as e:
            logger.error(f"Erro ao gerar abordagem: {str(e)}")
    
    def _identify_strengths(self) -> List[str]:
        """Identifica pontos fortes do lead"""
        strengths = []
        
        if self.gdr.get('gdr_rating_google', 0) >= 4.5:
            strengths.append('Excelente reputação online')
        
        if self.gdr.get('gdr_total_reviews_google', 0) > 100:
            strengths.append('Alto volume de avaliações')
        
        if self.gdr.get('gdr_website'):
            strengths.append('Presença digital estabelecida')
        
        if self.gdr.get('gdr_whatsapp'):
            strengths.append('Atendimento por WhatsApp')
        
        return strengths
    
    def _identify_opportunities(self) -> List[str]:
        """Identifica oportunidades de melhoria"""
        opportunities = []
        
        if not self.gdr.get('gdr_website'):
            opportunities.append('Criar presença online')
        
        if self.gdr.get('gdr_rating_google', 0) < 4:
            opportunities.append('Melhorar reputação online')
        
        if self.gdr.get('gdr_total_reviews_google', 0) < 10:
            opportunities.append('Aumentar volume de avaliações')
        
        if not self.gdr.get('gdr_whatsapp'):
            opportunities.append('Implementar atendimento WhatsApp')
        
        return opportunities
    
    def _calculate_basic_score(self):
        """Calcula score básico (modo BASIC)"""
        score = 50  # Base
        
        # Rating
        rating = self.gdr.get('gdr_rating_google', 0)
        if rating >= 4.5:
            score += 20
        elif rating >= 4:
            score += 10
        elif rating >= 3.5:
            score += 5
        
        # Reviews
        reviews = self.gdr.get('gdr_total_reviews_google', 0)
        if reviews > 100:
            score += 15
        elif reviews > 50:
            score += 10
        elif reviews > 10:
            score += 5
        
        # Contatos
        if self.gdr.get('gdr_telefone_1'):
            score += 5
        if self.gdr.get('gdr_whatsapp'):
            score += 10
        if self.gdr.get('gdr_website'):
            score += 10
        
        self.gdr['gdr_score'] = min(score, 100)
        self.gdr['gdr_score_categoria'] = self._get_score_category(score)
        self.gdr['gdr_motivo_score'] = 'Score básico baseado em dados públicos'
    
    async def _calculate_advanced_score(self):
        """Calcula score avançado (modo FULL)"""
        if self.scoring_system:
            # Usar sistema de scoring avançado
            score_result = self.scoring_system.calculate_score(self.gdr)
            
            self.gdr['gdr_score'] = score_result['final_score']
            self.gdr['gdr_score_categoria'] = score_result['category']
            self.gdr['gdr_score_detalhado'] = score_result.get('detailed_scores', {})
            
            # Gerar motivo
            motivos = []
            for criteria, value in score_result.get('detailed_scores', {}).items():
                if value > 80:
                    motivos.append(f"{criteria}: excelente")
                elif value < 40:
                    motivos.append(f"{criteria}: precisa melhorar")
            
            self.gdr['gdr_motivo_score'] = '; '.join(motivos) if motivos else 'Score calculado com múltiplos critérios'
        else:
            # Fallback para cálculo básico
            self._calculate_basic_score()
    
    def _get_score_category(self, score: float) -> str:
        """Retorna categoria baseada no score"""
        if score >= 85:
            return 'Excelente'
        elif score >= 70:
            return 'Muito Bom'
        elif score >= 55:
            return 'Bom'
        elif score >= 40:
            return 'Regular'
        else:
            return 'Fraco'
    
    async def _extract_contacts_from_content(self, content: str):
        """Extrai contatos adicionais de conteúdo"""
        if not self.contact_extractor or not content:
            return
        
        # Extrair e-mails adicionais
        emails = self.contact_extractor.extract_emails(content)
        if emails and not self.gdr.get('gdr_email_1'):
            self.gdr['gdr_email_1'] = emails[0]
        
        # Extrair redes sociais
        social_patterns = {
            'facebook': r'facebook\.com/([^/\s]+)',
            'instagram': r'instagram\.com/([^/\s]+)',
            'linkedin': r'linkedin\.com/company/([^/\s]+)'
        }
        
        import re
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                self.gdr[f'gdr_url_{platform}'] = f"https://{platform}.com/{match.group(1)}"
    
    def _calculate_advanced_metrics(self):
        """Calcula métricas avançadas para modo premium"""
        try:
            # Completude dos dados
            total_fields = len([k for k in self.gdr.keys() if k.startswith('gdr_')])
            filled_fields = len([k for k, v in self.gdr.items() if k.startswith('gdr_') and v])
            self.gdr['gdr_data_completeness'] = round((filled_fields / total_fields * 100), 2) if total_fields > 0 else 0
            
            # Score de confiança geral
            confidence_factors = []
            
            # Fator 1: Múltiplas fontes de dados
            sources_count = sum([
                1 if self.gdr.get('gdr_rating_google') else 0,
                1 if self.gdr.get('gdr_url_instagram') else 0,
                1 if self.gdr.get('gdr_url_facebook') else 0,
                1 if self.gdr.get('gdr_website') else 0,
                1 if self.gdr.get('gdr_cse_results') else 0
            ])
            confidence_factors.append(min(sources_count / 5, 1.0))
            
            # Fator 2: Qualidade do consenso
            if self.gdr.get('gdr_agreement_score'):
                confidence_factors.append(self.gdr['gdr_agreement_score'])
            
            # Fator 3: Quantidade de reviews
            reviews_count = self.gdr.get('gdr_total_reviews_google', 0)
            confidence_factors.append(min(reviews_count / 100, 1.0))
            
            # Score final de confiança
            if confidence_factors:
                self.gdr['gdr_confidence_score'] = round(sum(confidence_factors) / len(confidence_factors), 3)
            
            # Índice de presença digital
            digital_presence = {
                'website': 25 if self.gdr.get('gdr_website') else 0,
                'instagram': 20 if self.gdr.get('gdr_url_instagram') else 0,
                'facebook': 20 if self.gdr.get('gdr_url_facebook') else 0,
                'google_rating': 15 if self.gdr.get('gdr_rating_google', 0) >= 4.0 else 5,
                'reviews': 20 if self.gdr.get('gdr_total_reviews_google', 0) >= 50 else 10
            }
            self.gdr['gdr_digital_presence_index'] = sum(digital_presence.values())
            
            logger.info(f"📊 Métricas avançadas calculadas: Completude={self.gdr['gdr_data_completeness']}%, "
                       f"Confiança={self.gdr.get('gdr_confidence_score', 0):.2f}")
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas avançadas: {str(e)}")
    
    def _finalize_processing(self):
        """Finaliza o processamento"""
        # Status final
        self.gdr['gdr_status'] = 'concluido'
        
        # LLMs usados
        if self.multi_llm:
            self.gdr['gdr_llms_usados'] = ', '.join(self.multi_llm.llm_configs.keys())
        
        # Timestamp
        self.gdr['gdr_data_atualizacao'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Remover campos vazios opcionais
        optional_fields = ['gdr_telefone_2', 'gdr_email_2']
        for field in optional_fields:
            if not self.gdr.get(field):
                self.gdr.pop(field, None)

# ===================================================================================
# FUNÇÕES AUXILIARES
# ===================================================================================

def get_processor_config(mode: str = 'full_strategy') -> Dict[str, Any]:
    """
    Retorna configuração padrão para o processador
    
    Args:
        mode: 'basic' ou 'full_strategy'
        
    Returns:
        Dict com configurações
    """
    config = {
        'ANALYSIS_MODE': mode,
        'enable_scraping': mode == 'full_strategy',
        'enable_facade_analysis': mode == 'full_strategy',
        'enable_ai_analysis': mode == 'full_strategy',
        'batch_size': 20 if mode == 'basic' else 5,
        'timeout_per_lead': 10 if mode == 'basic' else 60
    }
    
    return config

# ===================================================================================
# EXEMPLO DE USO
# ===================================================================================

if __name__ == "__main__":
    # Exemplo de configuração
    print("📋 Modos disponíveis:")
    print("1. BASIC - Coleta rápida de dados públicos")
    print("2. FULL_STRATEGY - Análise completa com IA")
    
    # Configuração BASIC
    config_basic = get_processor_config('basic')
    print("\n⚡ Configuração BASIC:")
    print(config_basic)
    
    # Configuração FULL
    config_full = get_processor_config('full_strategy')  
    print("\n🚀 Configuração FULL STRATEGY:")
    print(config_full)