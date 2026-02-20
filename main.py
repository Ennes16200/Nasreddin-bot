#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import logging
import requests
import tweepy
from datetime import datetime, timedelta
from openai import OpenAI

# ========= LOG YAPILANDIRMASI =========
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========= API İSTEMCİLERİ (GİZLİ FORMAT) =========
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

twitter = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
)

# ========= KRIPTO HOCA AGENT =========
class KriptoHocaAgent:
    def __init__(self, name="KriptoHoca"):
        self.name = name
        self.last_mention_id = None
        self.tweet_times = []
        self.TWEET_LIMIT_PER_HOUR = 5
        self.me = None
        
        # Başlangıçta kendi ID'mizi alalım
        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca sisteme giriş yaptı: @{self.me.username}")
        except Exception as e:
            logger.error(f"Twitter girişi başarısız! API anahtarlarını kontrol et: {e}")

    def check_security(self, chain_id, contract_address):
        """GoPlus Security API kullanarak kontratı tarar."""
        if not contract_address or contract_address == "N/A":
            return "Yeni bir kazan doğmuş ama henüz mühürlerini göremedim."
            
        try:
            url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract_address}"
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 1 and res.get("result"):
                data = res["result"].get(contract_address.lower(), {})
                risks = []
                if data.get("is_honeypot") == "1": risks.append("BAL KÜPÜ!")
                if data.get("is_mintable") == "1": risks.append("SINIRSIZ BASKI!")
                if data.get("cannot_sell") == "1": risks.append("SATIŞ KİLİDİ!")
                
                return " | ".join(risks) if risks else "Sözleşme temiz görünüyor."
        except:
            return "Sözleşme mühürlerini sökemedim."
        return "İnceleme yapılamadı."

    def get_market_wisdom(self):
        """Piyasa verilerini toplar."""
        try:
            # Fiyatlar
            btc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price']
            # Trendler
            t_res = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
            top_coin = t_res['coins'][0]['item']
            # Korku Endeksi
            fng = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']

            return {
                "btc": round(float(btc), 2),
                "trend": top_coin['name'],
                "security": self.check_security("1", top_coin.get('native_slug', 'N/A')),
                "fng": fng
            }
        except Exception as e:
            logger.error(f"Veri toplama hatası: {e}")
            return None

    def generate_wisdom_tweet(self):
        """Hoca'nın ağzından genel tweet üretir."""
        w = self.get_market_wisdom()
        if not w: return None

        prompt = f"Bitcoin: {w['btc']}$, Trend: {w['trend']}, Güvenlik: {w['security']}, Korku: {w['fng']}/100. Nasreddin Hoca olarak bu verilerle iğneleyici, komik, fıkra temalı bir Türkçe tweet yaz (Max 240 karakter)."
        
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen bilge Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except: return None

    def generate_reply(self, user_tweet):
        """Mention'lara Hoca tarzında cevap üretir."""
        prompt = f"Bir kullanıcı sana şunu yazdı: '{user_tweet}'. Nasreddin Hoca olarak ona bilgece, fıkra elementli (kazan, eşek vb.) ve kripto jargonlu komik bir cevap ver (Max 200 karakter)."
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except: return None

    def check_mentions(self):
        """Gelen mention'ları kontrol eder ve yanıtlar."""
        if not self.me: return
        try:
            mentions = twitter.get_users_mentions(id=self.me.id, since_id=self.last_mention_id)
            if not mentions.data: return

            for tweet in mentions.data:
                self.last_mention_id = tweet.id
                logger.info(f"Mention yakalandı: {tweet.text}")
                reply = self.generate_reply(tweet.text)
                if reply:
                    twitter.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                    logger.info(f"Cevap gönderildi.")
                time.sleep(5) # Limit koruması
        except Exception as e:
            logger.error(f"Mention hatası: {e}")

    def send_tweet(self, text):
        """Genel tweet gönderir."""
        try:
            twitter.create_tweet(text=text)
            logger.info(f"Tweet atıldı: {text}")
        except Exception as e:
            logger.error(f"Tweet gönderme hatası: {e}")

    def run(self):
        """Ana döngü."""
        logger.info("=== Hoca Piyasaya İndi! ===")
        last_wisdom_time = 0
        
        while True:
            # 1. Mention Kontrolü (Her döngüde)
            self.check_mentions()
            
            # 2. Periyodik Tweet (2 saatte bir)
            now = time.time()
            if now - last_wisdom_time > 7200:
                tweet = self.generate_wisdom_tweet()
                if tweet:
                    self.send_tweet(tweet)
                    last_wisdom_time = now
            
            # 3. Bekleme (2 dakika)
            time.sleep(120)

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
