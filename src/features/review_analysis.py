import asyncio
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

# ===================================================================================
# CÉLULA 7: ANÁLISE DE REVIEWS E FACADE
# ===================================================================================

class ReviewsAnalyzer:
    """Analisador avançado de reviews"""
    
    def __init__(self, max_reviews: int = 20, max_chars_per_review: int = 500):
        self.max_reviews = max_reviews
        self.max_chars_per_review = max_chars_per_review
        self.max_total_chars = 4000
        
        # Dicionários de análise
        self.sentiment_keywords = {
            'positive': {
                'atendimento': ['atendimento', 'atencioso', 'educado', 'gentil', 'prestativo', 
                               'cordial', 'simpático', 'solicito'],
                'qualidade': ['qualidade', 'excelente', 'ótimo', 'perfeito', 'bom', 'top',
                             'melhor', 'incrível', 'maravilhoso'],
                'rapidez': ['rápido', 'ágil', 'rapidez', 'agilidade', 'eficiente', 'pontual'],
                'preço': ['preço', 'barato', 'justo', 'econômico', 'custo-benefício', 'vale'],
                'honestidade': ['honesto', 'confiável', 'transparente', 'sincero', 'correto'],
                'limpeza': ['limpo', 'organizado', 'higiene', 'limpeza', 'impecável'],
                'recomendação': ['recomendo', 'indico', 'voltarei', 'retornarei', 'fidelizado']
            },
            'negative': {
                'demora': ['demora', 'demorado', 'lento', 'espera', 'aguardar', 'horas'],
                'caro': ['caro', 'caríssimo', 'abusivo', 'exploração', 'roubo', 'absurdo'],
                'atendimento_ruim': ['grosso', 'mal educado', 'ignorante', 'despreparado', 
                                    'grosseria', 'descaso', 'péssimo atendimento'],
                'qualidade_ruim': ['ruim', 'péssimo', 'defeito', 'problema', 'quebrado', 
                                  'estragado', 'mal feito'],
                'desorganização': ['desorganizado', 'bagunça', 'confusão', 'perdido', 'caos'],
                'desonestidade': ['enganado', 'mentira', 'falso', 'propaganda enganosa'],
                'sujeira': ['sujo', 'imundo', 'nojento', 'falta de higiene']
            }
        }
    
    def extract_and_analyze_reviews(self, place_details: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai e analisa reviews completas"""
        try:
            # Extrair reviews
            reviews = self._extract_reviews_from_details(place_details)
            
            if not reviews:
                return {
                    'reviews_found': False,
                    'reviews_count': 0,
                    'analysis_text': "Sem avaliações disponíveis para análise",
                    'prepared_reviews': [],
                    'insights': {},
                    'summary': "Estabelecimento sem avaliações registradas"
                }
            
            # Preparar reviews
            prepared_reviews = self._prepare_reviews_for_analysis(reviews)
            
            # Gerar texto para análise
            analysis_text = self._generate_analysis_text(prepared_reviews)
            
            # Extrair insights
            insights = self._extract_detailed_insights(prepared_reviews)
            
            # Gerar resumo executivo
            summary = self._generate_executive_summary(insights, prepared_reviews)
            
            return {
                'reviews_found': True,
                'reviews_count': len(reviews),
                'analysis_text': analysis_text,
                'prepared_reviews': prepared_reviews[:self.max_reviews],
                'insights': insights,
                'summary': summary,
                'sentiment_distribution': insights.get('sentiment_distribution', {}),
                'key_themes': insights.get('key_themes', {})
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar reviews: {e}")
            return {
                'reviews_found': False,
                'reviews_count': 0,
                'analysis_text': f"Erro ao processar avaliações: {str(e)}",
                'prepared_reviews': [],
                'insights': {},
                'summary': "Erro na análise"
            }
    
    def _extract_reviews_from_details(self, place_details: Dict[str, Any]) -> List[Dict]:
        """Extrai reviews de diferentes formatos possíveis"""
        reviews = []
        
        # Tentar múltiplos campos
        review_fields = ['review', 'reviews', 'user_reviews', 'customer_reviews']
        
        for field in review_fields:
            if field in place_details:
                review_data = place_details[field]
                if isinstance(review_data, list):
                    reviews.extend(review_data)
                elif isinstance(review_data, dict):
                    reviews.append(review_data)
        
        # Remover duplicatas
        seen_texts = set()
        unique_reviews = []
        
        for review in reviews:
            if isinstance(review, dict) and 'text' in review:
                text = review.get('text', '').strip()
                # Criar hash do texto para comparação
                text_hash = hashlib.md5(text.encode()).hexdigest()
                
                if text and text_hash not in seen_texts:
                    seen_texts.add(text_hash)
                    unique_reviews.append(review)
        
        # Ordenar por relevância
        unique_reviews.sort(
            key=lambda r: (
                -r.get('rating', 0),                    # Rating maior primeiro
                -len(r.get('text', '')),                # Textos mais longos
                -self._calculate_review_helpfulness(r)   # Reviews mais úteis
            )
        )
        
        return unique_reviews
    
    def _calculate_review_helpfulness(self, review: Dict) -> float:
        """Calcula utilidade de uma review"""
        score = 0
        
        # Texto longo é mais útil
        text_length = len(review.get('text', ''))
        if text_length > 200:
            score += 3
        elif text_length > 100:
            score += 2
        elif text_length > 50:
            score += 1
        
        # Reviews com fotos são mais úteis
        if review.get('photos') or review.get('profile_photo_url'):
            score += 2
        
        # Reviews recentes são mais relevantes
        time_desc = review.get('relative_time_description', '')
        if 'dia' in time_desc or 'day' in time_desc:
            score += 3
        elif 'semana' in time_desc or 'week' in time_desc:
            score += 2
        elif 'mês' in time_desc or 'month' in time_desc:
            score += 1
        
        return score
    
    def _prepare_reviews_for_analysis(self, reviews: List[Dict]) -> List[Dict]:
        """Prepara reviews para análise com IA"""
        prepared = []
        total_chars = 0
        
        for i, review in enumerate(reviews[:self.max_reviews]):
            if total_chars >= self.max_total_chars:
                break
            
            text = review.get('text', '').strip()
            if not text:
                continue
            
            # Truncar se necessário
            if len(text) > self.max_chars_per_review:
                text = text[:self.max_chars_per_review] + "..."
            
            # Preparar review
            prepared_review = {
                'index': i + 1,
                'rating': review.get('rating', 0),
                'text': text,
                'author': review.get('author_name', 'Anônimo'),
                'time': review.get('relative_time_description', ''),
                'language': review.get('language', 'pt'),
                'original_text': review.get('text', ''),  # Manter original
                'has_photo': bool(review.get('photos')),
                'author_level': review.get('author_level', 0)
            }
            
            # Classificar sentimento
            if prepared_review['rating'] >= 4:
                prepared_review['sentiment'] = 'positive'
            elif prepared_review['rating'] >= 3:
                prepared_review['sentiment'] = 'neutral'
            else:
                prepared_review['sentiment'] = 'negative'
            
            # Detectar idioma principal
            prepared_review['is_portuguese'] = self._is_portuguese(text)
            
            prepared.append(prepared_review)
            total_chars += len(text)
        
        return prepared
    
    def _is_portuguese(self, text: str) -> bool:
        """Detecta se o texto está em português"""
        portuguese_indicators = [
            'ção', 'ões', 'mente', 'para', 'muito', 'com', 'que',
            'não', 'mas', 'por', 'uma', 'bem', 'foi', 'está'
        ]
        
        text_lower = text.lower()
        matches = sum(1 for indicator in portuguese_indicators if indicator in text_lower)
        
        return matches >= 3
    
    def _generate_analysis_text(self, prepared_reviews: List[Dict]) -> str:
        """Gera texto formatado para análise de IA"""
        if not prepared_reviews:
            return "Sem avaliações com texto disponível para análise"
        
        # Separar por sentimento
        positive = [r for r in prepared_reviews if r['sentiment'] == 'positive']
        neutral = [r for r in prepared_reviews if r['sentiment'] == 'neutral']
        negative = [r for r in prepared_reviews if r['sentiment'] == 'negative']
        
        sections = []
        
        # Resumo estatístico
        avg_rating = sum(r['rating'] for r in prepared_reviews) / len(prepared_reviews)
        sections.append(
            f"RESUMO: {len(prepared_reviews)} avaliações analisadas, "
            f"média {avg_rating:.1f}★ "
            f"({len(positive)} positivas, {len(neutral)} neutras, {len(negative)} negativas)\n"
        )
        
        # Reviews positivas
        if positive:
            sections.append("AVALIAÇÕES POSITIVAS:")
            for r in positive[:5]:
                excerpt = r['text'][:200]
                sections.append(f"• ({r['rating']}★) \"{excerpt}...\"")
        
        # Reviews negativas
        if negative:
            sections.append("\nAVALIAÇÕES NEGATIVAS:")
            for r in negative[:3]:
                excerpt = r['text'][:200]
                sections.append(f"• ({r['rating']}★) \"{excerpt}...\"")
        
        # Reviews neutras
        if neutral and len(sections) < 10:
            sections.append("\nAVALIAÇÕES NEUTRAS:")
            for r in neutral[:2]:
                excerpt = r['text'][:150]
                sections.append(f"• ({r['rating']}★) \"{excerpt}...\"")
        
        return "\n".join(sections)
    
    def _extract_detailed_insights(self, prepared_reviews: List[Dict]) -> Dict[str, Any]:
        """Extrai insights detalhados das reviews"""
        if not prepared_reviews:
            return {}
        
        insights = {
            'average_rating': sum(r['rating'] for r in prepared_reviews) / len(prepared_reviews),
            'total_analyzed': len(prepared_reviews),
            'sentiment_distribution': self._calculate_sentiment_distribution(prepared_reviews),
            'key_themes': self._extract_key_themes(prepared_reviews),
            'temporal_analysis': self._analyze_temporal_patterns(prepared_reviews),
            'author_analysis': self._analyze_authors(prepared_reviews),
            'detailed_sentiment': self._detailed_sentiment_analysis(prepared_reviews)
        }
        
        return insights
    
    def _calculate_sentiment_distribution(self, reviews: List[Dict]) -> Dict[str, Any]:
        """Calcula distribuição de sentimentos"""
        distribution = {
            'positive': len([r for r in reviews if r['sentiment'] == 'positive']),
            'neutral': len([r for r in reviews if r['sentiment'] == 'neutral']),
            'negative': len([r for r in reviews if r['sentiment'] == 'negative'])
        }
        
        total = sum(distribution.values())
        if total > 0:
            distribution['percentages'] = {
                k: round(v / total * 100, 1) for k, v in distribution.items()
            }
        
        return distribution
    
    def _extract_key_themes(self, reviews: List[Dict]) -> Dict[str, Any]:
        """Extrai temas principais das reviews"""
        positive_mentions = defaultdict(int)
        negative_mentions = defaultdict(int)
        
        # Analisar cada review
        for review in reviews:
            text_lower = review['text'].lower()
            
            # Contar menções positivas
            if review['sentiment'] == 'positive':
                for category, keywords in self.sentiment_keywords['positive'].items():
                    for keyword in keywords:
                        if keyword in text_lower:
                            positive_mentions[category] += 1
                            break
            
            # Contar menções negativas
            elif review['sentiment'] == 'negative':
                for category, keywords in self.sentiment_keywords['negative'].items():
                    for keyword in keywords:
                        if keyword in text_lower:
                            negative_mentions[category] += 1
                            break
        
        # Top temas
        top_positive = sorted(positive_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
        top_negative = sorted(negative_mentions.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'positive_themes': [{'theme': theme, 'count': count} for theme, count in top_positive],
            'negative_themes': [{'theme': theme, 'count': count} for theme, count in top_negative],
            'all_themes': dict(positive_mentions),
            'improvement_areas': dict(negative_mentions)
        }
    
    def _analyze_temporal_patterns(self, reviews: List[Dict]) -> Dict[str, Any]:
        """Analisa padrões temporais nas reviews"""
        temporal_groups = {
            'recent': [],      # últimos 30 dias
            'moderate': [],    # 1-6 meses
            'old': []         # mais de 6 meses
        }
        
        for review in reviews:
            time_desc = review.get('time', '').lower()
            
            if any(word in time_desc for word in ['dia', 'day', 'semana', 'week']):
                temporal_groups['recent'].append(review['rating'])
            elif any(word in time_desc for word in ['mês', 'meses', 'month']):
                # Extrair número de meses se possível
                months = 1
                numbers = re.findall(r'\d+', time_desc)
                if numbers:
                    months = int(numbers[0])
                
                if months <= 6:
                    temporal_groups['moderate'].append(review['rating'])
                else:
                    temporal_groups['old'].append(review['rating'])
            else:
                temporal_groups['old'].append(review['rating'])
        
        # Calcular médias
        analysis = {}
        for period, ratings in temporal_groups.items():
            if ratings:
                analysis[period] = {
                    'count': len(ratings),
                    'average_rating': sum(ratings) / len(ratings),
                    'trend': 'stable'  # Será calculado comparando períodos
                }
        
        # Calcular tendência
        if 'recent' in analysis and 'old' in analysis:
            recent_avg = analysis['recent']['average_rating']
            old_avg = analysis['old']['average_rating']
            
            if recent_avg > old_avg + 0.5:
                analysis['overall_trend'] = 'improving'
            elif recent_avg < old_avg - 0.5:
                analysis['overall_trend'] = 'declining'
            else:
                analysis['overall_trend'] = 'stable'
        
        return analysis
    
    def _analyze_authors(self, reviews: List[Dict]) -> Dict[str, Any]:
        """Analisa perfil dos autores"""
        total_authors = len(reviews)
        
        return {
            'total_authors': total_authors,
            'with_photos': len([r for r in reviews if r.get('has_photo')]),
            'local_guides': len([r for r in reviews if r.get('author_level', 0) > 0]),
            'average_author_level': sum(r.get('author_level', 0) for r in reviews) / total_authors if total_authors > 0 else 0,
            'languages': {
                'portuguese': len([r for r in reviews if r.get('is_portuguese', True)]),
                'other': len([r for r in reviews if not r.get('is_portuguese', True)])
            }
        }
    
    def _detailed_sentiment_analysis(self, reviews: List[Dict]) -> Dict[str, Any]:
        """Análise detalhada de sentimentos"""
        all_text = ' '.join(r['text'] for r in reviews).lower()
        
        # Contar palavras-chave
        keyword_counts = {}
        
        for sentiment_type, categories in self.sentiment_keywords.items():
            keyword_counts[sentiment_type] = {}
            
            for category, keywords in categories.items():
                count = sum(all_text.count(keyword) for keyword in keywords)
                if count > 0:
                    keyword_counts[sentiment_type][category] = count
        
        # Calcular score de sentimento geral
        positive_score = sum(keyword_counts.get('positive', {}).values())
        negative_score = sum(keyword_counts.get('negative', {}).values())
        
        if positive_score + negative_score > 0:
            sentiment_score = (positive_score - negative_score) / (positive_score + negative_score)
        else:
            sentiment_score = 0
        
        return {
            'keyword_analysis': keyword_counts,
            'sentiment_score': round(sentiment_score, 3),  # -1 a 1
            'positivity_ratio': round(positive_score / (positive_score + negative_score), 3) if (positive_score + negative_score) > 0 else 0.5
        }
    
    def _generate_executive_summary(self, insights: Dict[str, Any], reviews: List[Dict]) -> str:
        """Gera resumo executivo das análises"""
        if not insights:
            return "Dados insuficientes para gerar resumo"
        
        parts = []
        
        # Sentimento geral
        sentiment_dist = insights.get('sentiment_distribution', {})
        if sentiment_dist:
            percentages = sentiment_dist.get('percentages', {})
            if percentages.get('positive', 0) >= 80:
                parts.append("Excelente reputação com avaliações predominantemente positivas")
            elif percentages.get('positive', 0) >= 60:
                parts.append("Boa reputação com maioria de avaliações positivas")
            elif percentages.get('negative', 0) >= 40:
                parts.append("Reputação mista com pontos de atenção importantes")
            else:
                parts.append("Reputação em construção")
        
        # Temas principais
        key_themes = insights.get('key_themes', {})
        if positive_themes := key_themes.get('positive_themes', []):
            top_positives = [t['theme'] for t in positive_themes[:3]]
            parts.append(f"Destaques: {', '.join(top_positives)}")
        
        if negative_themes := key_themes.get('negative_themes', []):
            top_negatives = [t['theme'] for t in negative_themes[:2]]
            parts.append(f"Melhorias sugeridas: {', '.join(top_negatives)}")
        
        # Tendência temporal
        temporal = insights.get('temporal_analysis', {})
        if trend := temporal.get('overall_trend'):
            if trend == 'improving':
                parts.append("Tendência de melhoria nas avaliações recentes")
            elif trend == 'declining':
                parts.append("Atenção: tendência de queda nas avaliações recentes")
        
        return ". ".join(parts) if parts else "Estabelecimento com histórico de avaliações em análise"
    
    def format_analysis_for_gdr(self, analysis_result: Dict[str, Any]) -> str:
        """Formata análise para campo GDR"""
        if not analysis_result.get('reviews_found'):
            return analysis_result.get('analysis_text', 'Sem avaliações disponíveis')
        
        # Usar o resumo executivo como base
        summary = analysis_result.get('summary', '')
        
        # Adicionar rating médio
        if avg_rating := analysis_result.get('insights', {}).get('average_rating'):
            summary = f"({avg_rating:.1f}★) {summary}"
        
        # Limitar tamanho
        if len(summary) > 500:
            summary = summary[:497] + "..."
        
        return summary


class FixedFacadeAnalyzer:
    """Analisador de fachada com Street View e análise por IA"""
    
    def __init__(self, google_maps_api_key: str, multi_llm: Optional[Any] = None):
        self.api_key = google_maps_api_key
        self.multi_llm = multi_llm
        self.base_url = "https://maps.googleapis.com/maps/api/streetview"
        self.metadata_url = f"{self.base_url}/metadata"
        
        # Cache de análises
        self.analysis_cache = {}
    
    async def analyze_facade_safe(self, location: Dict[str, float], 
                                 lead_info: Dict[str, Any]) -> str:
        """Analisa fachada com verificação e fallback"""
        try:
            # Verificar cache
            cache_key = f"{location['lat']}_{location['lng']}"
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]
            
            # Verificar disponibilidade do Street View
            if not await self._check_streetview_availability(location):
                return await self._generate_fallback_analysis(lead_info)
            
            # Baixar imagem
            image_data = await self._download_streetview_image(location)
            if not image_data:
                return await self._generate_fallback_analysis(lead_info)
            
            # Analisar com IA se disponível
            if self.multi_llm and self.multi_llm.active_llm:
                analysis = await self._analyze_image_with_ai(image_data, lead_info)
            else:
                analysis = await self._generate_visual_description(image_data, lead_info)
            
            # Cachear resultado
            self.analysis_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise de fachada: {e}")
            return await self._