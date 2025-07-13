"""
Logging Konfigürasyonu
Konsol ve dosya logging'i yapılandırır
"""

import logging
import sys
from datetime import datetime

def setup_logger(name=__name__, level=logging.INFO):
    """Logger kurulumu"""
    
    # Ana logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Zaten handler varsa tekrar ekleme
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Root logger için de ayarla
    if name == __name__:
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(console_handler)
    
    return logger
