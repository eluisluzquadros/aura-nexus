# -*- coding: utf-8 -*-
"""
AURA NEXUS v25.0 - CÉLULA 11: ORQUESTRADOR PRINCIPAL V4
Versão melhorada com suporte completo para base-leads_amostra_v2.xlsx
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


import asyncio
import pandas as pd
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import traceback

# Imports das células
from aura_nexus_celula_00 import APIManager, MultiLLMConfig
from aura_nexus_celula_03 import MultiLLMConsensusOrchestrator, UniversalTokenCounter
from aura_nexus_celula_08 import SmartMultiLevelCache, PerformanceMonitor
from aura_nexus_celula_09 import RobustCheckpointManager, BatchExecutionController
from aura_nexus_celula_10_v2 import LeadProcessor, get_processor_config
from aura_nexus_spreadsheet_adapter import SpreadsheetAdapter

# Tentar importar a busca do Maps (pode não existir ainda)
try:
    from aura_nexus_celula_12 import GoogleMapsDirectSearch
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False
    
# ===================================================================================
# CLASSE: AuraNexusOrchestratorV4
# ===================================================================================

class AuraNexusOrchestratorV4:
    """
    Orquestrador principal v4 com suporte completo para diferentes formatos de planilha
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o orquestrador
        
        Args:
            config: Configuração completa do sistema
        """
        self.config = config
        self.logger = self._setup_logger()
        
        # Componentes principais
        self.api_manager = None
        self.multi_llm = None
        self.lead_processor = None
        self.cache = None
        self.checkpoint_manager = None
        self.performance_monitor = None
        self.spreadsheet_adapter = SpreadsheetAdapter()
        
        # Estado
        self.is_initialized = False
        self.processing_stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Configura logger personalizado"""
        logger = logging.getLogger("AURA_NEXUS.OrchestratorV4")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
        return logger
    
    async def initialize(self):
        """Inicializa todos os componentes do sistema"""
        if self.is_initialized:
            return
            
        self.logger.info("🚀 Inicializando AURA NEXUS v25.0...")
        
        try:
            # 1. API Manager
            self.api_manager = APIManager()
            
            # 1.1 Criar MultiLLMConfig para obter APIs ativas
            multi_llm_config = MultiLLMConfig(self.api_manager)
            available_apis = multi_llm_config.get_active_llms()
            self.logger.info(f"✅ APIs disponíveis: {', '.join(available_apis)}")
            
            # 2. Multi-LLM Orchestrator
            llm_configs = self._create_llm_configs()
            if llm_configs:
                # Create token counter for Multi-LLM orchestrator
                token_counter = UniversalTokenCounter()
                self.multi_llm = MultiLLMConsensusOrchestrator(llm_configs, token_counter, enable_review=True)
                self.logger.info(f"✅ LLMs configurados: {', '.join(llm_configs.keys())}")
            else:
                self.logger.warning("⚠️ Nenhum LLM configurado - modo básico ativado")
            
            # 3. Cache
            if self.config.get('enable_cache', True):
                cache_config = {
                    'ttl': self.config.get('cache_ttl', 604800),  # 7 dias
                    'enable_disk': True,
                    'enable_drive': self.config.get('enable_drive_cache', False)
                }
                self.cache = SmartMultiLevelCache(config=cache_config)
                self.logger.info("✅ Sistema de cache inicializado")
            
            # 4. Checkpoint Manager
            if self.config.get('enable_checkpoint', True):
                checkpoint_dir = self.config.get('checkpoint_dir', './checkpoints')
                checkpoint_file = os.path.join(checkpoint_dir, 'aura_nexus_checkpoint.csv')
                os.makedirs(checkpoint_dir, exist_ok=True)
                
                self.checkpoint_manager = RobustCheckpointManager(
                    checkpoint_path=checkpoint_file
                )
                self.logger.info("✅ Sistema de checkpoint inicializado")
            
            # 5. Performance Monitor
            if self.config.get('performance_monitoring', True):
                self.performance_monitor = PerformanceMonitor()
                self.logger.info("✅ Monitor de performance inicializado")
            
            # 6. Lead Processor
            processor_config = get_processor_config(
                mode=self.config.get('ANALYSIS_MODE', 'basic')
            )
            
            # Sobrescrever configurações específicas
            processor_config['enable_scraping'] = self.config.get('enable_scraping', True)
            processor_config['enable_facade_analysis'] = self.config.get('enable_facade_analysis', False)
            processor_config['enable_ai_analysis'] = self.config.get('enable_ai_analysis', True)
            
            # Adicionar referências necessárias ao config
            processor_config['api_manager'] = self.api_manager
            processor_config['multi_llm_orchestrator'] = self.multi_llm
            
            self.lead_processor = LeadProcessor(config=processor_config)
            self.logger.info(f"✅ Processador de leads inicializado (modo: {processor_config['ANALYSIS_MODE']})")
            
            self.is_initialized = True
            self.logger.info("✅ Sistema inicializado com sucesso!")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {str(e)}")
            raise
    
    def _create_llm_configs(self) -> Dict[str, Any]:
        """Cria configurações para os LLMs disponíveis"""
        configs = {}
        
        # Gemini
        if os.getenv('GEMINI_API_KEY'):
            configs['gemini'] = {
                'provider': 'gemini',
                'api_key': os.getenv('GEMINI_API_KEY'),
                'model': 'gemini-1.5-flash',
                'temperature': 0.1,
                'max_tokens': 2048
            }
        
        # Claude
        if os.getenv('CLAUDE_API_KEY'):
            configs['claude'] = {
                'provider': 'claude',
                'api_key': os.getenv('CLAUDE_API_KEY'),
                'model': 'claude-3-sonnet-20240229',
                'temperature': 0.1,
                'max_tokens': 2048
            }
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            configs['openai'] = {
                'provider': 'openai',
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': 'gpt-4-turbo-preview',
                'temperature': 0.1,
                'max_tokens': 2048
            }
        
        # DeepSeek
        if os.getenv('DEEPSEEK_API_KEY'):
            configs['deepseek'] = {
                'provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY'),
                'model': 'deepseek-chat',
                'temperature': 0.1,
                'max_tokens': 2048
            }
        
        return configs
    
    async def process_spreadsheet_with_adapter(self, file_path: str, num_leads: Optional[int] = None) -> pd.DataFrame:
        """
        Processa planilha usando o adaptador para preservar dados
        
        Args:
            file_path: Caminho para o arquivo Excel
            num_leads: Número máximo de leads para processar
            
        Returns:
            DataFrame com dados originais + enriquecidos
        """
        self.logger.info(f"📊 Processando planilha: {file_path}")
        
        # 1. Adaptar planilha para formato padrão
        adapted_df = self.spreadsheet_adapter.adapt_spreadsheet(file_path)
        self.logger.info(f"✅ Planilha adaptada: {len(adapted_df)} leads")
        
        # 2. Limitar número de leads se especificado
        if num_leads and num_leads < len(adapted_df):
            adapted_df = adapted_df.head(num_leads)
            self.logger.info(f"📌 Limitado a {num_leads} leads")
        
        # 3. Adicionar ID de processamento único
        adapted_df['gdr_id_processamento'] = [f"LEAD_{i:04d}" for i in range(len(adapted_df))]
        
        # 4. Processar cada lead
        results = []
        batch_size = self.config.get('batch_size', 5)
        
        # Processar em batches
        for batch_start in range(0, len(adapted_df), batch_size):
            batch_end = min(batch_start + batch_size, len(adapted_df))
            batch_df = adapted_df.iloc[batch_start:batch_end]
            
            self.logger.info(f"\n📦 Processando batch {batch_start//batch_size + 1} ({batch_start+1}-{batch_end}/{len(adapted_df)})")
            
            # Processar batch em paralelo
            batch_tasks = []
            for idx, row in batch_df.iterrows():
                # Preparar dados do lead
                lead_data = self._prepare_lead_data(row)
                
                # Verificar se precisa enriquecer
                if row.get('gdr_ja_enriquecido_google', False) and self.config.get('skip_already_enriched', True):
                    self.logger.info(f"⏭️ Lead {lead_data['nome_empresa']} já possui dados do Google")
                    # Apenas formatar dados existentes
                    enriched = self._format_existing_data(row)
                    results.append(enriched)
                else:
                    # Enriquecer lead
                    task = self._process_single_lead(lead_data, idx)
                    batch_tasks.append(task)
            
            # Aguardar conclusão do batch
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"❌ Erro no processamento: {str(result)}")
                        self.processing_stats['failed'] += 1
                    else:
                        results.append(result)
                        if result.get('gdr_status') == 'concluído':
                            self.processing_stats['successful'] += 1
                        else:
                            self.processing_stats['failed'] += 1
            
            # Checkpoint após cada batch
            if self.checkpoint_manager and results:
                await self._save_checkpoint(results)
        
        # 5. Criar DataFrame com resultados enriquecidos
        enriched_df = pd.DataFrame(results)
        
        # 6. Mesclar com dados originais para preservar TUDO
        final_df = self.spreadsheet_adapter.merge_enriched_data(adapted_df, enriched_df)
        
        self.logger.info(f"\n✅ Processamento concluído: {len(final_df)} leads")
        self.logger.info(f"   • Colunas originais preservadas: {sum(1 for col in final_df.columns if col.startswith('original_'))}")
        self.logger.info(f"   • Novas colunas adicionadas: {sum(1 for col in final_df.columns if col.startswith('gdr_') and not col.endswith('_original'))}")
        
        return final_df
    
    def _prepare_lead_data(self, row: pd.Series) -> Dict[str, Any]:
        """Prepara dados do lead para processamento"""
        lead_data = {
            'nome_empresa': row.get('nome_empresa', ''),
            'endereco': row.get('endereco', ''),
            'cidade': row.get('cidade', ''),
            'estado': row.get('estado', ''),
            'id_processamento': row.get('gdr_id_processamento', '')
        }
        
        # Adicionar dados existentes se disponíveis
        if pd.notna(row.get('gdr_google_place_id')):
            lead_data['place_id'] = row['gdr_google_place_id']
        
        if pd.notna(row.get('gdr_latitude')) and pd.notna(row.get('gdr_longitude')):
            lead_data['coordinates'] = {
                'lat': row['gdr_latitude'],
                'lng': row['gdr_longitude']
            }
        
        # Adicionar outros dados relevantes
        for key in ['gdr_telefone_consolidado', 'gdr_website_consolidado', 'gdr_cnpj_cpf']:
            if key in row and pd.notna(row[key]):
                lead_data[key] = row[key]
        
        return lead_data
    
    def _format_existing_data(self, row: pd.Series) -> Dict[str, Any]:
        """Formata dados existentes do Google Places"""
        formatted = {
            'gdr_id_processamento': row.get('gdr_id_processamento'),
            'gdr_nome': row.get('nome_empresa'),
            'gdr_status': 'já_enriquecido',
            'gdr_data_processamento': datetime.now().isoformat(),
            'gdr_fonte_enriquecimento': 'google_places_existente'
        }
        
        # Copiar todos os campos gdr_ existentes
        for col in row.index:
            if col.startswith('gdr_') and pd.notna(row[col]):
                formatted[col] = row[col]
        
        return formatted
    
    async def _process_single_lead(self, lead_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Processa um único lead"""
        try:
            # Verificar cache
            cache_key = f"{lead_data['nome_empresa']}_{lead_data['cidade']}_{lead_data['estado']}"
            
            if self.cache:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    self.logger.info(f"📦 {lead_data['nome_empresa']} - Usando cache")
                    self.processing_stats['cached'] += 1
                    return cached_result
            
            # Processar lead
            self.logger.info(f"🔍 Processando: {lead_data['nome_empresa']}")
            
            timer_id = None
            if self.performance_monitor:
                timer_id = self.performance_monitor.start_timer(
                    'lead_processing',
                    {'lead': lead_data['nome_empresa']}
                )
            
            result = await self.lead_processor.process_lead(lead_data)
            
            if self.performance_monitor and timer_id:
                self.performance_monitor.stop_timer(timer_id)
            
            # Adicionar metadados
            result['gdr_id_processamento'] = lead_data['id_processamento']
            result['gdr_data_processamento'] = datetime.now().isoformat()
            result['gdr_modo_analise'] = self.config.get('ANALYSIS_MODE', 'basic')
            
            # Salvar no cache
            if self.cache and result.get('gdr_status') == 'concluído':
                await self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar {lead_data['nome_empresa']}: {str(e)}")
            return {
                'gdr_id_processamento': lead_data['id_processamento'],
                'gdr_nome': lead_data['nome_empresa'],
                'gdr_status': 'erro',
                'gdr_erro': str(e)
            }
    
    async def _save_checkpoint(self, results: List[Dict]):
        """Salva checkpoint do progresso"""
        if self.checkpoint_manager:
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(results),
                'successful': sum(1 for r in results if r.get('gdr_status') == 'concluído'),
                'results': results
            }
            
            # Convert checkpoint data to DataFrame for RobustCheckpointManager
            checkpoint_df = pd.DataFrame(results)
            await asyncio.to_thread(
                self.checkpoint_manager.save_incremental,
                checkpoint_df,
                metadata=checkpoint_data
            )
    
    async def process_leads(self, 
                          input_data: Union[str, Dict[str, Any]], 
                          num_leads: Optional[int] = None) -> Dict[str, Any]:
        """
        Processa leads de acordo com o modo configurado
        
        Args:
            input_data: Caminho do arquivo (spreadsheet) ou parâmetros de busca (maps)
            num_leads: Número máximo de leads para processar
            
        Returns:
            Dict com resultados do processamento
        """
        try:
            # Inicializar se necessário
            if not self.is_initialized:
                await self.initialize()
            
            # Registrar início
            self.processing_stats['start_time'] = datetime.now()
            
            # Determinar modo de entrada
            input_mode = self.config.get('INPUT_MODE', 'spreadsheet')
            
            if input_mode == 'spreadsheet':
                # Processar planilha
                if not isinstance(input_data, str):
                    raise ValueError("Modo spreadsheet requer caminho do arquivo")
                
                df_results = await self.process_spreadsheet_with_adapter(input_data, num_leads)
                
            elif input_mode == 'maps':
                # Buscar no Maps (se disponível)
                if not MAPS_AVAILABLE:
                    raise NotImplementedError("Modo Maps ainda não implementado")
                
                df_results = await self.process_maps_search(input_data, num_leads)
                
            else:
                raise ValueError(f"Modo de entrada inválido: {input_mode}")
            
            # Salvar resultados
            output_file = await self._save_results(df_results)
            
            # Registrar fim
            self.processing_stats['end_time'] = datetime.now()
            self.processing_stats['total'] = len(df_results)
            
            # Gerar relatório de performance
            if self.performance_monitor:
                performance_report = self.performance_monitor.get_detailed_report()
                self.logger.info(f"\n📊 Relatório de Performance:\n{json.dumps(performance_report, indent=2)}")
            
            return {
                'success': True,
                'total_processed': len(df_results),
                'successful': self.processing_stats['successful'],
                'failed': self.processing_stats['failed'],
                'cached': self.processing_stats['cached'],
                'output_file': output_file,
                'dataframe': df_results,
                'elapsed_time': (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro no processamento: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'total_processed': self.processing_stats['total'],
                'successful': self.processing_stats['successful'],
                'failed': self.processing_stats['failed']
            }
    
    async def _save_results(self, df_results: pd.DataFrame) -> str:
        """Salva resultados em Excel formatado"""
        try:
            # Determinar diretório de saída
            output_dir = self.config.get('output_dir', '.')
            os.makedirs(output_dir, exist_ok=True)
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"aura_nexus_results_{timestamp}.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            # Salvar com formatação
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Aba principal com resultados
                df_results.to_excel(writer, sheet_name='Resultados', index=False)
                
                # Aba com estatísticas
                stats_df = pd.DataFrame([{
                    'Total Processado': self.processing_stats['total'],
                    'Sucesso': self.processing_stats['successful'],
                    'Falhas': self.processing_stats['failed'],
                    'Do Cache': self.processing_stats['cached'],
                    'Tempo Total (s)': (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds() if self.processing_stats['end_time'] else 0,
                    'Modo de Análise': self.config.get('ANALYSIS_MODE', 'basic'),
                    'Data Processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }])
                stats_df.to_excel(writer, sheet_name='Estatísticas', index=False)
                
                # Ajustar largura das colunas
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            self.logger.info(f"✅ Resultados salvos em: {filepath}")
            
            # Gerar relatório de inconsistências
            try:
                from aura_nexus_celula_19_data_review import generate_inconsistency_report
                
                # Gerar relatório
                report_path = filepath.replace('.xlsx', '_inconsistencies.json')
                inconsistency_report = generate_inconsistency_report(df_results, report_path)
                
                # Log resumido
                self.logger.warning(f"📊 RELATÓRIO DE INCONSISTÊNCIAS GERADO:")
                self.logger.warning(f"   • Erros críticos: {inconsistency_report['statistics']['total_critical']}")
                self.logger.warning(f"   • Avisos: {inconsistency_report['statistics']['total_warnings']}")
                self.logger.warning(f"   • Score de qualidade: {inconsistency_report['statistics']['data_quality_score']:.1f}%")
                self.logger.info(f"   • Relatório salvo em: {report_path}")
                
                # Se houver erros críticos, avisar o usuário
                if inconsistency_report['statistics']['total_critical'] > 0:
                    self.logger.error("⚠️ ATENÇÃO: Foram encontrados erros críticos nos dados!")
                    self.logger.error("   Verifique o relatório de inconsistências antes de usar os dados.")
                    
            except Exception as e:
                self.logger.error(f"❌ Erro ao gerar relatório de inconsistências: {str(e)}")
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar resultados: {str(e)}")
            # Fallback para CSV
            csv_path = filepath.replace('.xlsx', '.csv')
            df_results.to_csv(csv_path, index=False)
            self.logger.info(f"✅ Resultados salvos em CSV: {csv_path}")
            return csv_path

# ===================================================================================
# FUNÇÕES AUXILIARES
# ===================================================================================

def create_orchestrator_config_v4(
    input_mode: str = 'spreadsheet',
    analysis_mode: str = 'basic',
    batch_size: int = 5,
    num_leads: Optional[int] = None,
    enable_cache: bool = True,
    enable_checkpoint: bool = True,
    skip_already_enriched: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Cria configuração para o orquestrador v4
    
    Args:
        input_mode: 'spreadsheet' ou 'maps'
        analysis_mode: 'basic' ou 'full_strategy'
        batch_size: Tamanho do batch para processamento
        num_leads: Número máximo de leads
        enable_cache: Habilitar cache
        enable_checkpoint: Habilitar checkpoints
        skip_already_enriched: Pular leads já enriquecidos com Google Places
        **kwargs: Configurações adicionais
        
    Returns:
        Dict com configuração completa
    """
    config = {
        # Modos principais
        'INPUT_MODE': input_mode,
        'ANALYSIS_MODE': analysis_mode,
        
        # Performance
        'batch_size': batch_size,
        'num_leads': num_leads,
        'max_concurrent_tasks': kwargs.get('max_concurrent_tasks', 3),
        'timeout_per_lead': kwargs.get('timeout_per_lead', 60),
        
        # Features
        'enable_cache': enable_cache,
        'cache_ttl': kwargs.get('cache_ttl', 604800),  # 7 dias
        'enable_checkpoint': enable_checkpoint,
        'enable_drive_cache': kwargs.get('enable_drive_cache', False),
        'performance_monitoring': kwargs.get('performance_monitoring', True),
        
        # Processamento
        'skip_already_enriched': skip_already_enriched,
        'enable_scraping': kwargs.get('enable_scraping', True),
        'enable_facade_analysis': kwargs.get('enable_facade_analysis', analysis_mode == 'full_strategy'),
        'enable_ai_analysis': kwargs.get('enable_ai_analysis', analysis_mode == 'full_strategy'),
        
        # Diretórios
        'output_dir': kwargs.get('output_dir', os.getenv('OUTPUT_DIR', './output')),
        'cache_dir': kwargs.get('cache_dir', './cache'),
        'checkpoint_dir': kwargs.get('checkpoint_dir', './checkpoints'),
        
        # Configurações adicionais
        **kwargs
    }
    
    return config