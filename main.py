#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import tweepy
from openai import OpenAI
from threading import Thread

# ========= AYARLAR VE LOGLAMA =========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Render hafıza dosyaları
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

class NasreddinHocaBot:
    def __init__(self):
        self.last_mention_id = self.load_data(ID_FILE)
        self.last_btc_price = self.load_data(PRICE_FILE, is_float=True)
        self.me = None
        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüde: @{self.me.username}")
        except Exception as e:
            logger.error(f"Twitter Giriş Hatası: {e}")

    def load_data(self, filename, is_float=False):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    val = f.read().strip()
                    return float(val) if is_float else int(val)
            except: return None
        return None

    def save_data(self, filename, value):
        try:
            with open(filename, "w") as f:
                f.write(str(value))
        except: pass

    def get_market_data(self):
        """Binance'den BTC fiyatını çeker."""
        try:
            res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
            price = float(res['price'])
            return price
        except: return None

    def check_market_movement(self):
        """%5 hareket kontrolü."""
        current_price = self.get_market_data()
        if not current_price: return

        if self.last_btc_price:
            change = ((current_price - self.last_btc_price) / self.last_btc_price) * 100
            if abs(change) >= 5.0:
                yon = "fırladı" if change > 0 else "çakıldı"
                prompt = f"BTC fiyatı %{change:.2f} {yon}! Şu an {current_price} USD. Nasreddin Hoca olarak halka bir ibretlik yorum yap."
                self.post_tweet(prompt)
                self.save_data(PRICE_FILE, current_price)
                self.last_btc_price = current_price
        else:
            self.save_data(PRICE_FILE, current_price)
            self.last_btc_price = current_price

    def post_tweet(self, prompt):
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
            )
            text = response.choices[0].message.content.strip()
            twitter.create_tweet(text=text)
            logger.info(f"Tweet Atıldı: {text}")
        except Exception as e:
            logger.error(f"Tweet Hatası: {e}")

    def check_mentions(self):
        """Mentionları kontrol eder ve yanıtlar."""
        if not self.me: return
        try:
            # 1. Kendi son yanıtlarımızı çek (Mükerrer yanıt engeli)
            my_replies = twitter.get_users_tweets(id=self.me.id, max_results=20, tweet_fields=["referenced_tweets"])
            answered_ids = []
            if my_replies and my_replies.data:
                for r in my_replies.data:
                    if r.referenced_tweets:
                        for ref in r.referenced_tweets:
                            if ref.type == "replied_to":
                                answered_ids.append(ref.id)

            # 2. Gelen mentionları çek
            params = {"id": self.me.id, "max_results": 10}
            if self.last_mention_id:
                params["since_id"] = self.last_mention_id

            mentions = twitter.get_users_mentions(**params)
            if not mentions or not mentions.data: return

            for tweet in sorted(mentions.data, key=lambda x: x.id):
                if tweet.id in answered_ids:
                    continue

                logger.info(f"Yanıtlanıyor: {tweet.text}")
                prompt = f"Kullanıcı: '{tweet.text}'. Nasreddin Hoca olarak kısa, bilgece ve komik bir cevap ver."
                
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content.strip()
                
                twitter.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                self.save_data(ID_FILE, tweet.id)
                self.last_mention_id = tweet.id
                time.sleep(5)

        except Exception as e:
            logger.error(f"Mention Hatası: {e}")

    def run(self):
        logger.info("Sistem başlatıldı...")
        while True:
            self.check_mentions()
            self.check_market_movement()
            time.sleep(60) # 1 dakikada bir kontrol

if __name__ == "__main__":
    hoca = NasreddinHocaBot()
    hoca.run()
