#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import os
import logging
import asyncio
import requests
import random
from datetime import datetime

# --- LOGGING AYARLARI (Hataları takip etmek için) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("hoca_bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class SiberDervisNasreddin:
    def __init__(self):
        self.bot_name = "Siber-Derviş Nasreddin AI"
        
        # --- TWITTER API ANAHTARLARI ---
        # Buradaki tırnak içindeki yerleri Twitter Developer Portal'dan aldığın bilgilerle doldur.
        self.auth_keys = {
            "api_key": "QYMKqttYnTsx8cMok3ZAyX3jT",
            "api_secret": "BVMX6xg35Ujn2I1b5XeARdw8exGRRiX4TVEBstXX5TEFGCrPuA",
            "access_token": "2024178599994212352-JLWzVqyzSbrrJS8UvKaijnEjJTlaQZ",
            "access_token_secret": "iAgTL0djRZeOMAioCndkeppNiU240m11njgJJLyZpLEpo",
            "bearer_token": "AAAAAAAAAAAAAAAAAAAAAOHm7gEAAAAA7k%2B%2FXNpdC8mQaT0E826AD1WX4cw%3DLaYxWB7HcdmRDa8gQ3JysGmeOmhbNY6nheQ2L54GmgNUPn9cv0"
        }
        
        # --- FİKİR HAVUZU ---
        self.wisdom_pool = [
            "Blockchain tabanlı semaver: Her blokta bir çay demler, gas ücretiyle şeker alır.",
            "Eşeğin semerine takılan madencilik cihazı: Yürüdükçe Satoshi, durdukça dert üretir.",
            "Akıllı kontratla kız isteme: Başlık parası USDT ile ödenir.",
            "Metaverse'de cuma namazı çıkışı lokma dağıtımı: Sadece cüzdanında 'HAYIR' token olanlara.",
            "Kuantum tespih: Aynı anda hem çekildi hem çekilmedi, gözlemleyene kadar sevabı belli değil.",
            "Kazan doğurdu diyen balinaya, kazan öldü diyen küçük yatırımcı (Exit Liquidity).",
            "Eşeğe ters binip ayı piyasasında geri geri gitmek: 'Ben düşmüyorum, dünya yükseliyor'.",
            "Gölü mayalarken 'Ya tutarsa' diyen ilk DeFi kurucusu.",
            "Parayı veren düdüğü çalar: Balinalar çalar, planktonlar oynar.",
            "Ye kürküm ye: Sadece mavi tiki olanlara airdrop yapan protokoller."
        ]

    def connect_twitter(self):
        """Twitter'a bağlanmayı dener."""
        try:
            client = tweepy.Client(
                bearer_token=self.auth_keys["bearer_token"],
                consumer_key=self.auth_keys["api_key"],
                consumer_secret=self.auth_keys["api_secret"],
                access_token=self.auth_keys["access_token"],
                access_token_secret=self.auth_keys["access_token_secret"]
            )
            logger.info("Twitter bağlantısı kuruldu (API anahtarları girilmemişse hata verebilir).")
            return client
        except Exception as e:
            logger.error(f"Twitter bağlantı hatası: {e}")
            return None

    def rastgele_mesaj(self):
        """Havuzdan rastgele bir bilge söz seçer."""
        mesaj = random.choice(self.wisdom_pool)
        tarih = datetime.now().strftime("%H:%M:%S")
        return f"💡 Hoca Der Ki ({tarih}): {mesaj} #NasreddinAI #Web3"

    async def run_bot(self):
        """Botun ana çalışma döngüsü."""
        logger.info(f"{self.bot_name} aktif edildi.")
        twitter_client = self.connect_twitter()
        
        while True:
            try:
                icerik = self.rastgele_mesaj()
                logger.info(f"Hazırlanan Mesaj: {icerik}")
                
                # Twitter'da paylaşmak için aşağıdaki satırın başındaki '#' işaretini kaldır:
                # if twitter_client:
                #     twitter_client.create_tweet(text=icerik)
                #     logger.info("Tweet başarıyla gönderildi.")
                
                # 6 saatte bir çalışması için (Saniye cinsinden: 6 * 3600)
                # Test etmek için burayı 10 yapabilirsin (10 saniyede bir yazar).
                await asyncio.sleep(21600) 
                
            except Exception as e:
                logger.error(f"Bir hata oluştu: {e}")
                await asyncio.sleep(60) # Hata olursa 1 dakika bekle ve tekrar dene

# --- PROGRAMI BAŞLAT ---
if __name__ == "__main__":
    bot = SiberDervisNasreddin()
    try:
        asyncio.run(bot.run_bot())
    except KeyboardInterrupt:
        logger.info("Bot kullanıcı tarafından kapatıldı.")
