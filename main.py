#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import hashlib
import random
import tweepy
from datetime import datetime
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

# ========= AYARLAR VE LOGLAMA =========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ID_FILE = "last_mention_id.txt"
PRICE_FILE = "last_prices.json" # Çoklu coin için json

# ========= API İSTEMCİLERİ =========
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

twitter = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
)

class KriptoHocaUltimate:
    def __init__(self):
        self.last_mention_id = self.load_last_id()
        self.me = None
        # Takip listesi (Hoca'nın ana heybesi)
        self.main_coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
        # Hoca'nın Kişilik Tanımı
        self.system_prompt = (
            "Sen 13. yüzyıldan günümüze ışınlanmış Kripto Nasreddin Hoca'sın. "
            "Kripto dünyasındaki 'Moon', 'Lambo', 'HODL' gibi terimleri saçma ama komik buluyorsun. "
            "Üslubun: 'Bre evlat', 'Cemaat-i Dijital', 'İlahi', 'Ya tutarsa' eksenli. "
            "Zeki, hafif fırlama, asla yatırım tavsiyesi vermeyen bir filozofsun. "
            "Eğer biri saçma bir coin sorarsa 'Kazan öldü' veya 'Eşeği kaybettik' fıkralarıyla cevap ver."
        )

        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüde: @{self.me.username}")
        except Exception as e:
            logger.error(f"Twitter Giriş Hatası: {e}")

    # --- VERİ VE HAFIZA ---
    def load_last_id(self):
        if os.path.exists(ID_FILE):
            try:
                with open(ID_FILE, "r") as f: return int(f.read().strip())
            except: return None
        return None

    def save_last_id(self, tweet_id):
        with open(ID_FILE, "w") as f: f.write(str(tweet_id))

    def get_coin_price(self, symbol):
        """Binance üzerinden dinamik fiyat çeker."""
        try:
            symbol = symbol.upper().replace("$", "")
            if not symbol.endswith("USDT"): symbol += "USDT"
            res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=10).json()
            return float(res['price'])
        except: return None

    # --- ZEKA VE MİZAH MODÜLLERİ ---
    def get_maya_score(self, coin_name):
        """Herhangi bir coin için 'Ya Tutarsa' skoru üretir."""
        seed = f"{coin_name.upper()}{datetime.now().strftime('%Y%m%d')}"
        score = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 100
        
        price = self.get_coin_price(coin_name)
        price_info = f" (Fiyatı: {price} USDT)" if price else " (Pazarda fiyatını bulamadım!)"

        prompt = (
            f"Kullanıcı {coin_name} coini için 'maya tutar mı' diye sordu. "
            f"Skor: %{score}. Mevcut durum: {price_info}. "
            "Nasreddin Hoca olarak bu skoru 'Ya tutarsa' mantığıyla esprili yorumla."
        )
        
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def check_market_shock(self):
        """Piyasa sert hareketlerini kontrol eder."""
        for coin in self.main_coins:
            price = self.get_coin_price(coin)
            if price:
                # Burada fiyat değişim mantığını (last_price karşılaştırması) ekleyebilirsin.
                pass

    # --- RUTİN ETKİNLİKLER ---
    def weekly_sermon(self):
        """Pazar Akşamı Kripto Hutbesi."""
        prompt = "Pazar akşamı oldu. Haftalık Kripto Hutbesi vaktidir. Cemaate bilgece ve komik bir kapanış konuşması yap."
        res = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}]
        )
        twitter.create_tweet(text=f"📜 HAFTALIK HUTBE:\n\n{res.choices[0].message.content.strip()[:250]}")

    def reply_to_mentions(self):
        """Gelen mentionları zekice yanıtlar."""
        if not self.me: return
        try:
            mentions = twitter.get_users_mentions(id=self.me.id, since_id=self.last_mention_id)
            if not mentions or not mentions.data: return

            for tweet in sorted(mentions.data, key=lambda x: x.id):
                if tweet.author_id == self.me.id: continue
                
                txt = tweet.text.upper()
                # ZEKİ ANALİZ: Coin mi soruyor?
                if any(w in txt for w in [" NE OLUR", "MAYA", "ALINIR MI", "SKOR", "NASIL"]):
                    words = tweet.text.split()
                    # Sembol yakala ($BTC veya BTC gibi)
                    coin = next((w for w in words if w.startswith('$') or w.isupper()), "bu coin")
                    reply = self.get_maya_score(coin)
                else:
                    # Normal Sohbet
                    res = client_ai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": tweet.text}]
                    )
                    reply = res.choices[0].message.content.strip()

                twitter.create_tweet(text=reply[:280], in_reply_to_tweet_id=tweet.id)
                self.save_last_id(tweet.id)
                time.sleep(5)
        except Exception as e:
            logger.error(f"Mention Hatası: {e}")

    def run(self):
        scheduler = BackgroundScheduler()
        # Her Pazar 21:00'de Hutbe
        scheduler.add_job(self.weekly_sermon, 'cron', day_of_week='sun', hour=21, minute=0)
        # Her Sabah 09:00'da Selam
        scheduler.add_job(lambda: twitter.create_tweet(text="Sabah-ı şerifleriniz hayrolsun cemaat-i kripto! Eşeği doyurduk, grafikleri açtık. Ya tutarsa!"), 'cron', hour=9, minute=0)
        scheduler.start()

        while True:
            self.reply_to_mentions()
            time.sleep(60)

if __name__ == "__main__":
    hoca = KriptoHocaUltimate()
    hoca.run()
        
