# -*- coding: utf-8 -*-
"""
AURA NEXUS - Utilitários
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import colorama
from colorama import Fore, Style

# Inicializa colorama para Windows
colorama.init()


def setup_logging(name: str = "AURA_NEXUS", level: int = logging.INFO) -> logging.Logger:
    """
    Configura sistema de logging com cores e formatação
    
    Args:
        name: Nome do logger
        level: Nível de logging
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Remove handlers existentes
    logger.handlers.clear()
    
    # Cria handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Formato com cores
    class ColoredFormatter(logging.Formatter):
        """Formatter que adiciona cores aos logs"""
        
        COLORS = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.RED + Style.BRIGHT,
        }
        
        def format(self, record):
            # Adiciona cor baseada no nível
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
            
            # Adiciona emoji baseado no nível
            emojis = {
                'DEBUG': '🔍',
                'INFO': '📌',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }
            
            if hasattr(record, 'emoji'):
                emoji = record.emoji
            else:
                emoji = emojis.get(record.levelname.strip().split()[0], '')
            
            # Formata mensagem
            formatted = super().format(record)
            if emoji:
                formatted = f"{emoji} {formatted}"
                
            return formatted
    
    # Define formato
    formatter = ColoredFormatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(level)
    
    # Evita propagação para o logger raiz
    logger.propagate = False
    
    return logger


def format_time_elapsed(seconds: float) -> str:
    """
    Formata tempo decorrido em formato legível
    
    Args:
        seconds: Tempo em segundos
        
    Returns:
        String formatada (ex: "2h 15m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres inválidos
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Nome sanitizado
    """
    # Caracteres inválidos em Windows/Linux
    invalid_chars = '<>:"|?*\\/\0'
    
    # Substitui caracteres inválidos
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove espaços extras
    filename = ' '.join(filename.split())
    
    # Limita tamanho
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename.strip()


def format_phone_br(phone: str) -> str:
    """
    Formata número de telefone brasileiro
    
    Args:
        phone: Número de telefone
        
    Returns:
        Telefone formatado
    """
    # Remove caracteres não numéricos
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Adiciona código do país se não tiver
    if len(digits) == 10 or len(digits) == 11:
        if not digits.startswith('55'):
            digits = '55' + digits
    
    # Formata baseado no tamanho
    if len(digits) == 12:  # 55 + 10 dígitos (fixo)
        return f"+{digits[:2]} ({digits[2:4]}) {digits[4:8]}-{digits[8:]}"
    elif len(digits) == 13:  # 55 + 11 dígitos (celular)
        return f"+{digits[:2]} ({digits[2:4]}) {digits[4:5]} {digits[5:9]}-{digits[9:]}"
    else:
        return phone  # Retorna original se não conseguir formatar


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro
    
    Args:
        cnpj: String do CNPJ
        
    Returns:
        True se válido
    """
    # Remove caracteres não numéricos
    cnpj = ''.join(c for c in cnpj if c.isdigit())
    
    # Verifica tamanho
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos dígitos são iguais
    if len(set(cnpj)) == 1:
        return False
    
    # Calcula primeiro dígito verificador
    soma = 0
    peso = 5
    for i in range(12):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    
    # Verifica primeiro dígito
    if int(cnpj[12]) != dv1:
        return False
    
    # Calcula segundo dígito verificador
    soma = 0
    peso = 6
    for i in range(13):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    
    # Verifica segundo dígito
    return int(cnpj[13]) == dv2


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    Cria barra de progresso ASCII
    
    Args:
        current: Valor atual
        total: Valor total
        width: Largura da barra
        
    Returns:
        String da barra de progresso
    """
    if total == 0:
        return "[" + "=" * width + "]"
    
    progress = current / total
    filled = int(width * progress)
    
    bar = "[" + "=" * filled + "-" * (width - filled) + "]"
    percentage = f"{progress * 100:.1f}%"
    
    return f"{bar} {percentage}"


# Exporta funções principais
__all__ = [
    'setup_logging',
    'format_time_elapsed',
    'sanitize_filename',
    'format_phone_br',
    'validate_cnpj',
    'create_progress_bar'
]
