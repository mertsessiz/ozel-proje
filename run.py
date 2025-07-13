#!/usr/bin/env python3
"""
Deployment için optimize edilmiş başlatma dosyası
"""

import os
import sys
import asyncio
import logging

# Dosya yollarını kontrol et
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Gerekli modülleri import et
try:
    from keep_alive import keep_alive
    from userbot import TelegramUserbot
    from logger import setup_logger
except ImportError as e:
    print(f"Import hatası: {e}")
    sys.exit(1)

async def main():
    """Ana fonksiyon"""
    logger = setup_logger()
    
    try:
        # Keep-alive sunucusunu başlat
        keep_alive()
        logger.info("Keep-alive sunucusu başlatıldı")
        
        # Userbot'u başlat
        userbot = TelegramUserbot()
        await userbot.start()
        
    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())