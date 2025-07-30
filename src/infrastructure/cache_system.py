import os
import json
import asyncio
import hashlib
import pickle
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import time
import random
from collections import OrderedDict, defaultdict
import numpy as np
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Imports de outras células
from aura_nexus_celula_02 import PerformanceMetric

# Logger
logger = logging.getLogger("AURA_NEXUS.CachePerformance")

# ===================================================================================
# CÉLULA 8: SISTEMA DE CACHE E PERFORMANCE
# ===================================================================================

class SmartMultiLevelCache:
    """Sistema de cache inteligente multi-nível"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Configurações padrão
        self.config.setdefault('l1_ttl', 3600)  # 1 hora
        self.config.setdefault('l1_max_size', 1000)
        self.config.setdefault('l2_ttl', 86400)  # 24 horas
        self.config.setdefault('l2_path', '/content/drive/MyDrive/aura_nexus_cache/l2')
        self.config.setdefault('l3_ttl', 604800)  # 7 dias
        self.config.setdefault('l3_path', '/content/drive/MyDrive/aura_nexus_cache/l3')
        
        # Níveis de cache
        self.levels = {
            'L1_memory': {
                'type': 'memory',
                'storage': OrderedDict(),
                'ttl': self.config['l1_ttl'],
                'max_size': self.config['l1_max_size'],
                'hits': 0,
                'misses': 0
            },
            'L2_file': {
                'type': 'file',
                'path': self.config['l2_path'],
                'ttl': self.config['l2_ttl'],
                'hits': 0,
                'misses': 0
            },
            'L3_persistent': {
                'type': 'persistent',
                'path': self.config['l3_path'],
                'ttl': self.config['l3_ttl'],
                'hits': 0,
                'misses': 0
            }
        }
        
        # Estatísticas globais
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'bytes_saved': 0,
            'time_saved': 0
        }
        
        # Criar diretórios
        os.makedirs(self.config['l2_path'], exist_ok=True)
        os.makedirs(self.config['l3_path'], exist_ok=True)
    
    async def get(self, key: str, cache_type: str = 'general') -> Optional[Any]:
        """Busca valor no cache em cascata"""
        self.stats['total_requests'] += 1
        start_time = time.time()
        
        # Tentar L1 (memória)
        value = await self._get_from_l1(key)
        if value is not None:
            self.stats['cache_hits'] += 1
            self.stats['time_saved'] += time.time() - start_time
            return value
        
        # Tentar L2 (arquivo)
        value = await self._get_from_l2(key)
        if value is not None:
            # Promover para L1
            await self._set_to_l1(key, value)
            self.stats['cache_hits'] += 1
            self.stats['time_saved'] += time.time() - start_time
            return value
        
        # Tentar L3 (persistente)
        value = await self._get_from_l3(key)
        if value is not None:
            # Promover para L1 e L2
            await self._set_to_l1(key, value)
            await self._set_to_l2(key, value)
            self.stats['cache_hits'] += 1
            self.stats['time_saved'] += time.time() - start_time
            return value
        
        # Cache miss
        self.stats['cache_misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, cache_type: str = 'general',
                  ttl_override: Optional[int] = None) -> bool:
        """Armazena valor no cache"""
        try:
            # Estimar tamanho
            value_size = self._estimate_size(value)
            
            # Armazenar em L1
            await self._set_to_l1(key, value, ttl_override)
            
            # Armazenar em L2 se grande
            if value_size > 1024:  # > 1KB
                await self._set_to_l2(key, value, ttl_override)
            
            # Armazenar em L3 se muito importante
            if cache_type in ['place_details', 'analysis_results']:
                await self._set_to_l3(key, value, ttl_override)
            
            self.stats['bytes_saved'] += value_size
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar no cache: {e}")
            return False
    
    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """Busca em L1 (memória)"""
        storage = self.levels['L1_memory']['storage']
        
        if key in storage:
            entry = storage[key]
            
            # Verificar TTL
            if time.time() - entry['timestamp'] <= entry['ttl']:
                # Atualizar LRU
                storage.move_to_end(key)
                self.levels['L1_memory']['hits'] += 1
                return entry['value']
            else:
                # Expirado
                del storage[key]
        
        self.levels['L1_memory']['misses'] += 1
        return None
    
    async def _set_to_l1(self, key: str, value: Any, ttl_override: Optional[int] = None):
        """Armazena em L1 (memória)"""
        storage = self.levels['L1_memory']['storage']
        ttl = ttl_override or self.levels['L1_memory']['ttl']
        
        # Armazenar
        storage[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        
        # LRU - mover para o final
        storage.move_to_end(key)
        
        # Limitar tamanho
        max_size = self.levels['L1_memory']['max_size']
        while len(storage) > max_size:
            storage.popitem(last=False)
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Busca em L2 (arquivo)"""
        try:
            file_path = os.path.join(self.levels['L2_file']['path'], f"{key}.pkl")
            
            if os.path.exists(file_path):
                # Verificar idade do arquivo
                file_age = time.time() - os.path.getmtime(file_path)
                if file_age <= self.levels['L2_file']['ttl']:
                    if AIOFILES_AVAILABLE:
                        async with aiofiles.open(file_path, 'rb') as f:
                            data = await f.read()
                    else:
                        # Fallback síncrono
                        with open(file_path, 'rb') as f:
                            data = f.read()
                    value = pickle.loads(data)
                    
                    self.levels['L2_file']['hits'] += 1
                    return value
                else:
                    # Expirado
                    os.remove(file_path)
            
            self.levels['L2_file']['misses'] += 1
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao ler L2: {e}")
            self.levels['L2_file']['misses'] += 1
            return None
    
    async def _set_to_l2(self, key: str, value: Any, ttl_override: Optional[int] = None):
        """Armazena em L2 (arquivo)"""
        try:
            file_path = os.path.join(self.levels['L2_file']['path'], f"{key}.pkl")
            
            data = pickle.dumps(value)
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(data)
            else:
                # Fallback síncrono
                with open(file_path, 'wb') as f:
                    f.write(data)
                
        except Exception as e:
            logger.debug(f"Erro ao salvar L2: {e}")
    
    async def _get_from_l3(self, key: str) -> Optional[Any]:
        """Busca em L3 (persistente)"""
        try:
            # Hash do key para criar subdiretórios
            key_hash = hashlib.md5(key.encode()).hexdigest()
            subdir = key_hash[:2]
            
            file_path = os.path.join(
                self.levels['L3_persistent']['path'],
                subdir,
                f"{key}.pkl"
            )
            
            if os.path.exists(file_path):
                # Verificar idade
                file_age = time.time() - os.path.getmtime(file_path)
                if file_age <= self.levels['L3_persistent']['ttl']:
                    if AIOFILES_AVAILABLE:
                        async with aiofiles.open(file_path, 'rb') as f:
                            data = await f.read()
                    else:
                        with open(file_path, 'rb') as f:
                            data = f.read()
                    value = pickle.loads(data)
                    
                    self.levels['L3_persistent']['hits'] += 1
                    return value
                else:
                    os.remove(file_path)
            
            self.levels['L3_persistent']['misses'] += 1
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao ler L3: {e}")
            self.levels['L3_persistent']['misses'] += 1
            return None
    
    async def _set_to_l3(self, key: str, value: Any, ttl_override: Optional[int] = None):
        """Armazena em L3 (persistente)"""
        try:
            # Hash do key para criar subdiretórios
            key_hash = hashlib.md5(key.encode()).hexdigest()
            subdir = key_hash[:2]
            
            dir_path = os.path.join(self.levels['L3_persistent']['path'], subdir)
            os.makedirs(dir_path, exist_ok=True)
            
            file_path = os.path.join(dir_path, f"{key}.pkl")
            
            data = pickle.dumps(value)
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(data)
            else:
                # Fallback síncrono
                with open(file_path, 'wb') as f:
                    f.write(data)
                
        except Exception as e:
            logger.debug(f"Erro ao salvar L3: {e}")
    
    def _estimate_size(self, obj: Any) -> int:
        """Estima tamanho de um objeto em bytes"""
        try:
            return len(pickle.dumps(obj))
        except:
            return 1024  # Default 1KB
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do cache"""
        total_requests = self.stats['total_requests']
        
        if total_requests == 0:
            hit_rate = 0
        else:
            hit_rate = (self.stats['cache_hits'] / total_requests) * 100
        
        # Estatísticas por nível
        level_stats = {}
        for level_name, level_data in self.levels.items():
            level_requests = level_data['hits'] + level_data['misses']
            if level_requests > 0:
                level_hit_rate = (level_data['hits'] / level_requests) * 100
            else:
                level_hit_rate = 0
            
            level_stats[level_name] = {
                'hits': level_data['hits'],
                'misses': level_data['misses'],
                'hit_rate': round(level_hit_rate, 2),
                'type': level_data['type']
            }
        
        return {
            'global': {
                'total_requests': total_requests,
                'cache_hits': self.stats['cache_hits'],
                'cache_misses': self.stats['cache_misses'],
                'hit_rate': round(hit_rate, 2),
                'bytes_saved': self._format_bytes(self.stats['bytes_saved']),
                'time_saved': round(self.stats['time_saved'], 2)
            },
            'levels': level_stats
        }
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Formata bytes para exibição"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"
    
    async def clear_expired(self):
        """Limpa entradas expiradas de todos os níveis"""
        cleared = {'L1': 0, 'L2': 0, 'L3': 0}
        
        # Limpar L1
        storage = self.levels['L1_memory']['storage']
        keys_to_remove = []
        
        for key, entry in storage.items():
            if time.time() - entry['timestamp'] > entry['ttl']:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del storage[key]
            cleared['L1'] += 1
        
        # Limpar L2 e L3 seria mais complexo (varrer arquivos)
        # Por ora, apenas registramos a limpeza de L1
        
        logger.info(f"Cache cleanup: {cleared}")
        return cleared


class PerformanceMonitor:
    """Monitor avançado de performance"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.active_timers = {}
        self.counters = defaultdict(int)
        self.gauges = {}
        
        # Configurações
        self.max_metrics_per_type = 1000
        self.alert_thresholds = {
            'lead_processing_time': 30.0,  # segundos
            'memory_usage': 80.0,  # percentual
            'api_response_time': 5.0  # segundos
        }
    
    def start_timer(self, name: str, metadata: Optional[Dict] = None) -> str:
        """Inicia timer com metadados"""
        timer_id = f"{name}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        self.active_timers[timer_id] = {
            'name': name,
            'start_time': time.time(),
            'metadata': metadata or {},
            'checkpoints': []
        }
        
        return timer_id
    
    def add_checkpoint(self, timer_id: str, checkpoint_name: str):
        """Adiciona checkpoint a um timer ativo"""
        if timer_id in self.active_timers:
            self.active_timers[timer_id]['checkpoints'].append({
                'name': checkpoint_name,
                'time': time.time()
            })
    
    def stop_timer(self, timer_id: str) -> float:
        """Para timer e registra métrica"""
        if timer_id not in self.active_timers:
            return 0.0
        
        timer = self.active_timers.pop(timer_id)
        elapsed = time.time() - timer['start_time']
        
        # Criar métrica
        metric = PerformanceMetric(
            name=timer['name'],
            value=elapsed,
            unit='seconds',
            timestamp=datetime.now(),
            tags=timer['metadata']
        )
        
        # Adicionar checkpoints como tags
        if timer['checkpoints']:
            checkpoint_times = {}
            prev_time = timer['start_time']
            
            for cp in timer['checkpoints']:
                cp_elapsed = cp['time'] - prev_time
                checkpoint_times[cp['name']] = round(cp_elapsed, 3)
                prev_time = cp['time']
            
            metric.tags['checkpoints'] = checkpoint_times
        
        # Armazenar métrica
        self._store_metric(metric)
        
        # Verificar alertas
        self._check_alerts(metric)
        
        return elapsed
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict] = None):
        """Incrementa contador"""
        self.counters[name] += value
        
        # Registrar como métrica também
        metric = PerformanceMetric(
            name=f"counter.{name}",
            value=self.counters[name],
            unit='count',
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        self._store_metric(metric)
    
    def set_gauge(self, name: str, value: float, unit: str = 'value', tags: Optional[Dict] = None):
        """Define valor de gauge"""
        self.gauges[name] = value
        
        # Registrar como métrica
        metric = PerformanceMetric(
            name=f"gauge.{name}",
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        self._store_metric(metric)
    
    def _store_metric(self, metric: PerformanceMetric):
        """Armazena métrica com limite de tamanho"""
        self.metrics[metric.name].append(metric)
        
        # Limitar tamanho
        if len(self.metrics[metric.name]) > self.max_metrics_per_type:
            # Remover 10% mais antigas
            to_remove = int(self.max_metrics_per_type * 0.1)
            self.metrics[metric.name] = self.metrics[metric.name][to_remove:]
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Verifica se métrica excede thresholds"""
        for alert_name, threshold in self.alert_thresholds.items():
            if alert_name in metric.name and metric.value > threshold:
                logger.warning(
                    f"⚠️ Performance alert: {metric.name} = {metric.value:.2f} "
                    f"(threshold: {threshold})"
                )
    
    def get_summary(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """Retorna resumo das métricas"""
        summary = {}
        
        # Filtrar por janela de tempo se especificado
        if time_window:
            cutoff_time = datetime.now().timestamp() - time_window
        else:
            cutoff_time = 0
        
        # Processar cada tipo de métrica
        for metric_name, metric_list in self.metrics.items():
            # Filtrar por tempo
            filtered = [
                m for m in metric_list 
                if m.timestamp.timestamp() > cutoff_time
            ]
            
            if filtered:
                values = [m.value for m in filtered]
                
                summary[metric_name] = {
                    'count': len(filtered),
                    'avg': np.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'p50': np.percentile(values, 50),
                    'p95': np.percentile(values, 95),
                    'p99': np.percentile(values, 99),
                    'std': np.std(values),
                    'unit': filtered[0].unit
                }
        
        # Adicionar contadores
        summary['counters'] = dict(self.counters)
        
        # Adicionar gauges
        summary['gauges'] = dict(self.gauges)
        
        return summary
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """Gera relatório detalhado de performance"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'resource_usage': self._get_resource_usage(),
            'slow_operations': self._identify_slow_operations(),
            'trends': self._analyze_trends()
        }
        
        return report
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Obtém uso de recursos do sistema"""
        try:
            if PSUTIL_AVAILABLE:
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=0.1)
                
                return {
                    'memory': {
                        'percent': memory.percent,
                        'used_gb': memory.used / (1024**3),
                        'available_gb': memory.available / (1024**3)
                    },
                    'cpu': {
                        'percent': cpu,
                        'count': psutil.cpu_count()
                    }
                }
            else:
                return {}
        except:
            return {}
    
    def _identify_slow_operations(self, top_n: int = 10) -> List[Dict]:
        """Identifica operações mais lentas"""
        slow_ops = []
        
        for metric_name, metric_list in self.metrics.items():
            if metric_list and metric_list[0].unit == 'seconds':
                # Pegar operações mais lentas
                sorted_metrics = sorted(metric_list, key=lambda m: m.value, reverse=True)
                
                for metric in sorted_metrics[:top_n]:
                    slow_ops.append({
                        'operation': metric.name,
                        'duration': metric.value,
                        'timestamp': metric.timestamp.isoformat(),
                        'tags': metric.tags
                    })
        
        # Ordenar globalmente
        slow_ops.sort(key=lambda x: x['duration'], reverse=True)
        
        return slow_ops[:top_n]
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analisa tendências nas métricas"""
        trends = {}
        
        for metric_name, metric_list in self.metrics.items():
            if len(metric_list) >= 10:
                values = [m.value for m in metric_list]
                timestamps = [m.timestamp.timestamp() for m in metric_list]
                
                # Calcular tendência simples
                if len(values) >= 2:
                    # Regressão linear simples
                    x = np.array(timestamps) - timestamps[0]
                    y = np.array(values)
                    
                    if np.std(x) > 0:  # Evitar divisão por zero
                        slope = np.cov(x, y)[0, 1] / np.var(x)
                        
                        if abs(slope) > 0.01:  # Threshold de significância
                            trends[metric_name] = {
                                'direction': 'increasing' if slope > 0 else 'decreasing',
                                'rate': float(slope),
                                'current_avg': float(np.mean(values[-5:])),
                                'previous_avg': float(np.mean(values[:5]))
                            }
        
        return trends
    
    def export_metrics(self, format: str = 'json') -> str:
        """Exporta métricas em formato específico"""
        if format == 'json':
            data = {
                'metrics': {},
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'exported_at': datetime.now().isoformat()
            }
            
            # Converter métricas
            for name, metric_list in self.metrics.items():
                data['metrics'][name] = [
                    {
                        'value': m.value,
                        'unit': m.unit,
                        'timestamp': m.timestamp.isoformat(),
                        'tags': m.tags
                    }
                    for m in metric_list
                ]
            
            return json.dumps(data, indent=2)
        
        else:
            raise ValueError(f"Formato não suportado: {format}")