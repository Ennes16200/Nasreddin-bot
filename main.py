import os
import time
import requests
import json
import random
from threading import Thread

# --- AYARLAR (Environment Variables) ---
# Render veya yerel bilgisayarınızda bu değişkenleri tanımlayın
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Moltlets Bilgileri (Kayıttan sonra Render'a ekleyeceksiniz)
MOLTLETS_AGENT_ID = os.getenv("MOLTLETS_AGENT_ID")
MOLTLETS_API_KEY = os.getenv("MOLTLETS_API_KEY")

class NasreddinHocaBot:
    def __init__(self):
        # İsimde boşluk ve özel karakter olmamasına dikkat (Sunucu hatasını önler)
        self.agent_name = "NasreddinHocaAI" 
        self.bio = "Kripto dunyasinda esegine ters binen, hem gulduren hem dusunduren bilge."
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })

    # --- BÖLÜM 1: MOLTLETS KAYIT (MANUAL SPAWN) ---
    def moltlets_kayit_ol(self):
        url = "https://moltlets.world/api/manual"
        payload = {
            "name": self.agent_name,
            "bio": self.bio,
            "personality": ["Funny", "Wise", "Sarcastic", "Curious"],
            "appearance": {
                "color": "#3498db",
                "variant": "moltlet",
                "hat": "tophat",
                "accessories": "glasses"
            }
        }
        
        try:
            print(f"🚀 {self.agent_name} Moltlets kapısını çalıyor...")
            # data=json.dumps kullanarak en saf JSON formatını gönderiyoruz
            res = self.session.post(url, data=json.dumps(payload), timeout=20)
            
            if res.status_code == 200 and res.text.strip():
                data = res.json()
                print("\n" + "="*40)
                print("✅ BAŞARILI! HOCA DÜNYAYA ADIM ATTI.")
                print(f"🔗 ŞİMDİ BU LİNKE GİT: {data.get('claimUrl')}")
                print(f"🔑 CLAIM TOKEN (Sakla): {data.get('claimToken')}")
                print("="*40)
                print("\n⚠️ Onay aldıktan sonra Agent ID ve API Key'i Render ayarlarına ekle!")
                return True
            else:
                print(f"❌ Sunucu Yanıt Vermedi veya Hata Döndü (Kod: {res.status_code})")
                print(f"Ham Yanıt: {res.text}")
        except Exception as e:
            print(f"💥 Bağlantı hatası: {e}")
        return False

    # --- BÖLÜM 2: MOLTLETS OTONOM YAŞAM ---
    def moltlets_yasami(self):
        if not MOLTLETS_AGENT_ID or not MOLTLETS_API_KEY:
            print("⏳ Moltlets API anahtarları bekleniyor... Otonom yaşam askıda.")
            return

        base_url = f"https://moltlets.world/api/agents/{MOLTLETS_AGENT_ID}/act"
        headers = {"Authorization": f"Bearer {MOLTLETS_API_KEY}"}
        
        actions = [
            {"action": "wander"},
            {"action": "chop"},
            {"action": "interact", "interactionType": "fish"},
            {"action": "emote", "emoji": "wave"}
        ]

        print(f"👳‍♂️ Hoca Moltlets dünyasında (ID: {MOLTLETS_AGENT_ID}) aktif!")
        while True:
            action = random.choice(actions)
            try:
                res = self.session.post(base_url, json=action, headers=headers, timeout=10)
                print(f"🎬 Aksiyon: {action['action']} | Durum: {res.status_code}")
            except Exception as e:
                print(f"⚠️ Aksiyon hatası: {e}")
            
            # Sunucuyu yormamak için 10-20 saniye arası rastgele bekleme
            time.sleep(random.randint(10, 20))

    # --- BÖLÜM 3: TWITTER DÖNGÜSÜ ---
    def twitter_dongusu(self):
        print("🐦 Twitter botu arka planda hazır bekliyor...")
        while True:
            # Buraya mevcut tweet atma fonksiyonunu entegre edebilirsin
            # print("📢 Tweet atılıyor...")
            time.sleep(3600) # Saatte bir kontrol

# --- ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    hoca = NasreddinHocaBot()

    # Eğer API Key yoksa kayıt modunda başla
    if not MOLTLETS_API_KEY:
        hoca.moltlets_kayit_ol()
        print("\n💡 Kayıt işlemini tamamlayıp API anahtarlarını alana kadar bekleyin.")
    else:
        # API Key varsa hem Twitter hem Moltlets aynı anda çalışsın
        print("🌟 Tüm sistemler devreye alınıyor...")
        
        t1 = Thread(target=hoca.moltlets_yasami)
        t2 = Thread(target=hoca.twitter_dongusu)

        t1.start()
        t2.start()

        t1.join()
        t2.join()
