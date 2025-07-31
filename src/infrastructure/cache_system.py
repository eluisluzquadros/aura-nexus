# -*- coding: utf-8 -*-
"""
AURA NEXUS - Sistema de Cache Simplificado
"""

import json
import os
import hashlib
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger("AURA_NEXUS.Cache")


class SmartMultiLevelCache:
    """Sistema de cache simplificado em disco"""
    
    def __init__(self, cache_dir: Path = Path("data/cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Inicializa o sistema de cache"""
        logger.info(f"📦 Cache inicializado em: {self.cache_dir}")
        return True
    
    def _get_cache_key(self, key: str) -> str:
        """Gera hash MD5 da chave para nome de arquivo"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Retorna caminho do arquivo de cache"""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"
    
    async def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache"""
        async with self._lock:
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                return None
            
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Verificar expiração
                if 'expires_at' in data:
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    if datetime.now() > expires_at:
                        cache_path.unlink()  # Remove arquivo expirado
                        return None
                
                return data.get('value')
                
            except Exception as e:
                logger.error(f"Erro ao ler cache: {e}")
                return None
    
    async def set(self, key: str, value: Any, ttl: int = 86400) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida em segundos (padrão: 24h)
        """
        async with self._lock:
            try:
                cache_path = self._get_cache_path(key)
                
                data = {
                    'key': key,
                    'value': value,
                    'created_at': datetime.now().isoformat(),
                    'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat()
                }
                
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                return True
                
            except Exception as e:
                logger.error(f"Erro ao salvar cache: {e}")
                return False
    
    async def delete(self, key: str) -> bool:
        """Remove item do cache"""
        async with self._lock:
            cache_path = self._get_cache_path(key)
            
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    return True
                except:
                    pass
            
            return False
    
    async def clear(self) -> int:
        """Limpa todo o cache"""
        count = 0
        async with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                    count += 1
                except:
                    pass
        
        logger.info(f"🧹 Cache limpo: {count} arquivos removidos")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_items': len(cache_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'cache_dir': str(self.cache_dir)
        }