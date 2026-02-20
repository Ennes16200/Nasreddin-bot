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
# Ortam değişkenlerinden API anahtarlarını alıyoruz
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
        """Piyasa verilerini toplar (Hata korumalı ve yedekli)."""
        try:
            # 1. Fiyat Verisi (Binance + CoinGecko yedeği)
            btc_price = "0"
            try:
                btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
                btc_price = btc_res.get('price', "0")
            except:
                btc_res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
                btc_price = btc_res.get('bitcoin', {}).get('usd', "0")

            # 2. Trend Verisi
            trend_name = "Piyasa durgun"
            security_info = "İnceleme yapılamadı"
            try:
                t_res = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10).json()
                if 'coins' in t_res and len(t_res['coins']) > 0:
                    top_coin = t_res['coins'][0]['item']
                    trend_name = top_coin.get('name', "Bilinmeyen Coin")
                    security_info = self.check_security("1", top_coin.get('native_slug', 'N/A'))
            except:
                pass

            # 3. Korku Endeksi
            fng = "50"
            try:
                fng_res = requests.get("https://api.alternative.me/fng/", timeout=10).json()
                fng = fng_res.get('data', [{}])[0].get('value', "50")
            except:
                pass

            return {
                "btc": round(float(btc_price), 2),
                "trend": trend_name,
                "security": security_info,
                "fng": fng
            }
        except Exception as e:
            logger.error(f"Veri toplama hatası: {e}")
            return None

    def generate_wisdom_tweet(self):
        """Genel piyasa tweeti üretir."""
        w = self.get_market_wisdom()
        if not w: return None
        
        # Prompt güncellendi: İsim etiketi yasaklandı ve yaratıcılık eklendi.
        prompt = (f"BTC: {w['btc']}$, Trend: {w['trend']}, Güvenlik: {w['security']}, Korku: {w['fng']}/100. "
                  f"Nasreddin Hoca olarak iğneleyici, fıkra temalı bir Türkçe tweet yaz. "
                  f"ÖNEMLİ: Cevaba asla 'Nasreddin Hoca:' veya 'Hoca:' gibi isim etiketleri ekleme, doğrudan cümleye baş. "
                  f"Sürekli aynı hitapları kullanma, yaratıcı ol. (Max 240 karakter).")
        
        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Sen bilge ve iğneleyici Nasreddin Hoca'sın."}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except: return None

    def generate_reply(self, user_tweet):
        """Mention (etiketleme) yanıtı üretir."""
        # Prompt güncellendi: İsim etiketi yasaklandı ve doğrudan konuşma istendi.
        prompt = (f"Kullanıcı sana şunu dedi: '{user_tweet}'. Nasreddin Hoca olarak bilgece, fıkra elementli ve kripto jargonlu komik bir cevap ver. "
                  f"ÖNEMLİ: Cevabın başına asla 'Nasreddin Hoca:' veya isim yazma, doğrudan konuşmaya baş. "
                  f"Sürekli 'Evladım' deme, farklı ve bilgece hitaplar kullan. (Max 200 karakter).")
        
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
                reply = self.generate_reply(tweet.text)
                if reply:
                    twitter.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                    logger.info(f"Yanıtlandı: {tweet.text} -> {reply}")
                time.sleep(5) # Twitter spam filtresine takılmamak için kısa bekleme
        except Exception as e:
            logger.error(f"Mention hatası: {e}")

    def run(self):
        """Botun ana döngüsü."""
        logger.info("=== Hoca Piyasaya İndi! ===")
        last_wisdom_time = 0
        while True:
            self.check_mentions()
            
            # Her 2 saatte bir genel piyasa yorumu atar
            now = time.time()
            if now - last_wisdom_time > 7200:
                tweet = self.generate_wisdom_tweet()
                if tweet:
                    twitter.create_tweet(text=tweet)
                    logger.info(f"Genel tweet atıldı: {tweet}")
                    last_wisdom_time = now
            
            time.sleep(120) # 2 dakikada bir kontrol et

if __name__ == "__main__":
    agent = KriptoHocaAgent()
    agent.run()
