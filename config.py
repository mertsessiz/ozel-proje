"""
Konfigürasyon Dosyası
Ortam değişkenlerinden ayarları yükler
"""

import os
import logging

class Config:
    """Uygulama konfigürasyonu"""
    
    # Telegram API bilgileri
    API_ID = int(os.getenv('TELEGRAM_API_ID', '22574551'))
    API_HASH = os.getenv('TELEGRAM_API_HASH', 'ba351b3965b636b695c0fdea8d7dd9f8')
    
    # Session dosyası
    SESSION_NAME = os.getenv('SESSION_NAME', 'userbot_session')
    
    # Hedef bot kullanıcı adı
    TARGET_BOT_USERNAME = os.getenv('TARGET_BOT_USERNAME', 'TheXThoth_bot')
    
    # Grup ID'leri (ortam değişkeninden alınabilir)
    GROUP_IDS_STR = os.getenv('GROUP_IDS', '-4778709440,-1002287233685,-1002814809362,-4891655686,-1002769670218,-1002437148486')
    GROUP_IDS = [int(id.strip()) for id in GROUP_IDS_STR.split(',') if id.strip()]
    
    # Logging ayarları
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Yeniden bağlanma ayarları
    RECONNECT_ATTEMPTS = int(os.getenv('RECONNECT_ATTEMPTS', '5'))
    RECONNECT_DELAY = int(os.getenv('RECONNECT_DELAY', '10'))
    
    @classmethod
    def validate(cls):
        """Konfigürasyon doğrulama"""
        logger = logging.getLogger(__name__)
        
        if not cls.API_ID or not cls.API_HASH:
            logger.error("TELEGRAM_API_ID ve TELEGRAM_API_HASH ortam değişkenleri gerekli!")
            return False
            
        if not cls.GROUP_IDS:
            logger.warning("Grup ID'leri bulunamadı, varsayılan değerler kullanılacak")
            
        logger.info(f"Konfigürasyon yüklendi: {len(cls.GROUP_IDS)} grup dinlenecek")
        return True
