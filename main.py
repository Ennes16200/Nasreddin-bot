#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import tweepy
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

class KriptoHocaAgent:
    def __init__(self):
        self.last_mention_id = None
        self.me = None
        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca Render Kürsüsünde: @{self.me.username}")
        except Exception as e:
            logger.error(f"Twitter Giriş Hatası: {e}")

    def get_market_wisdom(self):
        """Piyasa verilerini, haberleri ve balina hareketlerini toplar."""
        data = {"btc": "Bilinmiyor", "fng": "50", "news": "Piyasa durgun", "whale": "Sakin"}
        try:
            # 1. Fiyat Verisi (Binance)
            btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
            data['btc'] = round(float(btc_res.get('price', 0)), 2)

            # 2. Korku Endeksi
            fng_res = requests.get("https://api.alternative.me/fng/", timeout=10).json()
            data['fng'] = fng_res.get('data', [{}])[0].get('value', "50")

            # 3. Otomatik Haber Çekme (CryptoPanic veya benzeri bir API - Örnek simülasyon)
            # Not: Burası manuel input yerine piyasadaki son dakika gelişmelerini simüle eder
            news_res = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10).json()
            trending = [t['item']['name'] for t in news_res.get('coins', [])[:3]]
            data['news'] = f"Trend olanlar: {', '.join(trending)}"

            # 4. Balina Hareketi (Büyük hacimli değişimleri kontrol eder)
            vol_res = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=10).json()
            if float(vol_res.get('priceChangePercent', 0)) > 3:
                data['whale'] = "Sert hareketler var, balinalar suyu bulandırdı!"
            else:
                data['whale'] = "Balinalar derinde dinleniyor."
                
            return data
        except Exception as e:
            logger.error(f"Veri toplama hatası: {e}")
            return data

    def check_security(self, chain_id, contract_address):
        """Token güvenlik taraması (GoPlus API)"""
        if not contract_address: return "Mühürsüz."
        try:
            url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract_address}"
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 1:
                details = res["result"].get(contract_address.lower(), {})
                if details.get("is_honeypot") == "1": return "BAL KÜPÜ (Honeypot)!"
                return "Sözleşme temiz görünüyor."
        except:
            return "Güvenlik taraması yapılamadı."

    def generate_and_post(self):
        """Verileri Hoca diliyle yorumlar ve paylaşır."""
        w = self.get_market_wisdom()
        prompt = (f"Piyasa Durumu -> BTC: {w['btc']}$, Korku: {w['fng']}/100. "
                  f"HABER: {w['news']}. BALİNA: {w['whale']}. "
                  f"Nasreddin Hoca olarak bu durumu iğneleyici, fıkra temalı bir Türkçe tweet yaz. "
                  f"Asla 'Hoca:' gibi isim etiketleri kullanma. Doğrudan cümleye baş. (Max 240 karakter).")
        
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen bilge ve iğneleyici Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
            )
            tweet = response.choices[0].message.content.strip()
            twitter.create_tweet(text=tweet)
            logger.info(f"Tweet Paylaşıldı: {tweet}")
        except Exception as e:
            logger.error(f"AI veya Twitter Hatası: {e}")

    def check_mentions(self):
        """Gelen mention'ları kontrol eder ve yanıtlar."""
        if not self.me: return
        try:
            mentions = twitter.get_users_mentions(id=self.me.id, since_id=self.last_mention_id)
            if not mentions or not mentions.data: return
            
            for tweet in mentions.data:
                self.last_mention_id = tweet.id
                prompt = f"Kullanıcı: '{tweet.text}'. Nasreddin Hoca olarak kısa, komik ve bilgece bir cevap ver."
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content.strip()
                twitter.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                logger.info(f"Yanıtlandı: {reply}")
        except Exception as e:
            logger.debug(f"Mention kontrolü: {e}")

    def run(self):
        """Render üzerinde sonsuz döngü."""
        last_tweet_time = 0
        while True:
            # 1. Mentionları her dakika kontrol et
            self.check_mentions()
            
            # 2. Her 4 saatte bir (14400 sn) piyasa yorumu at
            now = time.time()
            if now - last_tweet_time > 14400:
                self.generate_and_post()
                last_tweet_time = now
            
            time.sleep(60) # Render'ı yormamak için 1 dk bekle

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
