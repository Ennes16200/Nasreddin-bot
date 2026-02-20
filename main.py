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
# Not: Bu değerleri ortam değişkeni (env) olarak tanımlamanız önerilir.
client_ai = OpenAI(api_key="OPENAI_API_KEY_BURAYA")

twitter = tweepy.Client(
    bearer_token="BEARER_TOKEN_BURAYA",
    consumer_key="API_KEY_BURAYA",
    consumer_secret="API_SECRET_BURAYA",
    access_token="ACCESS_TOKEN_BURAYA",
    access_token_secret="ACCESS_SECRET_BURAYA",
)

# ========= KRIPTO HOCA AGENT =========
class KriptoHocaAgent:
    def __init__(self, name="KriptoHoca"):
        self.name = name
        self.tweet_times = []
        self.TWEET_LIMIT_PER_HOUR = 5

    def check_security(self, chain_id, contract_address):
        """GoPlus Security API kullanarak kontratı tarar."""
        if not contract_address or contract_address == "N/A":
            return "Yeni bir kazan doğmuş ama henüz mühürlerini (kontratını) göremedim."
            
        try:
            url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract_address}"
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 1:
                data = res["result"][contract_address.lower()]
                
                risks = []
                if data.get("is_honeypot") == "1": risks.append("BAL KÜPÜ (Honeypot) TUZAĞI!")
                if data.get("is_mintable") == "1": risks.append("SINIRSIZ BASKI (Mintable)!")
                if data.get("cannot_buy") == "1" or data.get("cannot_sell") == "1": risks.append("ALIM-SATIM KİLİDİ!")
                
                if not risks:
                    return "Sözleşme temiz görünüyor, ama yine de eşeği sağlam kazığa bağlayın."
                return " | ".join(risks)
        except Exception as e:
            logger.error(f"Güvenlik tarama hatası: {e}")
            return "Sözleşme mühürlerini sökemedim, karanlık işler dönüyor olabilir."
        return "İnceleme yapılamadı."

    def get_market_wisdom(self):
        """Piyasa verilerini ve trendleri toplar."""
        try:
            # 1. Fiyatlar (Binance)
            btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            gold_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT").json()
            
            btc = btc_res.get('price', '0')
            gold = gold_res.get('price', '0')

            # 2. Trend Projeler (CoinGecko)
            t_res = requests.get("https://api.coingecko.com/api/v3/search/trending").json()
            if not t_res.get('coins'):
                return None
                
            top_coin = t_res['coins'][0]['item']
            coin_name = top_coin['name']
            # Trend coinlerin kontrat adresini almaya çalışalım (varsa)
            contract_addr = top_coin.get('native_slug', 'N/A') 
            
            # Güvenlik kontrolü (Örnek olarak Ethereum/1 ağında tarıyoruz)
            security_report = self.check_security("1", contract_addr)

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
            logger.error(f"Veri toplama hatası: {e}")
            return None

    def generate_wisdom_tweet(self):
        """Hoca'nın ağzından tweet üretir."""
        wisdom = self.get_market_wisdom()
        if not wisdom: return None

        prompt = f"""
Sen Nasreddin Hoca'sın. Elindeki veriler:
- Bitcoin: {wisdom['btc']}$
- Altın: {wisdom['gold']}$
- Yeni Trend Proje: {wisdom['trend']}
- Güvenlik Durumu: {wisdom['security']}
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
        except Exception as e:
            logger.error(f"AI Tweet üretim hatası: {e}")
            return None

    def send_tweet(self, text):
        """Tweeti Twitter'a gönderir."""
        now = datetime.now()
        self.tweet_times = [t for t in self.tweet_times if now - t < timedelta(hours=1)]
        
        if text and len(self.tweet_times) < self.TWEET_LIMIT_PER_HOUR:
            try:
                twitter.create_tweet(text=text)
                self.tweet_times.append(now)
                logger.info(f"Tweet Başarılı: {text}")
            except Exception as e:
                logger.error(f"Twitter API Hatası: {e}")

    def run(self):
        """Ana döngü."""
        logger.info("=== Hoca Piyasaya İndi! ===")
        while True:
            tweet = self.generate_wisdom_tweet()
            if tweet:
                self.send_tweet(tweet)
            
            # 1-3 saat arası rastgele bekleme
            wait = random.randint(3600, 10800)
            logger.info(f"Hoca istirahate çekildi. {wait//60} dk sonra dönecek.")
            time.sleep(wait)

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
