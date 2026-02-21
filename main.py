#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import tweepy
from datetime import datetime
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

# ========= AYARLAR VE LOGLAMA =========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class KriptoHocaUltimate:
    def __init__(self):
        self.last_mention_id = self.load_last_id()
        self.monitored_coins = ["BTCUSDT", "ETHUSDT"]
        self.me = None
        
        # Hoca'nın Karakter Tanımı
        self.system_prompt = (
            "Sen 13. yüzyıldan gelen Kripto Nasreddin Hoca'sın. "
            "Üslubun: 'Bre evlat', 'Cemaat-i Kripto', 'Ya tutarsa' eksenli, "
            "Osmanlıca/Eski Türkçe kelimelerle süslü ama güncel kripto jargonuna hakim. "
            "Haftalık Hutbe verirken bilge, hafif sitemkar ama umut dolu konuş."
        )

        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüye Çıktı: @{self.me.username}")
        except Exception as e:
            logger.error(f"Twitter Giriş Hatası: {e}")

    def load_last_id(self):
        if os.path.exists(ID_FILE):
            try:
                with open(ID_FILE, "r") as f: return int(f.read().strip())
            except: return None
        return None

    def save_last_id(self, tweet_id):
        with open(ID_FILE, "w") as f: f.write(str(tweet_id))

    def get_market_summary(self):
        """Hutbe için haftalık genel havayı çeker."""
        try:
            fng = requests.get("https://api.alternative.me/fng/").json()
            score = fng['data'][0]['value']
            status = fng['data'][0]['value_classification']
            
            btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            price = float(btc_res['price'])
            
            return f"BTC: {price:,.2f} USD, Korku Endeksi: {score} ({status})"
        except: return "Piyasa karışık, sular bulanık..."

    # --- YENİ: HAFTALIK KRİPTO HUTBESİ ---
    def weekly_sermon(self):
        """Pazar akşamları haftalık kapanış değerlendirmesi yapar."""
        market_info = self.get_market_summary()
        
        prompt = (
            f"Bugün Pazar, haftalık kapanış vakti. Piyasa durumu: {market_info}. "
            "Cemaat-i Kripto'ya 'Haftalık Kripto Hutbesi' başlığıyla seslen. "
            "Haftanın yorgunluğunu alan, hem güldüren hem düşündüren uzunca bir tweet yaz. "
            "Eşeğine ters binmiş Hoca bilgeliğini konuştur."
        )

        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}]
            )
            sermon = response.choices[0].message.content.strip()
            
            # Twitter 280 karakter sınırı kontrolü (Eğer çok uzunsa thread yapabilirsin ama şimdilik tek tweet)
            twitter.create_tweet(text=sermon[:280]) 
            logger.info("Haftalık Hutbe verildi!")
        except Exception as e:
            logger.error(f"Hutbe Hatası: {e}")

    # --- DİĞER FONKSİYONLAR ---
    def reply_to_mentions(self):
        if not self.me: return
        try:
            mentions = twitter.get_users_mentions(id=self.me.id, since_id=self.last_mention_id)
            if not mentions.data: return

            for tweet in sorted(mentions.data, key=lambda x: x.id):
                if tweet.author_id == self.me.id: continue
                
                res = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": tweet.text}]
                )
                twitter.create_tweet(text=res.choices[0].message.content.strip(), in_reply_to_tweet_id=tweet.id)
                self.save_last_id(tweet.id)
        except Exception as e: logger.error(f"Mention Hatası: {e}")

    def run(self):
        scheduler = BackgroundScheduler()
        # Her Pazar saat 21:00'de Hutbe Ver (Türkiye Saati ile ayarlanabilir)
        scheduler.add_job(self.weekly_sermon, 'cron', day_of_week='sun', hour=21, minute=0)
        scheduler.start()

        while True:
            self.reply_to_mentions()
            time.sleep(120)

if __name__ == "__main__":
    hoca = KriptoHocaUltimate()
    hoca.run()
                
