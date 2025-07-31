# -*- coding: utf-8 -*-
"""
AURA NEXUS - Orquestrador Principal V2
Versão corrigida que processa 100% dos leads
"""

import asyncio
import pandas as pd
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import traceback

from ..infrastructure.cache_system import SmartMultiLevelCache
from ..infrastructure.checkpoint_manager import CheckpointManager
from .api_manager import APIManager
from .lead_processor import LeadProcessor
from .multi_llm_consensus import MultiLLMConsensusOrchestrator
from ..utils import setup_logging, format_time_elapsed, create_progress_bar


class AuraNexusOrchestrator:
    """
    Orquestrador principal corrigido do AURA NEXUS
    - Processa 100% dos leads
    - Executa TODAS as features configuradas
    - Métricas de sucesso funcionais
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializa o orquestrador"""
        self.config = config
        self.logger = setup_logging("AURA_NEXUS.Orchestrator")
        
        # Componentes principais
        self.api_manager = None
        self.lead_processor = None
        self.multi_llm = None
        self.cache = None
        self.checkpoint_manager = None
        
        # Estado e estatísticas
        self.is_initialized = False
        self.processing_stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'skipped_google': 0,
            'features_executed': {},
            'start_time': None,
            'end_time': None
        }
    
    async def initialize(self):
        """Inicializa todos os componentes do sistema"""
        if self.is_initialized:
            return
            
        try:
            self.logger.info("🚀 Inicializando componentes do AURA NEXUS...")
            
            # API Manager
            self.api_manager = APIManager()
            await self.api_manager.initialize()
            
            # Cache System
            if self.config.get('cache_enabled', True):
                self.cache = SmartMultiLevelCache(
                    cache_dir=self.config.get('cache_dir', Path('data/cache'))
                )
                await self.cache.initialize()
            
            # Lead Processor com configuração corrigida
            processor_config = self._get_processor_config()
            self.lead_processor = LeadProcessor(processor_config)
            await self.lead_processor.initialize()
            
            # Multi-LLM Consensus
            if 'ai_analysis' in processor_config['active_features']:
                llm_configs = self._get_llm_configs()
                if llm_configs:
                    self.multi_llm = MultiLLMConsensusOrchestrator(llm_configs)
                    await self.multi_llm.initialize()
            
            # Checkpoint Manager
            self.checkpoint_manager = CheckpointManager(
                self.config.get('checkpoint_dir', Path('data/checkpoints'))
            )
            
            self.is_initialized = True
            self.logger.info("✅ Sistema inicializado com sucesso!")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {str(e)}")
            raise
    
    def _get_processor_config(self) -> Dict[str, Any]:
        """Retorna configuração corrigida do processador"""
        mode = self.config.get('mode', 'basic')
        
        # Features ativas baseadas no modo
        active_features = self.config['feature_modes'].get(mode, [])
        
        config = {
            'api_manager': self.api_manager,
            'cache': self.cache,
            'active_features': active_features,
            'mode': mode,
            'force_process_all': self.config.get('force_process_all', False),
            'skip_google_only': self.config.get('skip_google_only', True),
            'dry_run': self.config.get('dry_run', False),
            'debug': self.config.get('debug', False)
        }
        
        self.logger.info(f"📋 Modo: {mode.upper()}")
        self.logger.info(f"📊 Features ativas ({len(active_features)}): {', '.join(active_features)}")
        
        return config
    
    def _get_llm_configs(self) -> Dict[str, Any]:
        """Retorna configurações dos LLMs disponíveis"""
        configs = {}
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            configs['openai'] = {
                'provider': 'openai',
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': 'gpt-4-turbo-preview',
                'temperature': 0.1,
                'max_tokens': 2048
            }
        
        # Anthropic
        if os.getenv('ANTHROPIC_API_KEY'):
            configs['anthropic'] = {
                'provider': 'anthropic',
                'api_key': os.getenv('ANTHROPIC_API_KEY'),
                'model': 'claude-3-opus-20240229',
                'temperature': 0.1,
                'max_tokens': 2048
            }
        
        # Google Gemini
        if os.getenv('GOOGLE_GEMINI_API_KEY'):
            configs['gemini'] = {
                'provider': 'gemini',
                'api_key': os.getenv('GOOGLE_GEMINI_API_KEY'),
                'model': 'gemini-pro',
                'temperature': 0.1,
                'max_tokens': 2048
            }
        
        return configs
    
    async def process_leads(self, leads_df: pd.DataFrame, checkpoint_enabled: bool = False) -> pd.DataFrame:
        """
        Processa DataFrame de leads - VERSÃO CORRIGIDA
        
        Args:
            leads_df: DataFrame com os leads
            checkpoint_enabled: Se deve usar checkpoints
            
        Returns:
            DataFrame com dados enriquecidos
        """
        self.processing_stats['start_time'] = datetime.now()
        self.processing_stats['total'] = len(leads_df)
        
        self.logger.info(f"📊 Iniciando processamento de {len(leads_df)} leads")
        
        # Adicionar ID único se não existir
        if 'gdr_id_processamento' not in leads_df.columns:
            leads_df['gdr_id_processamento'] = [f"LEAD_{i:04d}" for i in range(len(leads_df))]
        
        results = []
        batch_size = self.config.get('batch_size', 5)
        max_workers = self.config.get('max_workers', 3)
        
        # Processar em batches
        for batch_start in range(0, len(leads_df), batch_size):
            batch_end = min(batch_start + batch_size, len(leads_df))
            batch_df = leads_df.iloc[batch_start:batch_end]
            
            # Progress bar
            progress = create_progress_bar(batch_end, len(leads_df))
            self.logger.info(f"\n📦 Batch {batch_start//batch_size + 1}: {progress}")
            
            # Processar batch em paralelo
            batch_tasks = []
            for idx, row in batch_df.iterrows():
                lead_data = self._prepare_lead_data(row)
                
                # CORREÇÃO PRINCIPAL: Não pular leads, apenas marcar flag
                if row.get('gdr_ja_enriquecido_google', False):
                    lead_data['skip_google_api'] = True
                    self.processing_stats['skipped_google'] += 1
                    self.logger.info(f"⏭️ {lead_data['nome_empresa']} - Pulando apenas Google Maps API")
                
                # SEMPRE processar o lead
                task = self._process_single_lead(lead_data, idx)
                batch_tasks.append(task)
            
            # Aguardar conclusão com limite de workers
            if batch_tasks:
                # Limitar concorrência
                semaphore = asyncio.Semaphore(max_workers)
                
                async def process_with_limit(task):
                    async with semaphore:
                        return await task
                
                limited_tasks = [process_with_limit(task) for task in batch_tasks]
                batch_results = await asyncio.gather(*limited_tasks, return_exceptions=True)
                
                # Processar resultados
                for result in batch_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"❌ Erro: {str(result)}")
                        self.processing_stats['failed'] += 1
                        # Adicionar resultado de erro
                        results.append({
                            'gdr_status': 'erro',
                            'gdr_erro': str(result)
                        })
                    else:
                        results.append(result)
                        if result.get('gdr_status') == 'sucesso':
                            self.processing_stats['successful'] += 1
                        else:
                            self.processing_stats['failed'] += 1
                        
                        # Contar features executadas
                        for feature in result.get('gdr_features_executadas', []):
                            self.processing_stats['features_executed'][feature] = \
                                self.processing_stats['features_executed'].get(feature, 0) + 1
            
            # Checkpoint após cada batch
            if checkpoint_enabled and self.checkpoint_manager:
                await self._save_checkpoint(results, batch_end, len(leads_df))
        
        # Criar DataFrame final
        self.processing_stats['end_time'] = datetime.now()
        
        # Mesclar resultados com dados originais
        results_df = pd.DataFrame(results)
        final_df = self._merge_results(leads_df, results_df)
        
        # Log estatísticas finais
        self._log_final_statistics()
        
        return final_df
    
    def _prepare_lead_data(self, row: pd.Series) -> Dict[str, Any]:
        """Prepara dados do lead para processamento"""
        lead_data = row.to_dict()
        
        # Campos essenciais
        essential_fields = {
            'nome_empresa': row.get('nome_empresa', ''),
            'endereco': row.get('endereco', ''),
            'cidade': row.get('cidade', ''),
            'estado': row.get('estado', ''),
            'id_processamento': row.get('gdr_id_processamento', '')
        }
        
        lead_data.update(essential_fields)
        
        # Adicionar dados existentes se disponíveis
        if pd.notna(row.get('gdr_google_place_id')):
            lead_data['place_id'] = row['gdr_google_place_id']
        
        if pd.notna(row.get('gdr_latitude')) and pd.notna(row.get('gdr_longitude')):
            lead_data['coordinates'] = {
                'lat': row['gdr_latitude'],
                'lng': row['gdr_longitude']
            }
        
        return lead_data
    
    async def _process_single_lead(self, lead_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Processa um único lead com todas as features"""
        try:
            start_time = datetime.now()
            
            # Cache key
            cache_key = f"{lead_data['nome_empresa']}_{lead_data['cidade']}_{lead_data['estado']}"
            
            # Verificar cache (exceto se force_process_all)
            if self.cache and not self.config.get('force_process_all', False):
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    self.logger.info(f"📦 {lead_data['nome_empresa']} - Resultado do cache")
                    self.processing_stats['cached'] += 1
                    return cached_result
            
            # Processar lead
            self.logger.info(f"🔍 Processando: {lead_data['nome_empresa']}")
            
            result = await self.lead_processor.process_lead(lead_data)
            
            # Adicionar metadados
            process_time = (datetime.now() - start_time).total_seconds()
            result.update({
                'gdr_id_processamento': lead_data['id_processamento'],
                'gdr_data_processamento': datetime.now().isoformat(),
                'gdr_tempo_processamento': f"{process_time:.2f}s",
                'gdr_modo_analise': self.config.get('mode', 'basic'),
                'gdr_features_executadas': result.get('features_executed', [])
            })
            
            # Salvar no cache se sucesso
            if self.cache and result.get('gdr_status') == 'sucesso':
                await self.cache.set(cache_key, result, ttl=86400)  # 24 horas
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar {lead_data['nome_empresa']}: {str(e)}")
            if self.config.get('debug'):
                traceback.print_exc()
                
            return {
                'gdr_id_processamento': lead_data['id_processamento'],
                'gdr_nome': lead_data['nome_empresa'],
                'gdr_status': 'erro',
                'gdr_erro': str(e),
                'gdr_features_executadas': []
            }
    
    def _merge_results(self, original_df: pd.DataFrame, results_df: pd.DataFrame) -> pd.DataFrame:
        """Mescla resultados com dados originais preservando tudo"""
        # Garantir que temos a coluna de merge
        if 'gdr_id_processamento' not in results_df.columns:
            self.logger.warning("⚠️ Coluna gdr_id_processamento não encontrada nos resultados")
            return original_df
        
        # Fazer merge preservando TODOS os dados
        merged = pd.merge(
            original_df,
            results_df,
            on='gdr_id_processamento',
            how='left',
            suffixes=('', '_new')
        )
        
        # Atualizar colunas que vieram dos resultados
        for col in results_df.columns:
            if col != 'gdr_id_processamento' and col + '_new' in merged.columns:
                merged[col] = merged[col + '_new'].fillna(merged.get(col, pd.NA))
                merged.drop(col + '_new', axis=1, inplace=True)
        
        return merged
    
    async def _save_checkpoint(self, results: List[Dict], current: int, total: int):
        """Salva checkpoint do progresso"""
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'progress': f"{current}/{total}",
            'stats': self.processing_stats,
            'results': results
        }
        
        await self.checkpoint_manager.save_checkpoint(checkpoint_data)
        self.logger.info(f"💾 Checkpoint salvo: {current}/{total} leads")
    
    def _log_final_statistics(self):
        """Loga estatísticas finais do processamento"""
        stats = self.processing_stats
        
        # Calcular métricas
        total_time = (stats['end_time'] - stats['start_time']).total_seconds()
        success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
        avg_time = total_time / stats['total'] if stats['total'] > 0 else 0
        
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 ESTATÍSTICAS FINAIS DO PROCESSAMENTO")
        self.logger.info("="*60)
        self.logger.info(f"📋 Total de leads: {stats['total']}")
        self.logger.info(f"✅ Processados com sucesso: {stats['successful']} ({success_rate:.1f}%)")
        self.logger.info(f"❌ Falhas: {stats['failed']}")
        self.logger.info(f"📦 Do cache: {stats['cached']}")
        self.logger.info(f"⏭️ Google API pulada: {stats['skipped_google']}")
        self.logger.info(f"⏱️ Tempo total: {format_time_elapsed(total_time)}")
        self.logger.info(f"📍 Média por lead: {avg_time:.2f}s")
        
        if stats['features_executed']:
            self.logger.info("\n🔧 Features executadas:")
            for feature, count in sorted(stats['features_executed'].items()):
                self.logger.info(f"   • {feature}: {count} vezes")
        
        self.logger.info("="*60 + "\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do processamento"""
        stats = self.processing_stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            total_time = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['processing_time'] = total_time
            stats['avg_time_per_lead'] = total_time / stats['total'] if stats['total'] > 0 else 0
        
        stats['success_rate'] = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return stats