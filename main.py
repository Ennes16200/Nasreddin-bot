#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import tweepy
from openai import OpenAI

# ========= AYARLAR VE LOGLAMA =========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Render'da kalıcı hafıza için dosya adı
ID_FILE = "last_mention_id.txt"

# ========= API İSTEMCİLERİ =========
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

twitter = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
)

class KriptoHocaAgent:
    def __init__(self):
        self.last_mention_id = self.load_last_id()
        self.me = None
        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüde: @{self.me.username} | Başlangıç ID: {self.last_mention_id}")
        except Exception as e:
            logger.error(f"Twitter Giriş Hatası: {e}")

    def load_last_id(self):
        """Dosyadan en son yanıtlanan tweet ID'sini okur."""
        if os.path.exists(ID_FILE):
            try:
                with open(ID_FILE, "r") as f:
                    content = f.read().strip()
                    return int(content) if content else None
            except Exception as e:
                logger.error(f"ID dosyası okuma hatası: {e}")
        return None

    def save_last_id(self, tweet_id):
        """En son yanıtlanan tweet ID'sini dosyaya kaydet."""
        try:
            with open(ID_FILE, "w") as f:
                f.write(str(tweet_id))
            self.last_mention_id = tweet_id
        except Exception as e:
            logger.error(f"ID kaydetme hatası: {e}")

    def get_market_wisdom(self):
        """Gerçek piyasa verilerini çeker. Hata varsa None döner."""
        try:
            # 1. BTC Fiyatı (Binance)
            btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=15).json()
            price = btc_res.get('price')
            
            if not price or float(price) <= 0:
                logger.warning("BTC fiyatı alınamadı, uydurma bilgi vermemek için işlem iptal.")
                return None

            # 2. Korku ve Açgözlülük Endeksi
            fng_res = requests.get("https://api.alternative.me/fng/", timeout=15).json()
            fng = fng_res.get('data', [{}])[0].get('value', "50")

            # 3. Trend Coinler
            news_res = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=15).json()
            trending = [t['item']['symbol'] for t in news_res.get('coins', [])[:3]]
            
            return {
                "btc": f"{float(price):,.2f}", 
                "fng": fng, 
                "news": ", ".join(trending),
                "whale": "Büyükler sessizce bekliyor" if float(fng) < 40 else "Sular ısınıyor"
            }
        except Exception as e:
            logger.error(f"Veri çekme hatası: {e}")
            return None

    def generate_and_post(self):
        """Piyasa yorumu tweeti atar."""
        w = self.get_market_wisdom()
        if not w: return 

        prompt = (f"VERİLER: BTC {w['btc']} USD, Korku {w['fng']}/100, Trendler: {w['news']}. "
                  "TALİMAT: Bu rakamları asla değiştirme. Nasreddin Hoca olarak bilgece ve iğneleyici "
                  "bir Türkçe tweet yaz. Kendi kafandan fiyat uydurma. (Max 240 karakter).")
        
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sen verilere sadık kalan Nasreddin Hoca'sın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6
            )
            tweet = response.choices[0].message.content.strip()
            twitter.create_tweet(text=tweet)
            logger.info(f"Tweet Atıldı: {tweet}")
        except Exception as e:
            logger.error(f"Tweet Hatası: {e}")

    def check_mentions(self):
        """Mentionları kontrol eder ve sadece yenileri yanıtlar."""
        if not self.me: return
        try:
            params = {
                "id": self.me.id, 
                "max_results": 10,
                "tweet_fields": ["author_id"]
            }
            # Sadece son kaldığımız ID'den sonrasını iste
            if self.last_mention_id:
                params["since_id"] = self.last_mention_id

            mentions = twitter.get_users_mentions(**params)
            
            if not mentions or not mentions.data: 
                return
            
            # Tweetleri eskiden yeniye doğru işle (ID sırasına göre)
            sorted_mentions = sorted(mentions.data, key=lambda x: x.id)
            
            for tweet in sorted_mentions:
                # Kendi tweetlerimize cevap vermeyelim
                if tweet.author_id == self.me.id:
                    continue

                # Çift kontrol: Eğer ID zaten işlendiyse atla
                if self.last_mention_id and tweet.id <= self.last_mention_id:
                    continue

                logger.info(f"Yeni mention: {tweet.id} - İçerik: {tweet.text}")

                prompt = f"Kullanıcı şunu sordu/dedi: '{tweet.text}'. Nasreddin Hoca olarak kısa, bilgece ve esprili bir cevap ver."
                
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Sen Nasreddin Hoca'sın. Kısa ve öz cevap verirsin."},
                        {"role": "user", "content": prompt}
                    ]
                )
                reply = response.choices[0].message.content.strip()
                
                # Yanıtı gönder
                twitter.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                
                # ID'yi güncelle ve dosyaya yaz
                self.save_last_id(tweet.id)
                
                logger.info(f"Yanıtlandı: {tweet.id} -> {reply}")
                time.sleep(5) # Spam koruması
                
        except Exception as e:
            logger.error(f"Mention kontrol hatası: {e}")

    def run(self):
        """Ana döngü."""
        last_tweet_time = 0
        while True:
            self.check_mentions()
            
            now = time.time()
            # 4 saatte bir piyasa yorumu at
            if now - last_tweet_time > 14400:
                self.generate_and_post()
                last_tweet_time = now
            
            time.sleep(60) # Dakikada bir mention kontrolü

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
