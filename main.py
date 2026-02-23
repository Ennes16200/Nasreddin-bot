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

def moltlets_dunyasına_gir(ajan_ismi, hoca_biosu):
    """
    Bu fonksiyon Moltlets API'sine gider ve sana o meşhur Claim Linkini getirir.
    """
    url = "https://moltlets.world/api/spawn" # Manual'daki spawn adresi
    payload = {
        "name": ajan_ismi,
        "bio": hoca_biosu
    }
    
    try:
        print(f"--- {ajan_ismi} için Moltlets kapısı çalınıyor... ---")
        response = requests.post(url, json=payload)
        data = response.json()
        
        if "claim_url" in data:
            print("\n✅ BULDUM! İşte senin Claim Linkin:")
            print(f"👉 {data['claim_url']} 👈")
            print("\nBu linke tıkla, Twitter handle'ını gir ve doğrula.")
        else:
            print("❌ Bir sorun çıktı, API yanıtı:", data)
            
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")

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
        self.me = None
        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Kürsüde: @{self.me.username}")
        except Exception as e:
            logger.error(f"Giriş Hatası: {e}")

        # Başlangıçta hafızayı Twitter'dan tazele
        self.last_mention_id = self.get_last_tweet_id_from_profile()
        
        # Hoca'nın Hayali Heybesi
        self.portfolio = {
            "BTC": {"amount": 0.1, "buy_price": 68000.0},
            "ETH": {"amount": 1.5, "buy_price": 1970.0},
            "SOL": {"amount": 20.0, "buy_price": 85.0},
            "SUI": {"amount": 1000.0, "buy_price": 0.9}
        }
        
        self.system_prompt = (
            "Sen Kripto Nasreddin Hoca'sın. Üslubun: 'Bre evlat', 'Cemaat-i Dijital', 'İlahi', 'Ya tutarsa'. "
            "Türk mizahı kuvvetli, zeki ve nüktedan birisin. Kriptoyu mahalle kültürüyle yorumlarsın. "
            "NFT'ye 'dijital parşömen', Airdrop'a 'bedava düdük', Staking'e 'kazığı çakmak' dersin. "
            "SUI sorulunca mutlaka su/göl esprileri yap. Yatırım tavsiyesi değil, nasip tavsiyesi ver."
        )

    # --- KRİTİK HAFIZA FONKSİYONU (SPAM ENGELLEYİCİ) ---
    def get_last_tweet_id_from_profile(self):
        """Render sıfırlansa bile Hoca'nın en son attığı tweeti bulup oradan devam etmesini sağlar."""
        try:
            my_tweets = twitter.get_users_tweets(id=self.me.id, max_results=5)
            if my_tweets and my_tweets.data:
                last_id = my_tweets.data[0].id
                logger.info(f"Son tweet bulundu, hafıza bu ID'den başlıyor: {last_id}")
                return last_id
            return None
        except Exception as e:
            logger.error(f"Profil hafızası çekilemedi: {e}")
            return None

    def save_last_id(self, tweet_id):
        self.last_mention_id = tweet_id
        try:
            with open(ID_FILE, "w") as f: f.write(str(tweet_id))
        except: pass

    # --- PİYASA VERİLERİ ---
    def get_coin_price(self, symbol):
        try:
            sym = symbol.upper().replace("$", "").replace("USDT", "") + "USDT"
            res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=10).json()
            return float(res['price'])
        except: return None

    # --- ÖZELLİKLER ---
    def get_maya_score(self, coin_name):
        seed = f"{coin_name.upper()}{datetime.now().strftime('%Y%m%d')}"
        score = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 100
        price = self.get_coin_price(coin_name)
        prompt = f"{coin_name} için maya skoru %{score}. Fiyat: {price if price else 'Yok'}. Esprili yorumla."
        res = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}])
        return res.choices[0].message.content.strip()

    def get_heybe_report(self):
        current_total = 0
        buy_total = sum(v["amount"] * v["buy_price"] for v in self.portfolio.values())
        for coin, data in self.portfolio.items():
            p = self.get_coin_price(coin) or data["buy_price"]
            current_total += data["amount"] * p
        change = ((current_total - buy_total) / buy_total) * 100
        prompt = f"Heybe %{change:.2f} değişimde. BTC, ETH, SOL, SUI var. Türk mizahıyla bereket yorumu yap."
        res = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}])
        return f"💰 HEYBE RAPORU (%{change:.2f})\n\n{res.choices[0].message.content.strip()[:240]}"

    # --- ETKİLEŞİM DÖNGÜSÜ ---
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
        except Exception as e: logger.error(f"Hata: {e}")

    def run(self):
        scheduler = BackgroundScheduler()
        # Sabah Selamı 09:00
        scheduler.add_job(lambda: twitter.create_tweet(text="Sabah-ı şerifleriniz hayrolsun cemaat! Eşeği doyurduk, göle bakıyoruz. Ya tutarsa!"), 'cron', hour=9, minute=0)
        # Salı & Perşembe Airdrop Radarı 14:00
        scheduler.add_job(lambda: twitter.create_tweet(text=self.get_maya_score("Airdrop")), 'cron', day_of_week='tue,thu', hour=14, minute=0)
        # Pazar 21:00 Heybe Raporu
        scheduler.add_job(lambda: twitter.create_tweet(text=self.get_heybe_report()), 'cron', day_of_week='sun', hour=21, minute=0)
        
        scheduler.start()
        while True:
            self.reply_to_mentions()
            time.sleep(120)

if __name__ == "__main__":
    # Sadece bir kez çalıştırıp linki alman yeterli
moltlets_dunyasına_gir("Nasreddin Hoca", "Gülümseten ve düşündüren bilge.")
    KriptoHocaUltimate().run()
            
