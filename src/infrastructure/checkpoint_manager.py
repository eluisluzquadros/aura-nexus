# -*- coding: utf-8 -*-
"""
AURA NEXUS - Gerenciador de Checkpoints
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("AURA_NEXUS.Checkpoint")


class CheckpointManager:
    """Gerencia checkpoints de processamento para retomada"""
    
    def __init__(self, checkpoint_dir: Path = Path("data/checkpoints")):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = None
        
    def create_session(self, name: str = None) -> str:
        """Cria nova sessão de checkpoint"""
        if not name:
            name = f"session_{datetime.now():%Y%m%d_%H%M%S}"
        
        self.current_session = name
        session_dir = self.checkpoint_dir / name
        session_dir.mkdir(exist_ok=True)
        
        logger.info(f"📍 Sessão de checkpoint criada: {name}")
        return name
    
    async def save_checkpoint(self, data: Dict[str, Any], name: str = None) -> bool:
        """Salva checkpoint"""
        try:
            if not self.current_session:
                self.create_session()
            
            if not name:
                name = f"checkpoint_{datetime.now():%Y%m%d_%H%M%S}"
            
            checkpoint_path = self.checkpoint_dir / self.current_session / f"{name}.json"
            
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'session': self.current_session,
                'data': data
            }
            
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Checkpoint salvo: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar checkpoint: {e}")
            return False
    
    async def load_checkpoint(self, session: str = None, name: str = None) -> Optional[Dict[str, Any]]:
        """Carrega checkpoint"""
        try:
            if not session:
                # Pegar sessão mais recente
                sessions = [d for d in self.checkpoint_dir.iterdir() if d.is_dir()]
                if not sessions:
                    return None
                session = max(sessions, key=lambda d: d.stat().st_mtime).name
            
            session_dir = self.checkpoint_dir / session
            
            if not name:
                # Pegar checkpoint mais recente
                checkpoints = list(session_dir.glob("checkpoint_*.json"))
                if not checkpoints:
                    return None
                checkpoint_path = max(checkpoints, key=lambda f: f.stat().st_mtime)
            else:
                checkpoint_path = session_dir / f"{name}.json"
            
            if not checkpoint_path.exists():
                return None
            
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"📂 Checkpoint carregado: {checkpoint_path.name}")
            return data['data']
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar checkpoint: {e}")
            return None
    
    def list_sessions(self) -> list:
        """Lista todas as sessões disponíveis"""
        sessions = []
        for session_dir in self.checkpoint_dir.iterdir():
            if session_dir.is_dir():
                checkpoints = list(session_dir.glob("*.json"))
                sessions.append({
                    'name': session_dir.name,
                    'created': datetime.fromtimestamp(session_dir.stat().st_ctime),
                    'checkpoints': len(checkpoints)
                })
        
        return sorted(sessions, key=lambda s: s['created'], reverse=True)
    
    def clean_old_sessions(self, keep_last: int = 5):
        """Remove sessões antigas mantendo apenas as N mais recentes"""
        sessions = self.list_sessions()
        
        if len(sessions) > keep_last:
            to_remove = sessions[keep_last:]
            
            for session in to_remove:
                session_dir = self.checkpoint_dir / session['name']
                
                # Remover todos os arquivos
                for file in session_dir.glob("*"):
                    file.unlink()
                
                # Remover diretório
                session_dir.rmdir()
                
                logger.info(f"🗑️ Sessão removida: {session['name']}")