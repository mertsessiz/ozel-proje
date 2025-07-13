"""
Railway.app Deployment Konfigürasyonu
Tarayıcı bağımsız çalışma için alternatif platform
"""

import os
import asyncio
from userbot import TelegramUserbot
from keep_alive import keep_alive
from logger import setup_logger

def main():
    """Railway için ana fonksiyon"""
    logger = setup_logger()
    
    # Railway ortam değişkenleri
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Railway.app'da başlatılıyor, port: {port}")
    
    # Keep-alive'ı farklı portta başlat
    keep_alive()
    
    # Userbot'u başlat
    async def start_bot():
        userbot = TelegramUserbot()
        await userbot.start()
    
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()