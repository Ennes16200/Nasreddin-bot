import os
import time
import logging
import requests
import tweepy
from openai import OpenAI

# --- LOGLAMA AYARLARI ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- API BAĞLANTILARI (Environment Variables) ---
# Render üzerinde bu isimlerle tanımladığından emin ol!
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# OpenAI İstemcisi
client = OpenAI(api_key=OPENAI_API_KEY)

def moltlets_dunyasına_gir(ajan_ismi, hoca_biosu):
    """Moltlets API'sine bağlanır, hata alırsa botu durdurmaz."""
    url = "https://moltlets.world/api/spawn"
    payload = {"name": ajan_ismi, "bio": hoca_biosu}
    
    try:
        logger.info(f"--- {ajan_ismi} için Moltlets kapısı çalınıyor... ---")
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "claim_url" in data:
                print(f"\n✅ MOLTLETS BAŞARILI! Linkin: {data['claim_url']}\n")
                return True
        else:
            # Destan gibi hata almamak için sadece durum kodunu yazdırıyoruz
            logger.warning(f"⚠️ Moltlets şu an yanıt vermiyor (Hata Kodu: {response.status_code}). Twitter moduna geçiliyor...")
    except Exception as e:
        logger.error(f"Moltlets bağlantı hatası: {e}")
    return False

class NasreddinHocaBot:
    def __init__(self):
        # Twitter API v2 Bağlantısı
        self.twitter_client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        self.bot_id = None
        try:
            me = self.twitter_client.get_me()
            self.bot_id = me.data.id
            logger.info(f"Bot aktif! İsim: {me.data.name}")
        except Exception as e:
            logger.error(f"Twitter bağlantı hatası: {e}")

    def ai_yanit_olustur(self, tweet_metni, kullanici_adi):
        """Nasreddin Hoca kişiliğiyle yanıt üretir."""
        sistem_mesaji = (
            "Sen 21. yüzyılda yaşayan, kripto paralardan anlayan Nasreddin Hoca'sın. "
            "Esprili, bilge ve hafif iğneleyici bir dil kullan. Yanıtların kısa ve öz olsun. "
            "Asla 'Nasreddin Hoca:' gibi ön ekler kullanma. Doğrudan söze gir."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sistem_mesaji},
                    {"role": "user", "content": f"@{kullanici_adi} şunu dedi: {tweet_metni}. Ona bir hoca cevabı ver."}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI Yanıt Hatası: {e}")
            return "Evlat, zihnim biraz karışık, sonra gel hele..."

    def mentionlari_kontrol_et(self):
        """Gelen mentionları kontrol eder ve yanıtlar."""
        try:
            mentions = self.twitter_client.get_users_mentions(id=self.bot_id)
            if mentions.data:
                for tweet in mentions.data:
                    # Burada normalde 'since_id' kontrolü yapılır ama basitlik için geçiyoruz
                    logger.info(f"Yeni tweet yakalandı: {tweet.text}")
                    # Yanıt verme mantığı buraya eklenebilir
        except Exception as e:
            logger.error(f"Mention kontrol hatası: {e}")

    def run(self):
        """Botu ana döngüye sokar."""
        logger.info("Nasreddin Hoca devriye geziyor...")
        while True:
            self.mentionlari_kontrol_et()
            time.sleep(60) # 1 dakikada bir kontrol et

if __name__ == "__main__":
    # 1. Önce Moltlets dünyasına girmeyi dene (Hata alsa da devam eder)
    moltlets_dunyasına_gir(
        "Nasreddin Hoca", 
        "Kripto dünyasında eşeğine ters binen, hem güldüren hem düşündüren bilge."
    )
    
    # 2. Sonra Twitter botunu başlat
    bot = NasreddinHocaBot()
    if bot.bot_id:
        bot.run()
    else:
        logger.error("Bot başlatılamadı, API anahtarlarını kontrol et!")
