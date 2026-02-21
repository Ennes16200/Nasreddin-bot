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

# Render'da kalıcı hafıza için dosya adı (Disk bağlıysa yol güncellenebilir)
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
        """En son yanıtlanan tweet ID'sini kaydet."""
        try:
            with open(ID_FILE, "w") as f:
                f.write(str(tweet_id))
            self.last_mention_id = tweet_id
        except Exception as e:
            logger.error(f"ID kaydetme hatası: {e}")

    def get_market_wisdom(self):
        """Gerçek piyasa verilerini çeker."""
        try:
            # BTC Fiyatı
            btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=15).json()
            price = btc_res.get('price')
            
            if not price or float(price) <= 0:
                return None

            # Korku ve Açgözlülük
            fng_res = requests.get("https://api.alternative.me/fng/", timeout=15).json()
            fng = fng_res.get('data', [{}])[0].get('value', "50")

            return {
                "btc": f"{float(price):,.2f}", 
                "fng": fng
            }
        except Exception as e:
            logger.error(f"Veri çekme hatası: {e}")
            return None

    def generate_and_post(self):
        """Genel piyasa yorumu tweeti atar."""
        w = self.get_market_wisdom()
        if not w: return 

        prompt = (f"VERİLER: BTC {w['btc']} USD, Korku Endeksi {w['fng']}/100. "
                  "Nasreddin Hoca olarak bu verilere dayanarak esprili bir Türkçe tweet yaz.")
        
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
            )
            tweet = response.choices[0].message.content.strip()
            twitter.create_tweet(text=tweet)
            logger.info(f"Genel Tweet Atıldı: {tweet}")
        except Exception as e:
            logger.error(f"Tweet Hatası: {e}")

    def check_mentions(self):
        """Mentionları kontrol eder ve sadece yanıtlanmamış olanları yanıtlar."""
        if not self.me: return
        try:
            # 1. Kendi son yanıtlarımızı kontrol et (Mükerrer yanıtı engellemek için en kesin yol)
            my_replies = twitter.get_users_tweets(
                id=self.me.id, 
                max_results=40, 
                tweet_fields=["referenced_tweets"]
            )
            
            answered_ids = []
            if my_replies and my_replies.data:
                for r in my_replies.data:
                    if r.referenced_tweets:
                        for ref in r.referenced_tweets:
                            if ref.type == "replied_to":
                                answered_ids.append(ref.id)

            # 2. Gelen mentionları çek
            params = {"id": self.me.id, "max_results": 10, "tweet_fields": ["author_id"]}
            if self.last_mention_id:
                params["since_id"] = self.last_mention_id

            mentions = twitter.get_users_mentions(**params)
            if not mentions or not mentions.data: return
            
            # Eskiden yeniye sırala
            sorted_mentions = sorted(mentions.data, key=lambda x: x.id)
            
            for tweet in sorted_mentions:
                # Kendi tweetimiz mi?
                if tweet.author_id == self.me.id:
                    continue
                
                # Zaten yanıtladık mı? (Kendi profilimizden kontrol)
                if tweet.id in answered_ids:
                    logger.info(f"Atlanıyor (Zaten yanıtlanmış): {tweet.id}")
                    self.save_last_id(tweet.id)
                    continue

                logger.info(f"Yeni ve yanıtsız mention tespit edildi: {tweet.id}")

                prompt = f"Kullanıcı: '{tweet.text}'. Nasreddin Hoca olarak kısa, bilgece ve esprili bir cevap ver."
                
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
                
                # ID'yi güncelle
                self.save_last_id(tweet.id)
                
                logger.info(f"Yanıt gönderildi: {tweet.id} -> {reply}")
                time.sleep(5) 
                
        except Exception as e:
            logger.error(f"Mention kontrol hatası: {e}")

    def run(self):
        """Ana döngü."""
        last_tweet_time = 0
        while True:
            self.check_mentions()
            
            now = time.time()
            # 4 saatte bir piyasa yorumu
            if now - last_tweet_time > 14400:
                self.generate_and_post()
                last_tweet_time = now
            
            time.sleep(60) # Dakikada bir kontrol

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
