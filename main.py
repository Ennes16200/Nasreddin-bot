import os
import time
import requests
import json
import random
from threading import Thread

# --- AYARLAR (Environment Variables) ---
# Render veya yerel bilgisayarında bu değişkenleri tanımlamalısın
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Moltlets Bilgileri (Kayıttan sonra burayı dolduracaksın)
MOLTLETS_AGENT_ID = os.getenv("MOLTLETS_AGENT_ID")
MOLTLETS_API_KEY = os.getenv("MOLTLETS_API_KEY")

class NasreddinHocaBot:
    def __init__(self):
        self.name = "Nasreddin_Hoca_AI"
        self.bio = "Kripto dünyasında eşeğine ters binen, hem güldüren hem düşündüren bilge. Akçe peşinde değil, akıl peşinde!"
        
    # --- BÖLÜM 1: MOLTLETS KAYIT FONKSİYONU ---
    def moltlets_kayit_ol(self):
        url = "https://moltlets.world/api/manual"
        payload = {
            "name": self.name,
            "bio": self.bio,
            "personality": ["Esprili", "Bilge", "İğneleyici", "Meraklı"],
            "appearance": {
                "color": "#3498db",
                "variant": "moltlet",
                "hat": "tophat",
                "accessories": "glasses"
            }
        }
        try:
            print("🚀 Hoca Moltlets kapısına dayandı, kayıt isteği gönderiliyor...")
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                print(f"\n✅ KAYIT BAŞLATILDI!")
                print(f"🔗 ŞU LİNKE GİT VE TWITTER DOĞRULAMASI YAP: {data.get('claimUrl')}")
                print(f"🔑 CLAIM TOKEN (Sorgulama için): {data.get('claimToken')}")
                print("\n⚠️ Onay aldıktan sonra Agent ID ve API Key'i Environment Variables'a ekle!")
                return True
            else:
                print(f"❌ Kayıt hatası: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"💥 Moltlets bağlantı hatası: {e}")
        return False

    # --- BÖLÜM 2: MOLTLETS OTONOM YAŞAM DÖNGÜSÜ ---
    def moltlets_yasami(self):
        if not MOLTLETS_AGENT_ID or not MOLTLETS_API_KEY:
            print("⏳ Moltlets API anahtarları eksik. Otonom yaşam başlatılamadı.")
            return

        base_url = f"https://moltlets.world/api/agents/{MOLTLETS_AGENT_ID}/act"
        headers = {"Authorization": f"Bearer {MOLTLETS_API_KEY}", "Content-Type": "application/json"}
        
        actions = [
            {"action": "wander"},
            {"action": "chop"},
            {"action": "interact", "interactionType": "fish"},
            {"action": "emote", "emoji": "wave"}
        ]

        print("👳‍♂️ Hoca Moltlets dünyasında uyanıyor...")
        while True:
            action = random.choice(actions)
            try:
                requests.post(base_url, json=action, headers=headers, timeout=5)
                print(f"🎬 Moltlets Aksiyonu: {action['action']} yapıldı.")
            except:
                pass
            time.sleep(random.randint(5, 10)) # 5-10 saniye bekle

    # --- BÖLÜM 3: TWITTER PAYLAŞIM DÖNGÜSÜ ---
    def twitter_paylasimi(self):
        print("🐦 Twitter botu aktif hale getiriliyor...")
        # Burada senin mevcut Twitter paylaşım kodun (Tweepy vb.) çalışacak
        while True:
            print("📢 Hoca bir tweet hazırlıyor: 'Ya tutarsa?'")
            # tweet_at("Kripto gölüne maya çalmaya geldik...")
            time.sleep(3600) # Saatte bir tweet

# --- ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    hoca = NasreddinHocaBot()

    # 1. Eğer API Key yoksa kayıt olmaya çalış
    if not MOLTLETS_API_KEY:
        hoca.moltlets_kayit_ol()
        print("\n🛑 Kayıt linki yukarıda. Lütfen doğrulamayı yapıp API anahtarlarını alana kadar bekleyin.")
    else:
        # 2. API Key varsa hem Twitter'ı hem Moltlets'i aynı anda başlat (Thread kullanarak)
        print("🌟 Tüm sistemler başlatılıyor...")
        
        moltlets_thread = Thread(target=hoca.moltlets_yasami)
        twitter_thread = Thread(target=hoca.twitter_paylasimi)

        moltlets_thread.start()
        twitter_thread.start()

        moltlets_thread.join()
        twitter_thread.join()
