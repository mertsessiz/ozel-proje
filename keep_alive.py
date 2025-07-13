"""
Replit Keep-Alive Mekanizması
Web sunucusu başlatarak uygulamanın sürekli çalışmasını sağlar
"""

from flask import Flask, jsonify
from threading import Thread
import logging

app = Flask(__name__)

# Flask logging'i sessizleştir
logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.route('/')
def index():
    """Ana sayfa - durum kontrolü"""
    return jsonify({
        "status": "online",
        "message": "Telegram Userbot çalışıyor",
        "service": "TC Kimlik Sorgu Bot"
    })

@app.route('/health')
def health():
    """Sağlık kontrolü endpoint'i"""
    return jsonify({
        "status": "healthy",
        "uptime": "running"
    })

@app.route('/status')
def status():
    """Detaylı durum bilgisi"""
    return jsonify({
        "bot_status": "active",
        "listening": "group_messages",
        "features": [
            "TC kimlik sorgusu",
            "Otomatik yanıt",
            "Inline butonlar",
            "Kopyalama özelliği"
        ]
    })

def run():
    """Flask sunucusunu çalıştır"""
    app.run(host='0.0.0.0', port=5000, debug=False)

def keep_alive():
    """Keep-alive thread'ini başlat"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
