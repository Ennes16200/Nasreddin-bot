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

# Dosya isimleri (Render'da kalıcı hafıza için)
ID_FILE = "last_mention_id.txt"
PRICE_FILE = "last_price.txt"

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
        self.last_btc_price = self.load_last_price()
        self.me = None
        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüde: @{self.me.username} | Başlangıç Fiyatı: {self.last_btc_price}")
        except Exception as e:
            logger.error(f"Twitter Giriş Hatası: {e}")

    def load_last_id(self):
        if os.path.exists(ID_FILE):
            try:
                with open(ID_FILE, "r") as f:
                    content = f.read().strip()
                    return int(content) if content else None
            except: return None
        return None

    def save_last_id(self, tweet_id):
        try:
            with open(ID_FILE, "w") as f:
                f.write(str(tweet_id))
            self.last_mention_id = tweet_id
        except: pass

    def load_last_price(self):
        """Dosyadan son kaydedilen fiyatı okur."""
        if os.path.exists(PRICE_FILE):
            try:
                with open(PRICE_FILE, "r") as f:
                    return float(f.read().strip())
            except: return None
        return None

    def save_last_price(self, price):
        """Fiyatı dosyaya kaydeder."""
        try:
            with open(PRICE_FILE, "w") as f:
                f.write(str(price))
            self.last_btc_price = price
        except: pass

    def get_market_wisdom(self):
        """Gerçek piyasa verilerini çeker."""
        try:
            btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=15).json()
            price = btc_res.get('price')
            if not price: return None
            
            fng_res = requests.get("https://api.alternative.me/fng/", timeout=15).json()
            fng = fng_res.get('data', [{}])[0].get('value', "50")
            
            return {"btc": f"{float(price):,.2f}", "raw_btc": float(price), "fng": fng}
        except: return None

    def check_market_movement(self):
        """%5 ve üzeri hareketleri kontrol eder."""
        w = self.get_market_wisdom()
        if not w: return

        current_price = w['raw_btc']
        
        # Eğer hafızada fiyat yoksa, şu anki fiyatı kaydet ve çık
        if self.last_btc_price is None:
            self.save_last_price(current_price)
            return

        # Değişim oranını hesapla
        change_pct = ((current_price - self.last_btc_price) / self.last_btc_price) * 100
        
        # EŞİK DEĞERİ: %5
        threshold = 5.0

        if abs(change_pct) >= threshold:
            yon = "YÜKSELİŞ" if change_pct > 0 else "DÜŞÜŞ"
            logger.info(f"SERT HAREKET: %{change_pct:.2f} {yon}")

            prompt = (f"PİYASA ALARMI: BTC fiyatı %{change_pct:.2f} {yon} gösterdi. "
                      f"Şu anki fiyat: {w['btc']} USD. Nasreddin Hoca olarak bu duruma "
                      "esprili, bilgece ve halk ağzıyla bir yorum yaz.")

            try:
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
                )
                tweet = response.choices[0].message.content.strip()
                twitter.create_tweet(text=tweet)
                
                # Yeni fiyatı kaydet ki sürekli aynı değişim için tweet atmasın
                self.save_last_price(current_price)
                logger.info(f"Hareket Tweeti Atıldı: {tweet}")
            except Exception as e:
                logger.error(f"Hareket Tweet Hatası: {e}")

    def check_mentions(self):
        """Mentionları kontrol eder ve mükerrer yanıtı engeller."""
        if not self.me: return
        try:
            # Kendi son yanıtlarımızı kontrol et
            my_replies = twitter.get_users_tweets(id=self.me.id, max_results=40, tweet_fields=["referenced_tweets"])
            answered_ids = []
            if my_replies and my_replies.data:
                for r in my_replies.data:
                    if r.referenced_tweets:
                        for ref in r.referenced_tweets:
                            if ref.type == "replied_to":
                                answered_ids.append(ref.id)

            params = {"id": self.me.id, "max_results": 10, "tweet_fields": ["author_id"]}
            if self.last_mention_id:
                params["since_id"] = self.last_mention_id

            mentions = twitter.get_users_mentions(**params)
            if not mentions or not mentions.data: return
            
            for tweet in sorted(mentions.data, key=lambda x: x.id):
                if tweet.author_id == self.me.id or tweet.id in answered_ids:
                    self.save_last_id(tweet.id)
                    continue

                prompt = f"Kullanıcı: '{tweet.text}'. Nasreddin Hoca olarak kısa ve esprili bir cevap ver."
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content.strip()
                twitter.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                self.save_last_id(tweet.id)
                time.sleep(5)
        except Exception as e:
            logger.error(f"Mention Hatası: {e}")

    def run(self):
        """Ana döngü."""
        while True:
            self.check_mentions()
            self.check_market_movement()
            time.sleep(60) # Dakikada bir kontrol

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
