import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import time
import traceback
import pandas as pd
import gc
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ===================================================================================
# CÉLULA 9: CHECKPOINT E BATCH MANAGER
# ===================================================================================

# Logger
logger = logging.getLogger("AURA_NEXUS.CheckpointBatch")

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle pandas Timestamp and datetime objects"""
    def default(self, obj):
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            # Handle pandas Series or other objects with to_dict method
            return obj.to_dict()
        elif hasattr(obj, 'tolist'):
            # Handle numpy arrays
            return obj.tolist()
        return super().default(obj)

class RobustCheckpointManager:
    """Sistema robusto de checkpoint com recuperação de falhas"""
    
    def __init__(self, checkpoint_path: str, backup_dir: Optional[str] = None):
        self.checkpoint_path = checkpoint_path
        self.backup_dir = backup_dir or os.path.join(
            os.path.dirname(checkpoint_path), 
            'backups'
        )
        
        # Configurações
        self.version_history = []
        self.max_backups = 5
        self.compression_enabled = True
        
        # Criar diretórios
        self.ensure_directories()
        
        # Carregar histórico
        self._load_version_history()
    
    def ensure_directories(self):
        """Garante que diretórios existam"""
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def save_incremental(self, new_results: pd.DataFrame, 
                        metadata: Optional[Dict] = None) -> pd.DataFrame:
        """Salva resultados incrementalmente sem perder dados anteriores"""
        try:
            # Carregar checkpoint existente
            existing_df = self.load_checkpoint()
            
            # Adicionar metadados
            if metadata:
                new_results['_metadata'] = json.dumps(metadata, cls=DateTimeEncoder)
            
            # Adicionar timestamp (como string ISO para evitar problemas de serialização)
            new_results['_checkpoint_time'] = pd.Timestamp.now().isoformat()
            
            # Combinar dados
            if not existing_df.empty and not new_results.empty:
                # Identificar coluna chave
                key_column = self._identify_key_column(new_results)
                
                if key_column and key_column in existing_df.columns:
                    # Merge inteligente
                    combined_df = self._smart_merge(existing_df, new_results, key_column)
                else:
                    # Concatenar simples
                    combined_df = pd.concat([existing_df, new_results], ignore_index=True)
            else:
                combined_df = new_results if not new_results.empty else existing_df
            
            # Criar backup antes de salvar
            if not existing_df.empty:
                self._create_backup(existing_df)
            
            # Salvar checkpoint
            self._save_dataframe(combined_df, self.checkpoint_path)
            
            # Registrar no histórico
            self._add_to_history(len(combined_df), len(new_results))
            
            logger.info(
                f"✅ Checkpoint salvo: {len(combined_df)} registros totais "
                f"({len(new_results)} novos)"
            )
            
            return combined_df
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar checkpoint incremental: {e}")
            
            # Tentar salvar em emergência
            try:
                emergency_path = self._get_emergency_backup_path()
                self._save_dataframe(new_results, emergency_path)
                logger.warning(f"⚠️ Dados salvos em backup de emergência: {emergency_path}")
            except:
                pass
            
            raise
    
    def load_checkpoint(self) -> pd.DataFrame:
        """Carrega checkpoint com recuperação de falhas"""
        try:
            if os.path.exists(self.checkpoint_path):
                df = self._load_dataframe(self.checkpoint_path)
                
                # Limpar colunas temporárias
                temp_columns = ['_checkpoint_time', '_metadata']
                for col in temp_columns:
                    if col in df.columns:
                        df = df.drop(col, axis=1)
                
                logger.info(f"✅ Checkpoint carregado: {len(df)} registros")
                return df
            else:
                logger.info("ℹ️ Nenhum checkpoint encontrado")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar checkpoint: {e}")
            return self._recover_from_backup()
    
    def _identify_key_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identifica coluna chave para merge"""
        potential_keys = ['id_ld', 'place_id', 'id', 'gdr_nome', 'name']
        
        for key in potential_keys:
            if key in df.columns:
                # Verificar se é única
                if df[key].nunique() == len(df):
                    return key
        
        return None
    
    def _smart_merge(self, df1: pd.DataFrame, df2: pd.DataFrame, key_column: str) -> pd.DataFrame:
        """Merge inteligente preservando dados mais recentes"""
        # Adicionar indicador de origem
        df1['_source'] = 'existing'
        df2['_source'] = 'new'
        
        # Concatenar
        combined = pd.concat([df1, df2], ignore_index=True)
        
        # Ordenar por tempo (novos primeiro)
        if '_checkpoint_time' in combined.columns:
            combined = combined.sort_values('_checkpoint_time', ascending=False)
        else:
            # Novos registros primeiro
            combined = combined.sort_values('_source', ascending=True)
        
        # Remover duplicatas mantendo mais recente
        combined = combined.drop_duplicates(subset=[key_column], keep='first')
        
        # Limpar colunas auxiliares
        combined = combined.drop('_source', axis=1)
        
        return combined
    
    def _create_backup(self, df: pd.DataFrame):
        """Cria backup com rotação automática"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"checkpoint_backup_{timestamp}.csv"
            
            if self.compression_enabled:
                backup_name += '.gz'
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Salvar backup
            self._save_dataframe(df, backup_path)
            
            # Adicionar ao histórico
            self.version_history.append({
                'path': backup_path,
                'timestamp': timestamp,
                'records': len(df),
                'size': os.path.getsize(backup_path)
            })
            
            # Rotação de backups
            self._rotate_backups()
            
            logger.debug(f"📦 Backup criado: {backup_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Falha ao criar backup: {e}")
    
    def _rotate_backups(self):
        """Remove backups antigos mantendo apenas os mais recentes"""
        if len(self.version_history) > self.max_backups:
            # Ordenar por timestamp
            self.version_history.sort(key=lambda x: x['timestamp'])
            
            # Remover mais antigos
            while len(self.version_history) > self.max_backups:
                old_backup = self.version_history.pop(0)
                try:
                    os.remove(old_backup['path'])
                    logger.debug(f"🗑️ Backup antigo removido: {old_backup['path']}")
                except:
                    pass
    
    def _recover_from_backup(self) -> pd.DataFrame:
        """Tenta recuperar dados do backup mais recente"""
        try:
            # Listar backups disponíveis
            backup_files = [
                f for f in os.listdir(self.backup_dir)
                if f.startswith('checkpoint_backup_') and (f.endswith('.csv') or f.endswith('.csv.gz'))
            ]
            
            if not backup_files:
                logger.error("❌ Nenhum backup encontrado")
                return pd.DataFrame()
            
            # Ordenar por data (mais recente primeiro)
            backup_files.sort(reverse=True)
            
            # Tentar carregar backups
            for backup_file in backup_files[:3]:
                try:
                    backup_path = os.path.join(self.backup_dir, backup_file)
                    df = self._load_dataframe(backup_path)
                    logger.warning(f"⚠️ Dados recuperados do backup: {backup_file}")
                    return df
                except Exception as e:
                    logger.debug(f"Falha ao carregar backup {backup_file}: {e}")
                    continue
            
            logger.error("❌ Não foi possível recuperar dados de nenhum backup")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar backup: {e}")
            return pd.DataFrame()
    
    def _save_dataframe(self, df: pd.DataFrame, path: str):
        """Salva DataFrame com compressão opcional"""
        if path.endswith('.gz'):
            df.to_csv(path, index=False, encoding='utf-8-sig', compression='gzip')
        else:
            df.to_csv(path, index=False, encoding='utf-8-sig')
    
    def _load_dataframe(self, path: str) -> pd.DataFrame:
        """Carrega DataFrame com detecção automática de compressão"""
        if path.endswith('.gz'):
            return pd.read_csv(path, encoding='utf-8-sig', compression='gzip')
        else:
            return pd.read_csv(path, encoding='utf-8-sig')
    
    def _get_emergency_backup_path(self) -> str:
        """Gera caminho para backup de emergência"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return os.path.join(self.backup_dir, f"emergency_backup_{timestamp}.csv")
    
    def _load_version_history(self):
        """Carrega histórico de versões"""
        history_file = os.path.join(self.backup_dir, 'version_history.json')
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.version_history = json.load(f)
        except:
            self.version_history = []
    
    def _add_to_history(self, total_records: int, new_records: int):
        """Adiciona entrada ao histórico"""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'total_records': total_records,
            'new_records': new_records,
            'checkpoint_path': self.checkpoint_path
        }
        
        # Salvar histórico
        history_file = os.path.join(self.backup_dir, 'version_history.json')
        
        try:
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            history.append(history_entry)
            
            # Manter apenas últimas 100 entradas
            history = history[-100:]
            
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2, cls=DateTimeEncoder)
        except:
            pass
    
    def get_checkpoint_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o checkpoint atual"""
        info = {
            'exists': os.path.exists(self.checkpoint_path),
            'path': self.checkpoint_path,
            'backup_dir': self.backup_dir,
            'backups_available': 0,
            'total_backup_size': 0,
            'last_modified': None,
            'records': 0
        }
        
        if info['exists']:
            try:
                stat = os.stat(self.checkpoint_path)
                info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                info['size'] = self._format_size(stat.st_size)
                
                # Contar registros
                df = self.load_checkpoint()
                info['records'] = len(df)
            except:
                pass
        
        # Informações de backups
        try:
            backup_files = [
                f for f in os.listdir(self.backup_dir)
                if f.startswith('checkpoint_backup_')
            ]
            info['backups_available'] = len(backup_files)
            
            total_size = sum(
                os.path.getsize(os.path.join(self.backup_dir, f))
                for f in backup_files
            )
            info['total_backup_size'] = self._format_size(total_size)
        except:
            pass
        
        return info
    
    def _format_size(self, size: int) -> str:
        """Formata tamanho de arquivo"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def merge_checkpoint_with_results(self, final_results: pd.DataFrame) -> pd.DataFrame:
        """Merge final entre checkpoint e resultados"""
        checkpoint_df = self.load_checkpoint()
        
        if checkpoint_df.empty:
            return final_results
        
        if final_results.empty:
            return checkpoint_df
        
        # Identificar coluna chave
        key_column = self._identify_key_column(final_results)
        
        if key_column:
            return self._smart_merge(checkpoint_df, final_results, key_column)
        else:
            # Concatenar sem duplicação
            return pd.concat([checkpoint_df, final_results], ignore_index=True)


class BatchExecutionController:
    """Controlador avançado de execução em batches"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configurações padrão
        self.config.setdefault('batch_size', 5)
        self.config.setdefault('pause_between_batches', 10)
        self.config.setdefault('auto_save_every', 3)
        self.config.setdefault('memory_threshold', 0.8)
        self.config.setdefault('force_gc_every', 10)
        self.config.setdefault('max_retries_per_lead', 3)
        self.config.setdefault('retry_delay', 5)
        self.config.setdefault('adaptive_batch_size', True)
        self.config.setdefault('min_batch_size', 1)
        self.config.setdefault('max_batch_size', 20)
        
        # Estado
        self.processed_count = 0
        self.failed_leads = []
        self.memory_usage_history = []
        self.execution_times = []
        self.last_gc_at = 0
        self.current_batch_size = self.config['batch_size']
        
        # Callbacks
        self.on_lead_complete = None
        self.on_batch_complete = None
        self.on_memory_warning = None
        self.on_checkpoint_save = None
        self.on_error = None
    
    async def execute_batch_with_control(self, 
                                       leads: List[Dict[str, Any]], 
                                       process_function: callable,
                                       checkpoint_manager: Optional[Any] = None,
                                       performance_monitor: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Executa processamento em lotes com controle avançado"""
        total_leads = len(leads)
        results = []
        
        # Banner inicial
        self._print_execution_banner(total_leads)
        
        # Timer global
        global_timer = performance_monitor.start_timer('batch_execution') if performance_monitor else None
        
        # Processar em batches
        batch_num = 0
        i = 0
        
        while i < total_leads:
            # Ajustar tamanho do batch dinamicamente
            if self.config['adaptive_batch_size']:
                self._adjust_batch_size()
            
            # Determinar tamanho do batch atual
            batch_end = min(i + self.current_batch_size, total_leads)
            batch = leads[i:batch_end]
            batch_size = len(batch)
            
            # Exibir progresso
            self._print_batch_header(batch_num + 1, i + 1, batch_end, total_leads)
            
            # Verificar memória
            if not self._check_memory_before_batch():
                logger.warning("⚠️ Memória insuficiente, executando limpeza...")
                await self._emergency_cleanup()
            
            # Timer do batch
            batch_timer = performance_monitor.start_timer('batch_processing') if performance_monitor else None
            batch_start_time = time.time()
            
            # Processar batch
            try:
                batch_results = await self._process_batch_internal(
                    batch, process_function, batch_num, performance_monitor
                )
                
                batch_time = time.time() - batch_start_time
                
                if batch_timer and performance_monitor:
                    performance_monitor.stop_timer(batch_timer)
                
                # Adicionar resultados
                results.extend(batch_results)
                
                # Estatísticas do batch
                successful = len([r for r in batch_results if r is not None])
                self._print_batch_summary(batch_num + 1, successful, batch_size, batch_time)
                
                # Callback
                if self.on_batch_complete:
                    self.on_batch_complete(batch_num + 1, batch_results)
                
                # Auto-save
                if checkpoint_manager and len(results) % self.config['auto_save_every'] == 0:
                    await self._save_checkpoint(results, checkpoint_manager)
                
                # Garbage collection forçado
                if self.processed_count - self.last_gc_at >= self.config['force_gc_every']:
                    await self._force_garbage_collection()
                
                # Pausa entre batches
                if batch_end < total_leads:
                    await self._pause_between_batches()
                
            except Exception as e:
                logger.error(f"❌ Erro crítico no batch {batch_num + 1}: {e}")
                if self.on_error:
                    self.on_error(e, batch_num + 1)
                
                # Tentar salvar progresso
                if checkpoint_manager and results:
                    try:
                        await self._save_checkpoint(results, checkpoint_manager)
                    except:
                        pass
            
            # Avançar
            i = batch_end
            batch_num += 1
        
        # Finalizar timer global
        if global_timer and performance_monitor:
            performance_monitor.stop_timer(global_timer)
        
        # Estatísticas finais
        self._print_final_statistics(results, total_leads)
        
        # Tentar reprocessar falhas
        if self.failed_leads:
            retry_results = await self._retry_failed_leads(process_function, performance_monitor)
            results.extend(retry_results)
        
        return results
    
    def _print_execution_banner(self, total_leads: int):
        """Exibe banner de execução"""
        print(f"\n{'='*70}")
        print(f"🚀 INICIANDO PROCESSAMENTO CONTROLADO")
        print(f"{'='*70}")
        print(f"📊 Total de leads: {total_leads}")
        print(f"📦 Tamanho do batch: {self.config['batch_size']}")
        print(f"⏱️ Pausa entre batches: {self.config['pause_between_batches']}s")
        print(f"💾 Auto-save a cada: {self.config['auto_save_every']} leads")
        print(f"🔄 Batch adaptativo: {'Sim' if self.config['adaptive_batch_size'] else 'Não'}")
        print(f"{'='*70}\n")
    
    def _print_batch_header(self, batch_num: int, start: int, end: int, total: int):
        """Exibe cabeçalho do batch"""
        progress = (start - 1) / total * 100
        print(f"\n{'─'*50}")
        print(f"📦 BATCH {batch_num} | Leads {start}-{end} de {total} ({progress:.1f}%)")
        print(f"{'─'*50}")
    
    def _print_batch_summary(self, batch_num: int, successful: int, total: int, time_taken: float):
        """Exibe resumo do batch"""
        success_rate = (successful / total * 100) if total > 0 else 0
        avg_time = time_taken / total if total > 0 else 0
        
        print(f"\n✅ Batch {batch_num} concluído:")
        print(f"   • Sucesso: {successful}/{total} ({success_rate:.1f}%)")
        print(f"   • Tempo total: {time_taken:.1f}s")
        print(f"   • Tempo médio: {avg_time:.1f}s/lead")
        print(f"   • Memória: {self._get_memory_usage():.1f}%")
    
    async def _process_batch_internal(self, 
                                    batch: List[Dict[str, Any]], 
                                    process_function: callable,
                                    batch_num: int,
                                    performance_monitor: Optional[Any]) -> List[Dict[str, Any]]:
        """Processa um batch internamente"""
        results = []
        
        # Criar tasks
        tasks = []
        for idx, lead in enumerate(batch):
            lead_idx = batch_num * self.config['batch_size'] + idx
            task = self._process_single_lead_with_retry(
                lead, process_function, lead_idx, performance_monitor
            )
            tasks.append(task)
        
        # Executar em paralelo
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for lead, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                lead_name = lead.get('name', lead.get('gdr_nome', 'SEM NOME'))
                print(f"   ❌ Erro: {lead_name} - {str(result)[:80]}")
                
                self.failed_leads.append({
                    'lead': lead,
                    'error': str(result),
                    'attempts': 1,
                    'batch_num': batch_num
                })
                results.append(None)
            else:
                results.append(result)
                self.processed_count += 1
                
                if self.on_lead_complete:
                    self.on_lead_complete(self.processed_count, result)
        
        return results
    
    async def _process_single_lead_with_retry(self, 
                                            lead: Dict[str, Any], 
                                            process_function: callable,
                                            lead_idx: int,
                                            performance_monitor: Optional[Any]) -> Optional[Dict[str, Any]]:
        """Processa um lead com retry em caso de erro"""
        lead_name = lead.get('name', lead.get('gdr_nome', f'Lead {lead_idx + 1}'))
        
        for attempt in range(self.config['max_retries_per_lead']):
            try:
                # Timer individual
                timer_id = None
                if performance_monitor:
                    timer_id = performance_monitor.start_timer(
                        'lead_processing',
                        {'lead_name': lead_name, 'attempt': attempt + 1}
                    )
                
                start_time = time.time()
                
                # Processar
                result = await process_function(lead)
                
                # Finalizar timer
                exec_time = time.time() - start_time
                if timer_id and performance_monitor:
                    performance_monitor.stop_timer(timer_id)
                
                self.execution_times.append(exec_time)
                
                # Log de sucesso
                print(f"   ✓ {lead_name[:40]:<40} processado em {exec_time:.1f}s")
                
                return result
                
            except Exception as e:
                if attempt < self.config['max_retries_per_lead'] - 1:
                    wait_time = self.config['retry_delay'] * (attempt + 1)
                    print(f"   ⚠️ Erro em {lead_name}, tentativa {attempt + 1}/{self.config['max_retries_per_lead']}. "
                          f"Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
        
        return None
    
    def _check_memory_before_batch(self) -> bool:
        """Verifica se há memória suficiente"""
        memory_percent = self._get_memory_usage()
        self.memory_usage_history.append(memory_percent)
        
        if memory_percent > self.config['memory_threshold'] * 100:
            if self.on_memory_warning:
                self.on_memory_warning(memory_percent)
            return False
        
        return True
    
    def _get_memory_usage(self) -> float:
        """Obtém uso de memória em porcentagem"""
        try:
            if PSUTIL_AVAILABLE:
                return psutil.virtual_memory().percent
            else:
                # Fallback: assumir 50% de uso
                return 50.0
        except:
            try:
                # Fallback para sistemas sem psutil
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # Estimativa aproximada
                return (usage.ru_maxrss / 1024.0 / 1024.0) / 4096 * 100
            except:
                return 50.0  # Default
    
    def _adjust_batch_size(self):
        """Ajusta tamanho do batch dinamicamente"""
        if not self.execution_times:
            return
        
        # Calcular performance recente
        recent_times = self.execution_times[-10:]
        avg_time = sum(recent_times) / len(recent_times)
        
        # Verificar memória
        memory_usage = self._get_memory_usage()
        
        # Ajustar baseado em performance
        if avg_time < 5 and memory_usage < 60:
            # Performance boa, aumentar batch
            self.current_batch_size = min(
                self.current_batch_size + 1,
                self.config['max_batch_size']
            )
        elif avg_time > 15 or memory_usage > 75:
            # Performance ruim ou memória alta, diminuir batch
            self.current_batch_size = max(
                self.current_batch_size - 1,
                self.config['min_batch_size']
            )
    
    async def _emergency_cleanup(self):
        """Limpeza de emergência de memória"""
        print("\n🧹 Executando limpeza de memória de emergência...")
        
        before = self._get_memory_usage()
        
        # Forçar garbage collection
        gc.collect()
        
        # Fechar recursos não utilizados
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass
        
        # Aguardar
        await asyncio.sleep(2)
        
        after = self._get_memory_usage()
        freed = before - after
        
        print(f"   Memória antes: {before:.1f}%")
        print(f"   Memória após: {after:.1f}%")
        if freed > 0:
            print(f"   Memória liberada: {freed:.1f}%")
    
    async def _force_garbage_collection(self):
        """Força coleta de lixo periódica"""
        print("\n🔄 Executando garbage collection...")
        before = self._get_memory_usage()
        
        gc.collect()
        self.last_gc_at = self.processed_count
        
        after = self._get_memory_usage()
        freed = before - after
        if freed > 0:
            print(f"   Memória liberada: {freed:.1f}%")
    
    async def _save_checkpoint(self, results: List[Dict], checkpoint_manager: Any):
        """Salva checkpoint"""
        print("\n💾 Salvando checkpoint...")
        
        try:
            # Filtrar resultados válidos
            valid_results = [r for r in results if r is not None]
            
            if valid_results:
                df_checkpoint = pd.DataFrame(valid_results)
                checkpoint_manager.save_incremental(df_checkpoint)
                
                if self.on_checkpoint_save:
                    self.on_checkpoint_save(len(valid_results))
                    
                print(f"   ✅ {len(valid_results)} registros salvos")
        except Exception as e:
            print(f"   ❌ Erro ao salvar checkpoint: {e}")
    
    async def _pause_between_batches(self):
        """Pausa entre batches com countdown"""
        pause_time = self.config['pause_between_batches']
        
        print(f"\n⏸️ Pausando {pause_time}s antes do próximo batch", end='')
        
        # Countdown visual
        for i in range(pause_time):
            await asyncio.sleep(1)
            remaining = pause_time - i - 1
            if remaining > 0:
                print(f"\r⏸️ Pausando {pause_time}s antes do próximo batch... {remaining}s", end='')
        
        print("\r" + " " * 60 + "\r", end='')  # Limpar linha
    
    async def _retry_failed_leads(self, process_function: callable, 
                                performance_monitor: Optional[Any]) -> List[Dict[str, Any]]:
        """Tenta reprocessar leads que falharam"""
        if not self.failed_leads:
            return []
        
        print(f"\n{'='*50}")
        print(f"🔄 REPROCESSANDO {len(self.failed_leads)} LEADS COM FALHA")
        print(f"{'='*50}")
        
        retry_results = []
        still_failed = []
        
        for idx, failed_item in enumerate(self.failed_leads):
            lead = failed_item['lead']
            attempts = failed_item['attempts']
            lead_name = lead.get('name', lead.get('gdr_nome', 'SEM NOME'))
            
            if attempts < self.config['max_retries_per_lead']:
                try:
                    print(f"\n🔄 Reprocessando {idx + 1}/{len(self.failed_leads)}: {lead_name}")
                    
                    result = await process_function(lead)
                    retry_results.append(result)
                    
                    print(f"   ✅ Sucesso na nova tentativa!")
                    
                except Exception as e:
                    failed_item['attempts'] += 1
                    failed_item['error'] = str(e)
                    still_failed.append(failed_item)
                    print(f"   ❌ Falhou novamente: {str(e)[:100]}")
            else:
                still_failed.append(failed_item)
        
        self.failed_leads = still_failed
        
        if still_failed:
            print(f"\n⚠️ {len(still_failed)} leads falharam definitivamente")
        
        return retry_results
    
    def _print_final_statistics(self, results: List[Dict[str, Any]], total_leads: int):
        """Imprime estatísticas finais detalhadas"""
        successful = len([r for r in results if r is not None])
        failed = total_leads - successful
        
        print(f"\n{'='*70}")
        print(f"📊 ESTATÍSTICAS FINAIS DA EXECUÇÃO")
        print(f"{'='*70}")
        
        # Resultados
        print(f"\n📈 RESULTADOS:")
        print(f"   • Total de leads: {total_leads}")
        print(f"   • Processados com sucesso: {successful} ({successful/total_leads*100:.1f}%)")
        print(f"   • Falhas: {failed} ({failed/total_leads*100:.1f}%)")
        
        # Tempos
        if self.execution_times:
            avg_time = sum(self.execution_times) / len(self.execution_times)
            min_time = min(self.execution_times)
            max_time = max(self.execution_times)
            total_time = sum(self.execution_times)
            
            print(f"\n⏱️ TEMPOS DE EXECUÇÃO:")
            print(f"   • Total: {total_time:.1f}s ({total_time/60:.1f} minutos)")
            print(f"   • Médio por lead: {avg_time:.1f}s")
            print(f"   • Mínimo: {min_time:.1f}s")
            print(f"   • Máximo: {max_time:.1f}s")
        
        # Memória
        if self.memory_usage_history:
            avg_memory = sum(self.memory_usage_history) / len(self.memory_usage_history)
            max_memory = max(self.memory_usage_history)
            min_memory = min(self.memory_usage_history)
            
            print(f"\n💾 USO DE MEMÓRIA:")
            print(f"   • Médio: {avg_memory:.1f}%")
            print(f"   • Máximo: {max_memory:.1f}%")
            print(f"   • Mínimo: {min_memory:.1f}%")
        
        # Performance do batch
        if self.config['adaptive_batch_size']:
            print(f"\n📦 BATCH ADAPTATIVO:")
            print(f"   • Tamanho inicial: {self.config['batch_size']}")
            print(f"   • Tamanho final: {self.current_batch_size}")
        
        print(f"{'='*70}\n")
    
    def get_execution_report(self) -> Dict[str, Any]:
        """Gera relatório detalhado da execução"""
        return {
            'summary': {
                'total_processed': self.processed_count,
                'failed_count': len(self.failed_leads),
                'success_rate': (self.processed_count / (self.processed_count + len(self.failed_leads))) * 100 
                                if (self.processed_count + len(self.failed_leads)) > 0 else 0
            },
            'failed_leads': [
                {
                    'name': f['lead'].get('name', f['lead'].get('gdr_nome', 'Unknown')),
                    'error': f['error'],
                    'attempts': f['attempts']
                }
                for f in self.failed_leads
            ],
            'execution_times': {
                'all': self.execution_times,
                'average': sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0,
                'min': min(self.execution_times) if self.execution_times else 0,
                'max': max(self.execution_times) if self.execution_times else 0,
                'total': sum(self.execution_times) if self.execution_times else 0
            },
            'memory_usage': {
                'history': self.memory_usage_history,
                'average': sum(self.memory_usage_history) / len(self.memory_usage_history) if self.memory_usage_history else 0,
                'max': max(self.memory_usage_history) if self.memory_usage_history else 0,
                'min': min(self.memory_usage_history) if self.memory_usage_history else 0
            },
            'batch_info': {
                'initial_size': self.config['batch_size'],
                'final_size': self.current_batch_size,
                'adaptive': self.config['adaptive_batch_size']
            }
        }