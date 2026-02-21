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
        # Hoca'nın Hayali Portföyü (Sui, Sol, Eth, Btc)
        self.portfolio = {
            "BTC": {"amount": 0.1, "buy_price": 68000.0},
            "ETH": {"amount": 1.5, "buy_price": 1970.0},
            "SOL": {"amount": 20.0, "buy_price": 87.0},
            "SUI": {"amount": 1000.0, "buy_price": 0.85}
        }
        
        # Karakter Tanımı
        self.system_prompt = (
            "Sen Kripto Nasreddin Hoca'sın. Üslubun: 'Bre evlat', 'Cemaat-i Dijital', 'İlahi', 'Ya tutarsa'. "
            "Türk mizahı kuvvetli, zeki ve nüktedan birisin. Kripto dünyasını mahalle kültürüyle yorumlarsın. "
            "NFT'ye 'dijital parşömen', Airdrop'a 'bedava düdük', Staking'e 'kazığı çakmak' dersin. "
            "SUI sorulunca mutlaka su/göl esprileri yaparsın. Yatırım tavsiyesi değil, nasip tavsiyesi verirsin."
        )

        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüde: @{self.me.username}")
        except Exception as e:
            logger.error(f"Giriş Hatası: {e}. API anahtarlarını kontrol et!")

    # --- HAFIZA VE VERİ ---
    def load_last_id(self):
        if os.path.exists(ID_FILE):
            try:
                with open(ID_FILE, "r") as f: return int(f.read().strip())
            except: return None
        return None

    def save_last_id(self, tweet_id):
        try:
            with open(ID_FILE, "w") as f: f.write(str(tweet_id))
            self.last_mention_id = tweet_id
        except: pass

    def get_coin_price(self, symbol):
        try:
            sym = symbol.upper().replace("$", "").replace("USDT", "") + "USDT"
            res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=10).json()
            return float(res['price'])
        except: return None

    # --- ÖZELLİKLER: MAYA SKORU & NÜKTE ---
    def get_maya_score(self, coin_name):
        seed = f"{coin_name.upper()}{datetime.now().strftime('%Y%m%d')}"
        score = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 100
        price = self.get_coin_price(coin_name)
        
        prompt = (f"{coin_name} için maya skoru %{score}. Mevcut fiyat: {price if price else 'Pazarda yok'}. "
                  "Hoca olarak bu coine maya tutar mı, esprili ve fıkra tadında anlat.")
        
        res = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}])
        return res.choices[0].message.content.strip()

    # --- ÖZELLİKLER: HEYBE VE AIRDROP ---
    def get_heybe_report(self):
        current_total = 0
        buy_total = sum(v["amount"] * v["buy_price"] for v in self.portfolio.values())
        for coin, data in self.portfolio.items():
            p = self.get_coin_price(coin) or data["buy_price"]
            current_total += data["amount"] * p
        change = ((current_total - buy_total) / buy_total) * 100
        
        prompt = f"Hoca'nın heybesi %{change:.2f} değişimde. BTC, ETH, SOL ve SUI var. Heybenin bereketini Türk mizahıyla yorumla."
        res = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}])
        return f"💰 HEYBE RAPORU (%{change:.2f})\n\n{res.choices[0].message.content.strip()[:240]}"

    def hunt_opportunities(self):
        prompt = "Piyasadaki airdrop (bedava düdük) ve NFT (dijital parşömen) çılgınlığı hakkında cemaate zekice bir uyarı veya fırsat tweeti yaz."
        res = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}])
        twitter.create_tweet(text=f"🧐 HOCA'NIN RADARI:\n\n{res.choices[0].message.content.strip()[:240]}")

    # --- ETKİLEŞİM VE RUTİN ---
    def reply_to_mentions(self):
        if not self.me: return
        try:
            params = {"id": self.me.id, "max_results": 10}
            if self.last_mention_id: params["since_id"] = self.last_mention_id
            
            mentions = twitter.get_users_mentions(**params)
            if not mentions or not mentions.data: return

            for tweet in sorted(mentions.data, key=lambda x: x.id):
                if tweet.author_id == self.me.id: continue
                
                txt = tweet.text.upper()
                if any(w in txt for w in ["MAYA", "NE OLUR", "SKOR", "SUI", "ALINIR MI"]):
                    words = tweet.text.split()
                    coin = next((w for w in words if w.startswith('$') or w.isupper()), "bu coin")
                    reply = self.get_maya_score(coin)
                else:
                    res = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": tweet.text}])
                    reply = res.choices[0].message.content.strip()

                twitter.create_tweet(text=reply[:280], in_reply_to_tweet_id=tweet.id)
                self.save_last_id(tweet.id)
                time.sleep(5)
        except Exception as e: logger.error(f"Etkileşim Hatası: {e}")

    def run(self):
        scheduler = BackgroundScheduler()
        # Her sabah 09:00 Selam
        scheduler.add_job(lambda: twitter.create_tweet(text="Sabah-ı şerifleriniz hayrolsun! Eşeği düğümden çözdük, grafikleri açtık. Ya tutarsa!"), 'cron', hour=9, minute=0)
        # Salı & Perşembe 14:00 Airdrop Radarı
        scheduler.add_job(self.hunt_opportunities, 'cron', day_of_week='tue,thu', hour=14, minute=0)
        # Pazar 21:00 Haftalık Hutbe & Heybe
        scheduler.add_job(lambda: twitter.create_tweet(text=self.get_heybe_report()), 'cron', day_of_week='sun', hour=21, minute=0)
        
        scheduler.start()
        logger.info("Hoca iş başında, cemaat bekleniyor...")
        while True:
            self.reply_to_mentions()
            time.sleep(120)

if __name__ == "__main__":
    KriptoHocaUltimate().run()
        
