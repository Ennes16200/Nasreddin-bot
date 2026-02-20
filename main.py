#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import os
import logging
import asyncio
import requests
import random
import time
from datetime import datetime

# --- LOGGING AYARLARI ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("hoca_bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class SiberDervisNasreddin:
    def __init__(self):
        self.bot_name = "Siber-Derviş Nasreddin AI"
        self.version = "4.0.0-FULL-INTEGRATED"
        
        # --- TWITTER API AYARLARI (Burayı doldurabilirsin) ---
        self.auth_keys = {
            "api_key": os.getenv("TWITTER_API_KEY", "QYMKqttYnTsx8cMok3ZAyX3jT"),
            "api_secret": os.getenv("TWITTER_API_SECRET", "BVMX6xg35Ujn2I1b5XeARdw8exGRRiX4TVEBstXX5TEFGCrPuA"),
            "access_token": os.getenv("TWITTER_ACCESS_TOKEN", "2024178599994212352-JLWzVqyzSbrrJS8UvKaijnEjJTlaQZ"),
            "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "iAgTL0djRZeOMAioCndkeppNiU240m11njgJJLyZpLEpo"),
            "bearer_token": os.getenv("TWITTER_BEARER_TOKEN", "AAAAAAAAAAAAAAAAAAAAAOHm7gEAAAAA7k%2B%2FXNpdC8mQaT0E826AD1WX4cw%3DLaYxWB7HcdmRDa8gQ3JysGmeOmhbNY6nheQ2L54GmgNUPn9cv0")
        }
        
        # --- 200+ FİKİR VE KONSEPT HAVUZU ---
        self.wisdom_pool = {
            "TEKNOLOJI": [
                "Blockchain tabanlı semaver: Her blokta bir çay demler, gas ücretiyle şeker alır.",
                "Eşeğin semerine takılan madencilik cihazı: Yürüdükçe Satoshi, durdukça dert üretir.",
                "Akıllı kontratla kız isteme: Başlık parası USDT ile ödenir, boşanma olursa burn edilir.",
                "Metaverse'de cuma namazı çıkışı lokma dağıtımı: Sadece cüzdanında 'HAYIR' token olanlara.",
                "Kuantum tespih: Aynı anda hem çekildi hem çekilmedi, gözlemleyene kadar sevabı belli değil.",
                "Siber-İstihare: Rüyada hangi altcoinin pump yapacağını görmek için soğuk cüzdanı yastık altına koymak.",
                "Dijital Muska: Cüzdanı hacklenmeye karşı koruyan 256-bitlik şifreli dua.",
                "Kamyon arkası siber sözler: 'Rampaların ustasıyım, Bitcoin'in hastasıyım'."
            ],
            "PIYASA_FELSEFESI": [
                "Kazan doğurdu diyen balinaya, kazan öldü diyen küçük yatırımcı (Exit Liquidity).",
                "Eşeğe ters binip ayı piyasasında geri geri gitmek: 'Ben düşmüyorum, dünya yükseliyor'.",
                "Gölü mayalarken 'Ya tutarsa' diyen ilk DeFi kurucusu.",
                "Parayı veren düdüğü çalar: Balinalar çalar, planktonlar oynar.",
                "Ye kürküm ye: Sadece mavi tiki olanlara airdrop yapan protokoller.",
                "Dünyanın merkezi burasıdır: Akşehir değil, senin cüzdanındaki Mainnet ağıdır."
            ],
            "SOSYAL_YASAM": [
                "Kripto altın günü: Her ay bir müritin cüzdanına 1 SOL atılır.",
                "Mahalle baskısı: 'Oğlum bak Vitalik bile evlendi, sen hala shitcoin peşindesin'.",
                "Sünnet konvoyu: Tesla'larla yapılan Dogecoin kutlaması.",
                "Gurbetçi tokeni: Euro ile alınıp köy kahvesinde shill'lenen coin.",
                "Siber-Tekke: Discord'da toplanıp 'HODL' zikri çekmek."
            ]
        }
        
        # 200 Fikri tamamlayan otomatik jeneratör
        self.extra_ideas = [
            f"Fikir #{i}: {random.choice(['Siber', 'Mistik', 'Anadolu', 'Kuantum', 'Dijital'])} "
            f"{random.choice(['Semaver', 'Heybe', 'Kavuk', 'Asa', 'Nal'])} ile "
            f"{random.choice(['Analiz', 'Ritüel', 'Madencilik', 'Airdrop', 'Swap'])} yapma."
            for i in range(1, 180)
        ]

    # --- TWITTER BAĞLANTI MODÜLÜ ---
    def connect_twitter(self):
        try:
            client = tweepy.Client(
                bearer_token=self.auth_keys["bearer_token"],
                consumer_key=self.auth_keys["api_key"],
                consumer_secret=self.auth_keys["api_secret"],
                access_token=self.auth_keys["access_token"],
                access_token_secret=self.auth_keys["access_token_secret"]
            )
            logger.info("Twitter bağlantısı başarılı.")
            return client
        except Exception as e:
            logger.error(f"Twitter bağlantı hatası: {e}")
            return None

    # --- FONKSİYONEL MODÜLLER ---
    def gol_mayala(self):
        chance = random.randint(0, 100)
        if chance > 85:
            return "📢 MÜJDE! Akşehir Gölü maya tuttu! Bitcoin 100.000$, herkes kaşığını alsın gelsin! #Bitcoin #NasreddinAI"
        return "📉 Maya tutmadı ama gölün suyuyla güzel bir Testnet çayı demleriz artık. #Crypto #Web3"

    def esek_ters_indikatoru(self):
        trends = ["Aşırı Boğa", "Ayı", "Yatay", "Kaos"]
        current_trend = random.choice(trends)
        responses = {
            "Aşırı Boğa": "🐂 Herkes 'Ay'a gidiyoruz' diyor. Ben eşeğe ters bindim, uçuruma gidiyoruz!",
            "Ayı": "🐻 Ayı geldi diyorlar, ben heybemde bal saklıyorum. Kışın sonu bahardır.",
            "Yatay": "🐢 Piyasa benim eşekten yavaş ilerliyor.",
            "Kaos": "🌀 Ortalık pazar yeri gibi karışık!"
        }
        return f"📊 Durum: {current_trend} | Hoca: {responses[current_trend]}"

    def rastgele_ogut(self):
        all_wisdom = sum(self.wisdom_pool.values(), []) + self.extra_ideas
        return f"💡 Hoca Der Ki: {random.choice(all_wisdom)}"

    # --- ASYNC ÇALIŞMA DÖNGÜSÜ ---
    async def run_bot(self):
        logger.info(f"{self.bot_name} başlatılıyor...")
        twitter_client = self.connect_twitter()
        
        while True:
            try:
                # Paylaşılacak içeriği oluştur
                content = f"{self.rastgele_ogut()}\n\n{self.esek_ters_indikatoru()}"
                
                # Logla ve Terminale Yaz
                logger.info(f"Paylaşılıyor: {content}")
                
                # Twitter'da Paylaş (Eğer bağlantı varsa)
                if twitter_client:
                    # twitter_client.create_tweet(text=content) # Gerçek paylaşım için yorumu kaldır
                    logger.info("Tweet simüle edildi (API aktifse create_tweet çalışır).")
                
                # Göl mayalama kontrolü
                if random.random() < 0.1: # %10 şansla göl mayala
                    logger.info(self.gol_mayala())

                # 6 saatte bir paylaşım yap (21600 saniye)
                await asyncio.sleep(21600) 
                
            except Exception as e:
                logger.error(f"Döngü hatası: {e}")
                await asyncio.sleep(60)

# --- ANA GİRİŞ ---
if __name__ == "__main__":
    hoca_bot = SiberDervisNasreddin()
    
    # Asyncio ile botu çalıştır
    try:
        asyncio.run(hoca_bot.run_bot())
    except KeyboardInterrupt:
        logger.info("Bot kullanıcı tarafından durduruldu.")
