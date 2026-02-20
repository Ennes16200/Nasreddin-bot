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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========= API İSTEMCİLERİ =========
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

twitter = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
)

# ========= AYARLAR =========
COLLECTIONS = ["boredapeyachtclub", "azuki", "pudgypenguins"]

class KriptoHocaAgent:
    def __init__(self, name="KriptoHoca"):
        self.name = name
        self.tweet_times = []
        self.TWEET_LIMIT_PER_HOUR = 5

    # --- GÜVENLİK MÜFETTİŞİ (GoPlus API) ---
    def check_security(self, chain_id, contract_address):
        """
        Yeni projenin kontratını tarar. 
        chain_id: 1 (ETH), 56 (BSC), 137 (Polygon), 8453 (Base)
        """
        try:
            url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract_address}"
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 1:
                data = res["result"][contract_address.lower()]
                
                risks = []
                if data.get("is_honeypot") == "1": risks.append("BAL KÜPÜ (Honeypot) TUZAĞI! Parayı koyan geri alamaz.")
                if data.get("is_mintable") == "1": risks.append("SINIRSIZ BASKI (Mintable)! Sahibi kafasına göre para basar.")
                if data.get("cannot_buy") == "1" or data.get("cannot_sell") == "1": risks.append("ALIM-SATIM KİLİDİ! Kazan mühürlü.")
                
                if not risks:
                    return "Sözleşme temiz görünüyor, ama yine de eşeği sağlam kazığa bağlayın."
                return " | ".join(risks)
        except:
            return "Sözleşme mühürlerini sökemedim, karanlık işler dönüyor olabilir."
        return "İnceleme yapılamadı."

    # --- PİYASA & TREND VERİSİ ---
    def get_market_wisdom(self):
        try:
            # 1. Fiyatlar (Binance)
            p_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbols=[\"BTCUSDT\",\"PAXGUSDT\"]").json()
            btc = next(p['price'] for p in p_res if p['symbol'] == 'BTCUSDT')
            gold = next(p['price'] for p in p_res if p['symbol'] == 'PAXGUSDT')

            # 2. Trend Projeler & Güvenlik Kontrolü (CoinGecko)
            t_res = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
            top_coin = t_res['coins'][0]['item']
            coin_name = top_coin['name']
            
            # Eğer kontrat adresi varsa güvenlik taraması yap (Örn: Ethereum ağı varsayılan)
            # Not: Gerçek senaryoda ağ ID'si dinamik alınmalıdır.
            security_report = "Yeni bir kazan doğmuş, henüz mühürlerini inceleyemedim."
            # Bazı trend coinlerin kontrat adresleri API'den gelebilir, burada simüle ediyoruz:
            # security_report = self.check_security("1", "0x...") 

            # 3. Korku Endeksi
            f_res = requests.get("https://api.alternative.me/fng/").json()
            fng = f_res['data'][0]['value']
            mood = f_res['data'][0]['value_classification']

            return {
                "btc": round(float(btc), 2),
                "gold": round(float(gold), 2),
                "trend": coin_name,
                "security": security_report,
                "mood": f"{mood} ({fng}/100)"
            }
        except Exception as e:
            logger.error("Veri hatası: %s", e)
            return None

    # --- AI TWEET GENERATOR ---
    def generate_wisdom_tweet(self):
        wisdom = self.get_market_wisdom()
        if not wisdom: return None

        prompt = f"""
Sen Nasreddin Hoca'sın. Elindeki veriler:
- Bitcoin: {wisdom['btc']}$
- Altın (PAXG): {wisdom['gold']}$
- Yeni Proje: {wisdom['trend']}
- Güvenlik Raporu: {wisdom['security']}
- Piyasa Hissi: {wisdom['mood']}

Görev:
Bu verileri kullanarak; içinde 'Kazan doğurdu', 'Eşeğe ters binmek' veya 'Ya tutarsa' gibi bir fıkra teması olan, 
yeni çıkan {wisdom['trend']} projesine ve güvenlik durumuna ({wisdom['security']}) mutlaka değinen, 
kripto dünyasını iğneleyen bilgece ve komik bir Türkçe tweet yaz. Max 240 karakter.
"""
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen bilge ve mizahşör Nasreddin Hoca'sın."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except:
            return None

    # --- TWEET GÖNDER ---
    def send_tweet(self, text):
        now = datetime.now()
        self.tweet_times = [t for t in self.tweet_times if now - t < timedelta(hours=1)]
        
        if text and len(self.tweet_times) < self.TWEET_LIMIT_PER_HOUR:
            try:
                twitter.create_tweet(text=text)
                self.tweet_times.append(now)
                logger.info("Tweet Başarılı: %s", text)
            except Exception as e:
                logger.error("Twitter Hatası: %s", e)

    # --- ANA DÖNGÜ ---
    def run(self):
        logger.info("=== Hoca Piyasaya İndi! ===")
        while True:
            tweet = self.generate_wisdom_tweet()
            self.send_tweet(tweet)
            
            # 1-3 saat arası rastgele bekleme
            wait = random.randint(3600, 10800)
            logger.info(f"Hoca istirahate çekildi. {wait//60} dk sonra dönecek.")
            time.sleep(wait)

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
