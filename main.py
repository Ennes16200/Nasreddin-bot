#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import hashlib
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

class KriptoHocaMaster:
    def __init__(self):
        self.last_mention_id = self.load_last_id()
        self.me = None
        # Heybe (Portföy)
        self.portfolio = {
            "BTC": {"amount": 0.1, "buy_price": 68000.0},
            "ETH": {"amount": 1.5, "buy_price": 1970.0},
            "SOL": {"amount": 20.0, "buy_price": 85.0},
            "SUI": {"amount": 1000.0, "buy_price": 0.9}
        }
        
        self.system_prompt = (
            "Sen Kripto Nasreddin Hoca'sın. Üslubun: 'Bre evlat', 'Cemaat-i Dijital', 'İlahi'. "
            "Kripto jargonunu (Airdrop, NFT, Rugpull, FOMO) Anadolu fıkralarıyla harmanlarsın. "
            "NFT'ler için 'Dijital Tablo', Airdrop'lar için 'Bedava Düdük' tabirini kullanırsın. "
            "Çok zeki, esprili ve fırsatları kovalayan ama 'Ya tutarsa' demeyi unutmayan birisin."
        )

        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüde: @{self.me.username}")
        except Exception as e:
            logger.error(f"Twitter Giriş Hatası: {e}")

    # --- HAFIZA KONTROLÜ (RENDER UYUMLU) ---
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

    # --- PİYASA VERİLERİ ---
    def get_coin_price(self, symbol):
        try:
            sym = symbol.upper().replace("$", "").replace("USDT", "") + "USDT"
            res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=10).json()
            return float(res['price'])
        except: return None

    # --- YENİ: FIRSAT TAKİBİ (AIRDROP & NFT) ---
    def hunt_opportunities(self):
        """Hoca piyasadaki airdrop ve NFT trendlerini yorumlar."""
        # Burada yapay zekaya güncel trendleri yorumlatıyoruz
        prompt = (
            "Bugün piyasada hangi airdrop'lar veya NFT projeleri konuşuluyor olabilir? "
            "Genel bir piyasa araştırması yapıyormuş gibi davran ve Nasreddin Hoca olarak "
            "takipçilerine bir 'fırsat' uyarısı yap. 'Bedava düdük' (airdrop) peşinde "
            "koşanlara ya da 'dijital parşömenlere' (NFT) para yatıranlara nükte yap."
        )
        
        res = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}]
        )
        twitter.create_tweet(text=f"🧐 HOCA'NIN RADARI:\n\n{res.choices[0].message.content.strip()[:240]}")

    # --- ANA FONKSİYONLAR ---
    def get_heybe_report(self):
        current_total = 0
        buy_total = sum(v["amount"] * v["buy_price"] for v in self.portfolio.values())
        for coin, data in self.portfolio.items():
            p = self.get_coin_price(coin) or data["buy_price"]
            current_total += data["amount"] * p
            
        change = ((current_total - buy_total) / buy_total) * 100
        prompt = f"Heybe %{change:.2f} değişimde. BTC, ETH, SOL, SUI var. Hoca yorumu yaz."
        res = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}])
        return f"💰 HEYBE RAPORU (%{change:.2f})\n\n{res.choices[0].message.content.strip()[:240]}"

    def reply_to_mentions(self):
        if not self.me: return
        try:
            params = {"id": self.me.id, "max_results": 10}
            if self.last_mention_id:
                params["since_id"] = self.last_mention_id
            
            mentions = twitter.get_users_mentions(**params)
            if not mentions or not mentions.data: return

            for tweet in sorted(mentions.data, key=lambda x: x.id):
                if tweet.author_id == self.me.id: continue
                
                # ZEKİ ANALİZ
                txt = tweet.text.upper()
                prompt = f"Kullanıcı dedi ki: {tweet.text}. Ona Nasreddin Hoca olarak kısa, zeki ve esprili cevap ver."
                
                res = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}]
                )
                twitter.create_tweet(text=res.choices[0].message.content.strip()[:280], in_reply_to_tweet_id=tweet.id)
                self.save_last_id(tweet.id)
                time.sleep(5)
        except Exception as e: logger.error(f"Hata: {e}")

    def run(self):
        scheduler = BackgroundScheduler()
        # Haftalık Hutbe (Pazar 21:00)
        scheduler.add_job(lambda: twitter.create_tweet(text=self.get_heybe_report()), 'cron', day_of_week='sun', hour=21, minute=0)
        # Fırsat Takibi (Salı ve Perşembe 14:00)
        scheduler.add_job(self.hunt_opportunities, 'cron', day_of_week='tue,thu', hour=14, minute=0)
        # Sabah Selamı (Her gün 09:00)
        scheduler.add_job(lambda: twitter.create_tweet(text="Sabah-ı şerifleriniz hayrolsun! Akşehir pazarında SUI mi satılır NFT mi? Göle maya çaldık bekliyoruz."), 'cron', hour=9, minute=0)
        
        scheduler.start()
        while True:
            self.reply_to_mentions()
            time.sleep(120)

if __name__ == "__main__":
    KriptoHocaMaster().run()
                          
