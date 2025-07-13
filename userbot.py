"""
Telegram Userbot Ana Sınıfı
TC kimlik sorgusu yapan bot fonksiyonalitesi
"""

import asyncio
import re
import logging
import os
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import (
    FloodWaitError, 
    AuthKeyUnregisteredError,
    SessionPasswordNeededError
)
from telethon.tl.types import Channel, Chat
from config import Config

class TelegramUserbot:
    """Telegram Userbot sınıfı"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Konfigürasyon doğrulama
        if not self.config.validate():
            raise ValueError("Konfigürasyon hatası!")
        
        # Telegram client
        self.client = TelegramClient(
            self.config.SESSION_NAME,
            self.config.API_ID,
            self.config.API_HASH
        )
        
        # Bekleyen sorgular
        self.pending = {}
        
        # Otomatik grup monitoring
        self.grup_monitoring_aktif = True
        self.grup_kontrol_suresi = 15  # 15 saniyede bir kontrol
        
        # Event handler'ları kaydet
        self.register_handlers()
        
        self.logger.info("Userbot başlatıldı")
    
    def register_handlers(self):
        """Event handler'ları kaydet"""
        
        @self.client.on(events.NewMessage)
        async def bridge_handler(event):
            await self.handle_group_message(event)
        
        @self.client.on(events.NewMessage(from_users=self.config.TARGET_BOT_USERNAME))
        async def reply_handler(event):
            await self.handle_bot_reply(event)
        
        @self.client.on(events.CallbackQuery)
        async def callback_handler(event):
            await self.handle_callback_query(event)
    
    async def handle_group_message(self, event):
        """Grup mesajlarını işle"""
        try:
            chat_id = event.chat_id
            text = (event.raw_text or "").strip()
            
            if chat_id not in self.config.GROUP_IDS:
                return
            
            self.logger.debug(f"Grup mesajı alındı: {chat_id}")
            
            if re.fullmatch(r"\d{10}", text):
                await event.reply("❌ TC Kimlik Numarası Eksik (10 haneli)")
                self.logger.info(f"10 haneli TC girişi tespit edildi: {text[:3]}***")
                
            elif re.fullmatch(r"\d{11}", text):
                self.pending[text] = chat_id
                
                try:
                    bot = await self.client.get_entity(self.config.TARGET_BOT_USERNAME)
                    await self.client.send_message(bot, f"/sorgu -tc {text}")
                    self.logger.info(f"Sorgu gönderildi: {text[:3]}***")
                    
                except Exception as e:
                    self.logger.error(f"Bot mesajı gönderilirken hata: {e}")
                    await event.reply("❌ Sorgu gönderilemedi, lütfen tekrar deneyin")
                    self.pending.pop(text, None)
                    
        except Exception as e:
            self.logger.error(f"Grup mesajı işlenirken hata: {e}")
    
    async def handle_bot_reply(self, event):
        """Bot yanıtlarını işle"""
        try:
            raw = event.raw_text
            
            # "❌ Eşleşme bulunamadı" mesajını kontrol et
            if "❌ Eşleşme bulunamadı" in raw or "Eşleşme bulunamadı" in raw:
                # TC numarasını bul (mesajda veya pending'den)
                tc_match = re.search(r"(\d{11})", raw)
                if tc_match:
                    tc = tc_match.group(1)
                    origin = self.pending.pop(tc, None)
                    
                    if origin:
                        await self.client.send_message(origin, "❌ Eşleşme bulunamadı")
                        self.logger.info(f"Eşleşme bulunamadı yanıtı gönderildi → Grup {origin}")
                        return
                
                # Pending'deki son TC için kontrol (eğer mesajda TC yoksa)
                if self.pending:
                    # Son eklenen TC'yi al
                    tc = list(self.pending.keys())[-1]
                    origin = self.pending.pop(tc, None)
                    
                    if origin:
                        await self.client.send_message(origin, "❌ Eşleşme bulunamadı")
                        self.logger.info(f"Eşleşme bulunamadı yanıtı gönderildi → Grup {origin}")
                        return
            
            # Normal sorgu sonucu işleme
            match = re.search(r"Kimlik No:\s*(\d{11})", raw)
            
            if not match:
                return
            
            tc = match.group(1)
            origin = self.pending.pop(tc, None)
            
            if not origin:
                self.logger.warning(f"Beklenmeyen TC yanıtı: {tc[:3]}***")
                return
            
            # Veriyi işle
            lines = [l.strip() for l in raw.splitlines() if l.strip() and "SORGU SONUCU" not in l]
            output, data = [], {}
            
            for line in lines:
                line = self.strip_prefix(line)
                
                if line.startswith("Anne:"):
                    name = line.split(":",1)[1].split("-")[0].strip()
                    data["Anne"] = self.clean_field(name)
                    output.append(f"👩 Anne: {data['Anne']}")
                    
                elif line.startswith("Baba:"):
                    name = line.split(":",1)[1].split("-")[0].strip()
                    data["Baba"] = self.clean_field(name)
                    output.append(f"👨 Baba: {data['Baba']}")
                    
                elif ":" in line:
                    key, val = [self.clean_field(x) for x in line.split(":",1)]
                    data[key] = val
                    
                    # Emoji ekle
                    emoji = self.get_field_emoji(key)
                    output.append(f"{emoji} {key}: {val}")
            
            if not output:
                await self.client.send_message(origin, "❌ Sorgu sonucu işlenemedi")
                return
            
            # Mesajı gönder
            message_text = "📋 **TC Kimlik Sorgu Sonucu**\n\n" + "\n".join(output)
            buttons = [[Button.inline(f"📋 {k}", data=f"copy:{k}:{v}")] for k,v in data.items()]
            
            await self.client.send_message(origin, message_text, buttons=buttons)
            self.logger.info(f"Yanıt gönderildi → Grup {origin}")
            
        except Exception as e:
            self.logger.error(f"Bot yanıtı işlenirken hata: {e}")
    
    async def handle_callback_query(self, event):
        """Callback query'leri işle"""
        try:
            data_parts = event.data.decode().split(":",2)
            if len(data_parts) != 3:
                return
                
            _, field, value = data_parts
            await event.answer(f"✅ Kopyalandı: {value}", alert=True)
            self.logger.debug(f"Callback işlendi: {field}")
            
        except Exception as e:
            self.logger.error(f"Callback işlenirken hata: {e}")
    
    def clean_field(self, text: str) -> str:
        """Alanları temizle"""
        return re.sub(r"\([^)]*\)", "", text).strip()
    
    def strip_prefix(self, text: str) -> str:
        """Başlangıç sembollerini temizle"""
        return re.sub(r'^[^\wÇŞĞÜÖİçşğüöı]+', '', text).strip()
    
    def get_field_emoji(self, field: str) -> str:
        """Alan için emoji döndür"""
        emoji_map = {
            "Ad": "👤",
            "Soyad": "👤",
            "Doğum Tarihi": "📅",
            "Doğum Yeri": "📍",
            "Cinsiyet": "⚧",
            "Medeni Hal": "💑",
            "Nüfus İl": "🏙",
            "Nüfus İlçe": "🏘",
            "Kimlik No": "🆔"
        }
        return emoji_map.get(field, "📝")
    
    async def mevcut_grup_listesi_al(self):
        """config.py'dan mevcut grup listesini al"""
        try:
            with open('config.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            for line in content.split('\n'):
                if 'GROUP_IDS_STR = os.getenv' in line and 'GROUP_IDS' in line:
                    # Satırı daha güvenli şekilde parse et
                    parts = line.split("'")
                    if len(parts) >= 3:
                        grup_str = parts[-2]  # Son tırnak içindeki değer
                        return [int(x.strip()) for x in grup_str.split(',') if x.strip() and x.strip().lstrip('-').isdigit()]
            
            return self.config.GROUP_IDS
        except Exception as e:
            self.logger.error(f"Grup listesi okunamadı: {e}")
            return self.config.GROUP_IDS
    
    async def yeni_grup_tara(self):
        """Yeni grupları tara ve çıkılan grupları tespit et"""
        try:
            mevcut_gruplar = await self.mevcut_grup_listesi_al()
            dialogs = await self.client.get_dialogs()
            
            # Mevcut aktif grupları topla
            aktif_gruplar = []
            yeni_gruplar = []
            
            for dialog in dialogs:
                entity = dialog.entity
                
                # Grup ve kanal kontrolü
                if hasattr(entity, 'id') and (dialog.is_group or dialog.is_channel):
                    # Broadcast kanalları (tek yönlü) atla
                    if hasattr(entity, 'broadcast') and entity.broadcast:
                        continue
                    
                    grup_id = dialog.id
                    aktif_gruplar.append(grup_id)
                    
                    # Yeni grup mu?
                    if grup_id not in mevcut_gruplar:
                        grup_adi = getattr(entity, 'title', 'Bilinmeyen Grup')
                        yeni_gruplar.append({
                            'id': grup_id,
                            'title': grup_adi,
                            'type': 'Süper Grup' if dialog.is_channel else 'Normal Grup'
                        })
            
            # Çıkılan grupları tespit et
            cikilan_gruplar = []
            for grup_id in mevcut_gruplar:
                if grup_id not in aktif_gruplar:
                    cikilan_gruplar.append(grup_id)
            
            return yeni_gruplar, cikilan_gruplar
            
        except Exception as e:
            self.logger.error(f"Grup tarama hatası: {e}")
            return [], []
    
    async def config_guncelle(self, yeni_grup_listesi):
        """config.py'ı güncelle"""
        try:
            with open('config.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'GROUP_IDS_STR = os.getenv' in line:
                    yeni_liste_str = ','.join(map(str, yeni_grup_listesi))
                    lines[i] = f"    GROUP_IDS_STR = os.getenv('GROUP_IDS', '{yeni_liste_str}')"
                    break
            
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Config güncelleme hatası: {e}")
            return False
    
    async def grup_monitoring_gorevi(self):
        """Arka planda grup monitoring görevi"""
        while self.grup_monitoring_aktif:
            try:
                await asyncio.sleep(self.grup_kontrol_suresi)
                
                yeni_gruplar, cikilan_gruplar = await self.yeni_grup_tara()
                degisiklik_var = False
                
                # Yeni gruplar varsa ekle
                if yeni_gruplar:
                    self.logger.info(f"🆕 {len(yeni_gruplar)} yeni grup otomatik tespit edildi:")
                    
                    for grup in yeni_gruplar:
                        self.logger.info(f"   • {grup['title']} (ID: {grup['id']})")
                    
                    degisiklik_var = True
                
                # Çıkılan gruplar varsa kaldır
                if cikilan_gruplar:
                    self.logger.info(f"🚫 {len(cikilan_gruplar)} grup çıkıldı, sistemden kaldırılıyor:")
                    
                    for grup_id in cikilan_gruplar:
                        self.logger.info(f"   • Grup ID: {grup_id}")
                    
                    degisiklik_var = True
                
                # Değişiklik varsa config'i güncelle
                if degisiklik_var:
                    mevcut_gruplar = await self.mevcut_grup_listesi_al()
                    
                    # Yeni grupları ekle
                    if yeni_gruplar:
                        yeni_grup_idleri = [grup['id'] for grup in yeni_gruplar]
                        mevcut_gruplar.extend(yeni_grup_idleri)
                    
                    # Çıkılan grupları kaldır
                    if cikilan_gruplar:
                        mevcut_gruplar = [gid for gid in mevcut_gruplar if gid not in cikilan_gruplar]
                    
                    # Tekrar eden ID'leri temizle
                    guncel_liste = list(set(mevcut_gruplar))
                    
                    if await self.config_guncelle(guncel_liste):
                        self.logger.info("✅ Grup listesi otomatik olarak güncellendi")
                        self.logger.info("🔄 3 saniye sonra konfigürasyon yeniden yüklenecek")
                        
                        # Konfigürasyonu yeniden yükle
                        await asyncio.sleep(3)
                        self.config = Config()
                        self.logger.info(f"📢 Artık {len(self.config.GROUP_IDS)} grup dinleniyor")
                
            except Exception as e:
                self.logger.error(f"Grup monitoring hatası: {e}")
                await asyncio.sleep(15)  # Hata durumunda biraz daha uzun bekle
    
    async def start(self):
        """Userbot'u başlat"""
        reconnect_attempts = 0
        
        while True:
            try:
                await self.client.start()
                self.logger.info("🚀 Userbot başarıyla başlatıldı")
                self.logger.info(f"📢 {len(self.config.GROUP_IDS)} grup dinleniyor")
                
                # Otomatik grup monitoring'i arka planda başlat
                monitoring_task = asyncio.create_task(self.grup_monitoring_gorevi())
                self.logger.info("🔍 Otomatik grup monitoring başlatıldı (15 saniyede bir kontrol)")
                
                # Bağlantı sürdürme
                await self.client.run_until_disconnected()
                
            except AuthKeyUnregisteredError:
                self.logger.error("❌ Telegram oturumu geçersiz! Yeniden giriş yapın")
                break
                
            except SessionPasswordNeededError:
                self.logger.error("❌ İki faktörlü kimlik doğrulama gerekli!")
                break
                
            except OSError as e:
                reconnect_attempts += 1
                
                if reconnect_attempts > self.config.RECONNECT_ATTEMPTS:
                    self.logger.error(f"❌ Maksimum yeniden bağlanma denemesi aşıldı: {e}")
                    break
                
                wait_time = self.config.RECONNECT_DELAY * reconnect_attempts
                self.logger.warning(f"🔄 Bağlantı hatası, {wait_time}s bekleyip tekrar denenecek: {e}")
                await asyncio.sleep(wait_time)
                
            except FloodWaitError as e:
                self.logger.warning(f"⏳ Flood wait: {e.seconds}s bekleniyor")
                await asyncio.sleep(e.seconds)
                
            except Exception as e:
                self.logger.error(f"❌ Beklenmeyen hata: {e}")
                await asyncio.sleep(self.config.RECONNECT_DELAY)
    
    async def stop(self):
        """Userbot'u durdur"""
        self.grup_monitoring_aktif = False  # Monitoring'i durdur
        if self.client.is_connected():
            await self.client.disconnect()
            self.logger.info("🛑 Userbot durduruldu")
