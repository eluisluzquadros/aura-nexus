# -*- coding: utf-8 -*-
"""
AURA NEXUS v26.0 - CÉLULA 19: DATA REVIEW & VALIDATION AGENT
Sistema inteligente de revisão e validação de dados com feedback loop
"""
import re
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import numpy as np
from collections import defaultdict
import phonenumbers
from urllib.parse import urlparse
import validators
import pandas as pd

# Configurar logger
logger = logging.getLogger("AURA_NEXUS.DataReview")

# ===================================================================================
# CLASSE: DataReviewAgent
# ===================================================================================

class DataReviewAgent:
    """Agente inteligente de revisão e validação de dados"""
    
    def __init__(self, 
                 consensus_orchestrator: Any = None,
                 learning_enabled: bool = True):
        """
        Inicializa o agente de revisão
        
        Args:
            consensus_orchestrator: Instância do MultiLLMConsensusOrchestrator
            learning_enabled: Se deve aprender com correções
        """
        self.consensus_orchestrator = consensus_orchestrator
        self.learning_enabled = learning_enabled
        
        # Regras de validação por tipo
        self.validation_rules = self._initialize_validation_rules()
        
        # Histórico de correções para aprendizado
        self.correction_history = defaultdict(list)
        
        # Cache de validações
        self.validation_cache = {}
        
        # Estatísticas
        self.stats = {
            'total_reviews': 0,
            'validation_errors': 0,
            'auto_corrections': 0,
            're_analysis_requests': 0,
            'quality_improvements': 0
        }
        
        # Thresholds de qualidade
        self.quality_thresholds = {
            'min_score_confidence': 0.7,
            'max_score_variance': 15,
            'min_data_completeness': 0.6,
            'min_consensus_agreement': 0.6
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Inicializa regras de validação por tipo de dado"""
        return {
            'score': {
                'type': 'numeric',
                'min': 0,
                'max': 100,
                'required': True,
                'validator': self._validate_score
            },
            'phone': {
                'type': 'string',
                'pattern': r'^\+?[\d\s\-\(\)]+$',
                'min_length': 10,
                'validator': self._validate_phone
            },
            'email': {
                'type': 'string',
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'validator': self._validate_email
            },
            'website': {
                'type': 'url',
                'validator': self._validate_url
            },
            'social_url': {
                'type': 'url',
                'platforms': ['instagram', 'facebook', 'linkedin', 'twitter', 'tiktok'],
                'validator': self._validate_social_url
            },
            'rating': {
                'type': 'numeric',
                'min': 0,
                'max': 5,
                'decimal_places': 1,
                'validator': self._validate_rating
            },
            'sentiment': {
                'type': 'enum',
                'values': ['MUITO_POSITIVO', 'POSITIVO', 'NEUTRO', 'NEGATIVO', 'MUITO_NEGATIVO'],
                'validator': self._validate_sentiment
            },
            'business_hours': {
                'type': 'complex',
                'validator': self._validate_business_hours
            }
        }
    
    async def review_consensus_result(self, 
                                    consensus_result: Any,
                                    analysis_type: str,
                                    original_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revisa e valida resultado do consenso
        
        Args:
            consensus_result: Resultado do consenso Multi-LLM
            analysis_type: Tipo de análise realizada
            original_data: Dados originais analisados
            
        Returns:
            Dict com resultado revisado e melhorado
        """
        self.stats['total_reviews'] += 1
        
        # 1. Validação estrutural
        structural_issues = await self._validate_structure(
            consensus_result.final_analysis, 
            analysis_type
        )
        
        # 2. Validação de conteúdo
        content_issues = await self._validate_content(
            consensus_result.final_analysis,
            analysis_type,
            original_data
        )
        
        # 3. Análise de qualidade
        quality_assessment = await self._assess_quality(
            consensus_result,
            analysis_type
        )
        
        # 4. Decisão sobre ação necessária
        action_needed = self._determine_action(
            structural_issues,
            content_issues,
            quality_assessment
        )
        
        # 5. Executar ação apropriada
        if action_needed == 'APPROVE':
            return await self._approve_result(consensus_result)
            
        elif action_needed == 'AUTO_CORRECT':
            return await self._auto_correct(
                consensus_result,
                structural_issues + content_issues,
                analysis_type
            )
            
        elif action_needed == 'RE_ANALYZE':
            return await self._request_re_analysis(
                original_data,
                analysis_type,
                structural_issues + content_issues,
                consensus_result
            )
            
        else:  # MANUAL_REVIEW
            return await self._flag_for_manual_review(
                consensus_result,
                structural_issues + content_issues
            )
    
    async def _validate_structure(self, 
                                analysis: Dict[str, Any],
                                analysis_type: str) -> List[Dict[str, Any]]:
        """Valida estrutura do resultado"""
        issues = []
        
        # Definir campos obrigatórios por tipo
        required_fields = {
            'scoring': ['score_final', 'justificativa', 'criterios_atendidos'],
            'business_analysis': ['resumo_qualitativo', 'pontos_fortes', 'oportunidades', 'score_potencial'],
            'review_sentiment': ['sentimento_geral', 'score_sentimento', 'aspectos_positivos'],
            'sales_approach': ['abordagem_inicial', 'proposta_valor', 'pontos_de_valor'],
            'contact_extraction': ['telefones', 'emails', 'websites']
        }
        
        # Verificar campos obrigatórios
        fields = required_fields.get(analysis_type, [])
        for field in fields:
            if field not in analysis:
                issues.append({
                    'type': 'missing_field',
                    'field': field,
                    'severity': 'high',
                    'message': f'Campo obrigatório ausente: {field}'
                })
        
        # Verificar tipos de dados
        for field, value in analysis.items():
            expected_type = self._get_expected_type(field, analysis_type)
            if expected_type and not self._check_type(value, expected_type):
                issues.append({
                    'type': 'wrong_type',
                    'field': field,
                    'expected': expected_type,
                    'actual': type(value).__name__,
                    'severity': 'medium'
                })
        
        return issues
    
    async def _validate_content(self,
                              analysis: Dict[str, Any],
                              analysis_type: str,
                              original_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida conteúdo dos dados"""
        issues = []
        
        # Validações específicas por tipo
        if analysis_type == 'scoring':
            issues.extend(await self._validate_scoring_content(analysis))
            
        elif analysis_type == 'contact_extraction':
            issues.extend(await self._validate_contacts(analysis))
            
        elif analysis_type == 'business_analysis':
            issues.extend(await self._validate_business_analysis(analysis, original_data))
            
        elif analysis_type == 'review_sentiment':
            issues.extend(await self._validate_sentiment_analysis(analysis))
        
        return issues
    
    async def _validate_scoring_content(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida conteúdo de scoring"""
        issues = []
        
        # Validar score final
        score = analysis.get('score_final')
        if score is not None:
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                issues.append({
                    'type': 'invalid_range',
                    'field': 'score_final',
                    'value': score,
                    'severity': 'high',
                    'message': 'Score deve estar entre 0 e 100'
                })
        
        # Validar consistência entre critérios e pontos
        criterios = analysis.get('criterios_atendidos', {})
        pontos = analysis.get('pontos_detalhados', {})
        
        for criterio, atendido in criterios.items():
            if criterio in pontos:
                pontos_criterio = pontos[criterio]
                
                # Se não atendido, pontos devem ser 0
                if not atendido and pontos_criterio > 0:
                    issues.append({
                        'type': 'inconsistency',
                        'field': f'pontos_detalhados.{criterio}',
                        'severity': 'medium',
                        'message': f'Critério {criterio} não atendido mas tem {pontos_criterio} pontos'
                    })
        
        # Validar soma dos pontos
        if pontos:
            soma_pontos = sum(pontos.values())
            if abs(soma_pontos - score) > 5:  # Tolerância de 5 pontos
                issues.append({
                    'type': 'calculation_error',
                    'field': 'score_final',
                    'severity': 'high',
                    'message': f'Soma dos pontos ({soma_pontos}) difere do score final ({score})'
                })
        
        return issues
    
    async def _validate_contacts(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida contatos extraídos"""
        issues = []
        
        # Validar telefones
        phones = analysis.get('telefones', [])
        for i, phone in enumerate(phones):
            if not self._validate_phone(phone):
                issues.append({
                    'type': 'invalid_phone',
                    'field': f'telefones[{i}]',
                    'value': phone,
                    'severity': 'medium'
                })
        
        # Validar emails
        emails = analysis.get('emails', [])
        for i, email in enumerate(emails):
            if not self._validate_email(email):
                issues.append({
                    'type': 'invalid_email',
                    'field': f'emails[{i}]',
                    'value': email,
                    'severity': 'medium'
                })
        
        # Validar websites
        websites = analysis.get('websites', [])
        for i, website in enumerate(websites):
            if not self._validate_url(website):
                issues.append({
                    'type': 'invalid_url',
                    'field': f'websites[{i}]',
                    'value': website,
                    'severity': 'medium'
                })
        
        return issues
    
    async def _assess_quality(self, 
                            consensus_result: Any,
                            analysis_type: str) -> Dict[str, Any]:
        """Avalia qualidade geral do resultado"""
        assessment = {
            'overall_quality': 1.0,
            'factors': {},
            'recommendations': []
        }
        
        # 1. Acordo entre LLMs
        agreement = consensus_result.agreement_score
        assessment['factors']['llm_agreement'] = agreement
        if agreement < self.quality_thresholds['min_consensus_agreement']:
            assessment['overall_quality'] *= 0.8
            assessment['recommendations'].append('Baixo acordo entre LLMs')
        
        # 2. Completude dos dados
        completeness = self._calculate_completeness(consensus_result.final_analysis, analysis_type)
        assessment['factors']['data_completeness'] = completeness
        if completeness < self.quality_thresholds['min_data_completeness']:
            assessment['overall_quality'] *= 0.9
            assessment['recommendations'].append('Dados incompletos')
        
        # 3. Confiança individual dos LLMs
        avg_confidence = np.mean([r.confidence for r in consensus_result.individual_results])
        assessment['factors']['avg_confidence'] = avg_confidence
        if avg_confidence < self.quality_thresholds['min_score_confidence']:
            assessment['overall_quality'] *= 0.85
            assessment['recommendations'].append('Baixa confiança dos LLMs')
        
        # 4. Variância em scores (se aplicável)
        if analysis_type == 'scoring':
            scores = [r.analysis.get('score_final', 0) for r in consensus_result.individual_results 
                     if 'score_final' in r.analysis]
            if scores:
                variance = np.std(scores)
                assessment['factors']['score_variance'] = variance
                if variance > self.quality_thresholds['max_score_variance']:
                    assessment['overall_quality'] *= 0.7
                    assessment['recommendations'].append(f'Alta variância nos scores: {variance:.1f}')
        
        return assessment
    
    def _determine_action(self,
                         structural_issues: List[Dict],
                         content_issues: List[Dict],
                         quality_assessment: Dict[str, Any]) -> str:
        """Determina ação necessária baseado nas validações"""
        
        # Contar severidades
        high_severity = sum(1 for issue in structural_issues + content_issues 
                          if issue.get('severity') == 'high')
        medium_severity = sum(1 for issue in structural_issues + content_issues 
                            if issue.get('severity') == 'medium')
        
        quality_score = quality_assessment['overall_quality']
        
        # Regras de decisão
        if high_severity == 0 and medium_severity <= 2 and quality_score >= 0.8:
            return 'APPROVE'
        
        elif high_severity <= 1 and medium_severity <= 4 and quality_score >= 0.6:
            return 'AUTO_CORRECT'
        
        elif high_severity <= 3 or quality_score >= 0.4:
            return 'RE_ANALYZE'
        
        else:
            return 'MANUAL_REVIEW'
    
    async def _auto_correct(self,
                          consensus_result: Any,
                          issues: List[Dict],
                          analysis_type: str) -> Dict[str, Any]:
        """Aplica correções automáticas"""
        self.stats['auto_corrections'] += 1
        
        corrected_analysis = consensus_result.final_analysis.copy()
        corrections_applied = []
        
        for issue in issues:
            if issue['type'] == 'missing_field':
                # Tentar inferir campo faltante
                inferred_value = await self._infer_missing_field(
                    issue['field'], 
                    corrected_analysis,
                    analysis_type
                )
                if inferred_value is not None:
                    corrected_analysis[issue['field']] = inferred_value
                    corrections_applied.append(f"Inferido {issue['field']}: {inferred_value}")
            
            elif issue['type'] == 'invalid_range':
                # Ajustar para range válido
                field = issue['field']
                value = issue['value']
                
                if field == 'score_final':
                    corrected_value = max(0, min(100, value))
                    corrected_analysis[field] = corrected_value
                    corrections_applied.append(f"Ajustado {field}: {value} → {corrected_value}")
            
            elif issue['type'] == 'calculation_error':
                # Recalcular valores
                if issue['field'] == 'score_final':
                    pontos = corrected_analysis.get('pontos_detalhados', {})
                    corrected_score = sum(pontos.values())
                    corrected_analysis['score_final'] = corrected_score
                    corrections_applied.append(f"Recalculado score: {corrected_score}")
        
        # Registrar correções para aprendizado
        if self.learning_enabled:
            self.correction_history[analysis_type].append({
                'timestamp': datetime.now(),
                'issues': issues,
                'corrections': corrections_applied,
                'original': consensus_result.final_analysis,
                'corrected': corrected_analysis
            })
        
        return {
            'status': 'auto_corrected',
            'analysis': corrected_analysis,
            'corrections_applied': corrections_applied,
            'quality_score': 0.85,  # Penalidade por precisar correção
            'review_notes': f"Auto-corrigido: {len(corrections_applied)} correções aplicadas"
        }
    
    async def _request_re_analysis(self,
                                 original_data: Dict[str, Any],
                                 analysis_type: str,
                                 issues: List[Dict],
                                 previous_result: Any) -> Dict[str, Any]:
        """Solicita re-análise com feedback"""
        self.stats['re_analysis_requests'] += 1
        
        if not self.consensus_orchestrator:
            return {
                'status': 'failed',
                'analysis': previous_result.final_analysis,
                'error': 'Consensus orchestrator não disponível para re-análise'
            }
        
        # Criar prompt melhorado com feedback
        feedback_prompt = self._create_feedback_prompt(issues, analysis_type)
        
        # Modificar dados para incluir contexto
        enhanced_data = original_data.copy()
        enhanced_data['_review_feedback'] = feedback_prompt
        enhanced_data['_previous_issues'] = [issue['message'] for issue in issues[:3]]
        
        # Solicitar nova análise
        try:
            new_result = await self.consensus_orchestrator.analyze_with_consensus(
                enhanced_data,
                analysis_type,
                llms_to_use=None  # Usar todos disponíveis
            )
            
            # Validar nova análise
            new_issues = await self._validate_structure(new_result.final_analysis, analysis_type)
            new_issues.extend(await self._validate_content(new_result.final_analysis, analysis_type, original_data))
            
            # Se melhorou significativamente, aprovar
            if len(new_issues) < len(issues) / 2:
                self.stats['quality_improvements'] += 1
                return {
                    'status': 're_analyzed',
                    'analysis': new_result.final_analysis,
                    'quality_score': 0.9,
                    'review_notes': 'Re-análise bem-sucedida com melhorias'
                }
            else:
                # Ainda tem problemas, mas retornar o melhor
                return {
                    'status': 're_analyzed_partial',
                    'analysis': new_result.final_analysis,
                    'quality_score': 0.7,
                    'remaining_issues': new_issues[:3],
                    'review_notes': 'Re-análise parcialmente bem-sucedida'
                }
                
        except Exception as e:
            logger.error(f"Erro na re-análise: {e}")
            return {
                'status': 'failed',
                'analysis': previous_result.final_analysis,
                'error': str(e)
            }
    
    def _create_feedback_prompt(self, issues: List[Dict], analysis_type: str) -> str:
        """Cria prompt de feedback para re-análise"""
        feedback = f"\n\nATENÇÃO: A análise anterior teve os seguintes problemas:\n"
        
        # Agrupar por tipo
        issues_by_type = defaultdict(list)
        for issue in issues[:5]:  # Limitar feedback
            issues_by_type[issue['type']].append(issue)
        
        for issue_type, type_issues in issues_by_type.items():
            if issue_type == 'missing_field':
                fields = [i['field'] for i in type_issues]
                feedback += f"- Campos obrigatórios faltando: {', '.join(fields)}\n"
            
            elif issue_type == 'invalid_range':
                for i in type_issues:
                    feedback += f"- {i['field']}: valor {i['value']} fora do range válido\n"
            
            elif issue_type == 'calculation_error':
                feedback += f"- Erro de cálculo detectado nos scores\n"
        
        feedback += "\nPor favor, corrija estes problemas na nova análise."
        
        return feedback
    
    # Métodos de validação específicos
    def _validate_phone(self, phone: str) -> bool:
        """Valida número de telefone"""
        if not phone:
            return False
        
        # Remover caracteres especiais
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Verificar comprimento mínimo
        if len(clean_phone) < 10:
            return False
        
        # Tentar validar com phonenumbers
        try:
            parsed = phonenumbers.parse(clean_phone, "BR")  # Default Brasil
            return phonenumbers.is_valid_number(parsed)
        except:
            # Fallback para validação simples
            return bool(re.match(r'^\+?\d{10,15}$', clean_phone))
    
    def _validate_email(self, email: str) -> bool:
        """Valida endereço de email"""
        return validators.email(email) if email else False
    
    def _validate_url(self, url: str) -> bool:
        """Valida URL"""
        return validators.url(url) if url else False
    
    def _validate_social_url(self, url: str, platform: Optional[str] = None) -> bool:
        """Valida URL de rede social"""
        if not self._validate_url(url):
            return False
        
        # Padrões por plataforma
        patterns = {
            'instagram': r'instagram\.com/[\w\-\.]+',
            'facebook': r'facebook\.com/[\w\-\.]+|fb\.com/[\w\-\.]+',
            'linkedin': r'linkedin\.com/(company|in)/[\w\-]+',
            'twitter': r'twitter\.com/[\w]+|x\.com/[\w]+',
            'tiktok': r'tiktok\.com/@[\w\-\.]+'
        }
        
        if platform and platform in patterns:
            return bool(re.search(patterns[platform], url, re.IGNORECASE))
        
        # Verificar se é alguma rede social conhecida
        for pattern in patterns.values():
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_score(self, score: Any) -> bool:
        """Valida score (0-100)"""
        try:
            score_num = float(score)
            return 0 <= score_num <= 100
        except:
            return False
    
    def _validate_rating(self, rating: Any) -> bool:
        """Valida rating (0-5)"""
        try:
            rating_num = float(rating)
            return 0 <= rating_num <= 5
        except:
            return False
    
    def _validate_sentiment(self, sentiment: str) -> bool:
        """Valida sentimento"""
        valid_sentiments = ['MUITO_POSITIVO', 'POSITIVO', 'NEUTRO', 'NEGATIVO', 'MUITO_NEGATIVO']
        return sentiment in valid_sentiments
    
    def _validate_business_hours(self, hours: Any) -> bool:
        """Valida horário comercial"""
        # Implementação simplificada
        return isinstance(hours, (dict, str))
    
    def _calculate_completeness(self, analysis: Dict[str, Any], analysis_type: str) -> float:
        """Calcula completude dos dados"""
        expected_fields = {
            'scoring': ['score_final', 'justificativa', 'criterios_atendidos', 'pontos_detalhados'],
            'business_analysis': ['resumo_qualitativo', 'pontos_fortes', 'oportunidades', 
                                'score_potencial', 'recomendacoes'],
            'review_sentiment': ['sentimento_geral', 'score_sentimento', 'aspectos_positivos',
                               'aspectos_negativos', 'resumo'],
            'sales_approach': ['abordagem_inicial', 'proposta_valor', 'pontos_de_valor',
                             'objecoes_comuns', 'tom_comunicacao'],
            'contact_extraction': ['telefones', 'emails', 'websites', 'whatsapp']
        }
        
        fields = expected_fields.get(analysis_type, [])
        if not fields:
            return 1.0
        
        present_fields = sum(1 for field in fields if field in analysis and analysis[field])
        return present_fields / len(fields)
    
    async def _infer_missing_field(self, 
                                  field: str, 
                                  analysis: Dict[str, Any],
                                  analysis_type: str) -> Any:
        """Tenta inferir valor para campo faltante"""
        # Inferências simples baseadas em outros campos
        inferences = {
            'justificativa': lambda: f"Score {analysis.get('score_final', 0)} baseado nos critérios avaliados",
            'resumo': lambda: self._generate_summary_from_analysis(analysis),
            'recomendacoes': lambda: self._generate_recommendations(analysis, analysis_type),
            'tom_comunicacao': lambda: 'consultivo' if analysis.get('score_potencial', 0) > 70 else 'informal'
        }
        
        if field in inferences:
            return inferences[field]()
        
        return None
    
    def _generate_summary_from_analysis(self, analysis: Dict[str, Any]) -> str:
        """Gera resumo a partir da análise"""
        if 'pontos_fortes' in analysis and analysis['pontos_fortes']:
            return f"Negócio com pontos fortes em: {', '.join(analysis['pontos_fortes'][:3])}"
        elif 'score_final' in analysis:
            score = analysis['score_final']
            if score >= 80:
                return "Excelente potencial identificado"
            elif score >= 60:
                return "Bom potencial com oportunidades de melhoria"
            else:
                return "Potencial moderado, requer desenvolvimento"
        return "Análise em processamento"
    
    def _generate_recommendations(self, analysis: Dict[str, Any], analysis_type: str) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        if analysis_type == 'scoring':
            score = analysis.get('score_final', 0)
            criterios = analysis.get('criterios_atendidos', {})
            
            if not criterios.get('whatsapp'):
                recommendations.append("Implementar atendimento via WhatsApp")
            if not criterios.get('website'):
                recommendations.append("Criar website profissional")
            if score < 70:
                recommendations.append("Melhorar presença digital")
        
        elif analysis_type == 'business_analysis':
            if 'oportunidades' in analysis:
                for opp in analysis['oportunidades'][:2]:
                    recommendations.append(f"Explorar: {opp}")
        
        return recommendations or ["Manter estratégia atual"]
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Retorna insights do aprendizado do agente"""
        insights = {
            'total_corrections': sum(len(h) for h in self.correction_history.values()),
            'common_issues': self._identify_common_issues(),
            'improvement_rate': self._calculate_improvement_rate(),
            'recommendations': self._generate_system_recommendations()
        }
        
        return insights
    
    def _identify_common_issues(self) -> List[Dict[str, Any]]:
        """Identifica problemas mais comuns"""
        issue_counts = defaultdict(int)
        
        for history in self.correction_history.values():
            for entry in history:
                for issue in entry['issues']:
                    issue_counts[issue['type']] += 1
        
        return [
            {'issue': issue_type, 'count': count}
            for issue_type, count in sorted(issue_counts.items(), 
                                          key=lambda x: x[1], 
                                          reverse=True)[:5]
        ]
    
    def _calculate_improvement_rate(self) -> float:
        """Calcula taxa de melhoria ao longo do tempo"""
        if self.stats['re_analysis_requests'] == 0:
            return 0.0
        
        return self.stats['quality_improvements'] / self.stats['re_analysis_requests']
    
    def _generate_system_recommendations(self) -> List[str]:
        """Gera recomendações para melhorar o sistema"""
        recommendations = []
        
        # Baseado em estatísticas
        error_rate = self.stats['validation_errors'] / max(self.stats['total_reviews'], 1)
        if error_rate > 0.2:
            recommendations.append("Alto índice de erros - considerar retreinar LLMs")
        
        if self.stats['re_analysis_requests'] > self.stats['total_reviews'] * 0.3:
            recommendations.append("Muitas re-análises - revisar prompts")
        
        # Baseado em issues comuns
        common_issues = self._identify_common_issues()
        if common_issues and common_issues[0]['count'] > 10:
            recommendations.append(f"Foco em corrigir: {common_issues[0]['issue']}")
        
        return recommendations
    
    async def _approve_result(self, consensus_result: Any) -> Dict[str, Any]:
        """Aprova resultado que passou em todas as validações"""
        return {
            'status': 'approved',
            'analysis': consensus_result.final_analysis,
            'quality_score': 1.0,
            'review_notes': 'Aprovado sem necessidade de correções'
        }
    
    async def _flag_for_manual_review(self,
                                     consensus_result: Any,
                                     issues: List[Dict]) -> Dict[str, Any]:
        """Marca para revisão manual"""
        return {
            'status': 'manual_review_required',
            'analysis': consensus_result.final_analysis,
            'quality_score': 0.3,
            'issues': issues[:10],  # Top 10 issues
            'review_notes': 'Múltiplos problemas detectados - revisão manual necessária'
        }
    
    def _get_expected_type(self, field: str, analysis_type: str) -> Optional[str]:
        """Retorna tipo esperado para um campo"""
        type_mappings = {
            'score_final': 'numeric',
            'score_potencial': 'numeric',
            'score_sentimento': 'numeric',
            'pontos_fortes': 'list',
            'oportunidades': 'list',
            'telefones': 'list',
            'emails': 'list',
            'websites': 'list',
            'criterios_atendidos': 'dict',
            'pontos_detalhados': 'dict'
        }
        
        return type_mappings.get(field)
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Verifica se valor corresponde ao tipo esperado"""
        type_checks = {
            'numeric': lambda v: isinstance(v, (int, float)),
            'string': lambda v: isinstance(v, str),
            'list': lambda v: isinstance(v, list),
            'dict': lambda v: isinstance(v, dict),
            'boolean': lambda v: isinstance(v, bool)
        }
        
        check_func = type_checks.get(expected_type)
        return check_func(value) if check_func else True


# ===================================================================================
# INTEGRAÇÃO COM O SISTEMA DE CONSENSO
# ===================================================================================

async def enhance_consensus_with_review(consensus_orchestrator: Any,
                                      data: Dict[str, Any],
                                      analysis_type: str) -> Dict[str, Any]:
    """
    Função auxiliar para integrar revisão ao consenso
    
    Args:
        consensus_orchestrator: Instância do MultiLLMConsensusOrchestrator
        data: Dados para análise
        analysis_type: Tipo de análise
        
    Returns:
        Resultado revisado e validado
    """
    # Executar análise de consenso normal
    consensus_result = await consensus_orchestrator.analyze_with_consensus(
        data, 
        analysis_type
    )
    
    # Criar agente de revisão
    review_agent = DataReviewAgent(
        consensus_orchestrator=consensus_orchestrator,
        learning_enabled=True
    )
    
    # Revisar e validar resultado
    reviewed_result = await review_agent.review_consensus_result(
        consensus_result,
        analysis_type,
        data
    )
    
    # Log de qualidade
    logger.info(f"Análise {analysis_type} - Status: {reviewed_result['status']}, "
               f"Qualidade: {reviewed_result.get('quality_score', 0):.2f}")
    
    return reviewed_result


# ===================================================================================
# GERAÇÃO DE RELATÓRIOS DE INCONSISTÊNCIAS
# ===================================================================================

def generate_inconsistency_report(df, output_path: str = None) -> Dict[str, Any]:
    """
    Gera relatório detalhado de inconsistências encontradas nos dados
    
    Args:
        df: DataFrame com os dados processados
        output_path: Caminho para salvar o relatório (opcional)
        
    Returns:
        Dicionário com todas as inconsistências encontradas
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_records': len(df),
        'inconsistencies': {
            'critical': [],
            'warning': [],
            'info': []
        },
        'statistics': {},
        'recommendations': []
    }
    
    # 1. Verificar campos obrigatórios ausentes
    required_fields = ['gdr_nome', 'gdr_score_sinergia', 'gdr_motivo_score']
    for field in required_fields:
        if field not in df.columns:
            report['inconsistencies']['critical'].append({
                'type': 'missing_required_field',
                'field': field,
                'message': f'Campo obrigatório {field} não encontrado na planilha'
            })
        else:
            missing_count = df[field].isna().sum()
            if missing_count > 0:
                report['inconsistencies']['critical'].append({
                    'type': 'null_required_field',
                    'field': field,
                    'count': missing_count,
                    'percentage': (missing_count / len(df) * 100),
                    'message': f'{missing_count} registros sem {field} ({missing_count/len(df)*100:.1f}%)'
                })
    
    # 2. Verificar dados de scraping vazios
    scraping_fields = {
        'gdr_url_instagram': 'Instagram',
        'gdr_url_facebook': 'Facebook',
        'gdr_url_linktree': 'Linktree',
        'gdr_fb_followers': 'Facebook followers',
        'gdr_insta_followers': 'Instagram followers'
    }
    
    for field, name in scraping_fields.items():
        if field in df.columns:
            filled_count = df[field].notna().sum()
            if filled_count == 0:
                report['inconsistencies']['warning'].append({
                    'type': 'empty_scraping_data',
                    'field': field,
                    'scraper': name,
                    'message': f'Nenhum dado de {name} foi coletado'
                })
    
    # 3. Verificar análises de consenso
    if 'gdr_llm_usado' in df.columns:
        single_llm = df['gdr_llm_usado'].str.contains(',').sum() == 0
        if single_llm:
            report['inconsistencies']['warning'].append({
                'type': 'no_consensus',
                'message': 'Análises usando apenas um LLM, sem consenso multi-LLM'
            })
    
    # 4. Verificar scores inconsistentes
    if 'gdr_score_sinergia' in df.columns:
        invalid_scores = df[(df['gdr_score_sinergia'] < 0) | (df['gdr_score_sinergia'] > 100)]
        if len(invalid_scores) > 0:
            report['inconsistencies']['critical'].append({
                'type': 'invalid_score',
                'count': len(invalid_scores),
                'records': invalid_scores.index.tolist(),
                'message': f'{len(invalid_scores)} registros com score fora do intervalo 0-100'
            })
    
    # 5. Verificar tokens e custos
    token_fields = ['gdr_total_tokens', 'gdr_total_cost']
    for field in token_fields:
        if field not in df.columns:
            report['inconsistencies']['info'].append({
                'type': 'missing_metrics',
                'field': field,
                'message': f'Campo de métrica {field} não encontrado'
            })
        elif field in df.columns and df[field].sum() == 0:
            report['inconsistencies']['warning'].append({
                'type': 'zero_metrics',
                'field': field,
                'message': f'Métricas de {field} todas zeradas'
            })
    
    # 6. Verificar dados de contato
    contact_validations = {
        'gdr_telefone_1': 'telefone',
        'gdr_whatsapp': 'whatsapp',
        'gdr_email_1': 'email',
        'gdr_website': 'website'
    }
    
    for field, tipo in contact_validations.items():
        if field in df.columns:
            invalid_count = 0
            for idx, value in df[field].items():
                if pd.notna(value) and str(value).strip():
                    if tipo == 'telefone' or tipo == 'whatsapp':
                        # Validação básica de telefone
                        if not re.match(r'^[\d\s\-\+\(\)]+$', str(value)):
                            invalid_count += 1
                    elif tipo == 'email':
                        # Validação básica de email
                        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)):
                            invalid_count += 1
                    elif tipo == 'website':
                        # Validação básica de URL
                        if not re.match(r'^https?://', str(value)):
                            invalid_count += 1
            
            if invalid_count > 0:
                report['inconsistencies']['warning'].append({
                    'type': f'invalid_{tipo}',
                    'field': field,
                    'count': invalid_count,
                    'message': f'{invalid_count} valores inválidos de {tipo}'
                })
    
    # 7. Estatísticas gerais
    report['statistics'] = {
        'total_critical': len(report['inconsistencies']['critical']),
        'total_warnings': len(report['inconsistencies']['warning']),
        'total_info': len(report['inconsistencies']['info']),
        'data_quality_score': calculate_data_quality_score(report),
        'completeness_score': calculate_completeness_score(df)
    }
    
    # 8. Recomendações baseadas nas inconsistências
    if report['statistics']['total_critical'] > 0:
        report['recommendations'].append(
            "URGENTE: Corrija os erros críticos antes de usar os dados para análise"
        )
    
    if any('empty_scraping_data' in inc['type'] for inc in report['inconsistencies']['warning']):
        report['recommendations'].append(
            "Configure e ative os scrapers (APIFY, GSE, CrawlAI) com as flags apropriadas"
        )
    
    if any('no_consensus' in inc['type'] for inc in report['inconsistencies']['warning']):
        report['recommendations'].append(
            "Configure múltiplos LLMs para obter análises de consenso mais confiáveis"
        )
    
    # 9. Salvar relatório se path fornecido
    if output_path:
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Relatório de inconsistências salvo em: {output_path}")
    
    # 10. Log resumido
    logger.warning(f"📊 RELATÓRIO DE INCONSISTÊNCIAS:")
    logger.warning(f"   • Erros críticos: {report['statistics']['total_critical']}")
    logger.warning(f"   • Avisos: {report['statistics']['total_warnings']}")
    logger.warning(f"   • Informações: {report['statistics']['total_info']}")
    logger.warning(f"   • Score de qualidade: {report['statistics']['data_quality_score']:.1f}%")
    
    return report


def calculate_data_quality_score(report: Dict) -> float:
    """Calcula score de qualidade dos dados baseado nas inconsistências"""
    base_score = 100.0
    
    # Penalidades
    base_score -= report['statistics']['total_critical'] * 10
    base_score -= report['statistics']['total_warnings'] * 3
    base_score -= report['statistics']['total_info'] * 0.5
    
    return max(0, min(100, base_score))


def calculate_completeness_score(df) -> float:
    """Calcula score de completude dos dados"""
    if len(df) == 0:
        return 0
    
    # Campos importantes para completude
    important_fields = [
        'gdr_nome', 'gdr_score_sinergia', 'gdr_telefone_1',
        'gdr_email_1', 'gdr_website', 'gdr_url_instagram',
        'gdr_url_facebook', 'gdr_analise_reviews'
    ]
    
    total_cells = 0
    filled_cells = 0
    
    for field in important_fields:
        if field in df.columns:
            total_cells += len(df)
            filled_cells += df[field].notna().sum()
    
    return (filled_cells / total_cells * 100) if total_cells > 0 else 0