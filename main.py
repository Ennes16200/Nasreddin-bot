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
    def __init__(self, name="KriptoHoca"):
        self.name = name
        self.last_mention_id = None
        self.me = None
        try:
            self.me = twitter.get_me().data
            logger.info(f"Hoca sisteme giriş yaptı: @{self.me.username}")
        except Exception as e:
            logger.error(f"Twitter girişi başarısız: {e}")

    def check_security(self, chain_id, contract_address):
        """Token güvenlik taraması yapar."""
        if not contract_address or contract_address == "N/A":
            return "Yeni bir kazan doğmuş ama mühürleri belirsiz."
        try:
            url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract_address}"
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 1 and res.get("result"):
                data = res["result"].get(contract_address.lower(), {})
                risks = []
                if data.get("is_honeypot") == "1": risks.append("BAL KÜPÜ!")
                if data.get("is_mintable") == "1": risks.append("SINIRSIZ BASKI!")
                return " | ".join(risks) if risks else "Sözleşme temiz."
        except:
            return "Mühürler sökülemedi."
        return "İnceleme yapılamadı."

    def get_market_wisdom(self):
        """Piyasa verilerini toplar."""
        try:
            # 1. Fiyat Verisi
            btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
            btc_price = btc_res.get('price', "0")

            # 2. Korku Endeksi
            fng_res = requests.get("https://api.alternative.me/fng/", timeout=10).json()
            fng = fng_res.get('data', [{}])[0].get('value', "50")

            return {"btc": round(float(btc_price), 2), "fng": fng}
        except Exception as e:
            logger.error(f"Veri toplama hatası: {e}")
            return {"btc": "Bilinmiyor", "fng": "50"}

    def generate_manual_wisdom(self, haber, balina):
        """Senin verdiğin manuel verileri Hoca diliyle yorumlar."""
        w = self.get_market_wisdom()
        prompt = (f"Piyasa Durumu -> BTC: {w['btc']}$, Korku Endeksi: {w['fng']}/100. "
                  f"GÜNCEL HABER: {haber}. BALİNA HAREKETİ: {balina}. "
                  f"Nasreddin Hoca olarak bu durumu iğneleyici, fıkra temalı bir Türkçe tweet yaz. "
                  f"Asla 'Hoca:' gibi isim etiketleri kullanma. Doğrudan cümleye baş. (Max 240 karakter).")
        
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen bilge ve iğneleyici Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI Yanıt Hatası: {e}")
            return None

    def check_mentions(self):
        """Gelen mention'ları kontrol eder."""
        if not self.me: return
        try:
            mentions = twitter.get_users_mentions(id=self.me.id, since_id=self.last_mention_id)
            if not mentions or not mentions.data: return
            for tweet in mentions.data:
                self.last_mention_id = tweet.id
                # Mention yanıtı üretme
                prompt = f"Kullanıcı: '{tweet.text}'. Nasreddin Hoca olarak kısa, komik ve bilgece bir cevap ver."
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "Sen Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content.strip()
                twitter.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                logger.info(f"Yanıtlandı: {reply}")
        except Exception as e:
            logger.error(f"Mention hatası: {e}")

    def run_manual_mode(self):
        """Botu senin kontrolünde çalıştırır."""
        logger.info("=== Hoca Manuel Kürsüde! ===")
        while True:
            print("\n--- Yeni Tweet Hazırlığı ---")
            haber = input("Haber (Boş bırakmak için Enter): ")
            balina = input("Balina Hareketi (Boş bırakmak için Enter): ")
            
            tweet = self.generate_manual_wisdom(haber, balina)
            if tweet:
                print(f"\n📜 HOCA'NIN YORUMU:\n{tweet}")
                onay = input("\nTwitter'da paylaşılsın mı? (e/h): ")
                if onay.lower() == 'e':
                    twitter.create_tweet(text=tweet)
                    logger.info("Tweet paylaşıldı.")
                
            # Arada mentionları da kontrol et
            self.check_mentions()
            
            devam = input("\nYeni bir yorum yapmak istiyor musun? (e/h): ")
            if devam.lower() != 'e':
                break

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    # Botu manuel modda başlatıyoruz
    agent.run_manual_mode()
