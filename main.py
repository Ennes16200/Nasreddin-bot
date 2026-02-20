#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import time
import random
import logging
from datetime import datetime

# --- LOGGING AYARLARI ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hoca_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NasreddinBot:
    def __init__(self):
        # --- TWITTER API BİLGİLERİ ---
        # Burayı kendi bilgilerine göre doldurmayı unutma!
        self.api_key = "QYMKqttYnTsx8cMok3ZAyX3jT"
        self.api_secret = "BVMX6xg35Ujn2I1b5XeARdw8exGRRiX4TVEBstXX5TEFGCrPuA"
        self.access_token = "2024178599994212352-JLWzVqyzSbrrJS8UvKaijnEjJTlaQZ"
        self.access_token_secret = "iAgTL0djRZeOMAioCndkeppNiU240m11njgJJLyZpLEpo"
        self.bearer_token = "AAAAAAAAAAAAAAAAAAAAAOHm7gEAAAAA7k%2B%2FXNpdC8mQaT0E826AD1WX4cw%3DLaYxWB7HcdmRDa8gQ3JysGmeOmhbNY6nheQ2L54GmgNUPn9cv0"

        # --- BİLGELİK HAVUZU ---
        self.wisdom_pool = [
            "Blockchain tabanlı semaver: Her blokta bir çay demler, gas ücretiyle şeker alır.",
            "Eşeğin semerine takılan madencilik cihazı: Yürüdükçe Satoshi, durdukça dert üretir.",
            "Akıllı kontratla kız isteme: Başlık parası USDT ile ödenir.",
            "Metaverse'de cuma namazı çıkışı lokma dağıtımı yapıyoruz, bekleriz.",
            "Kazan doğurdu diyen balinaya, kazan öldü diyen küçük yatırımcı (Exit Liquidity).",
            "Eşeğe ters binip ayı piyasasında geri geri gitmek: 'Ben düşmüyorum, dünya yükseliyor'.",
            "Gölü mayalarken 'Ya tutarsa' diyen ilk DeFi kurucusu Nasreddin Hoca'dır.",
            "Parayı veren düdüğü çalar: Balinalar çalar, planktonlar oynar.",
            "Ye kürküm ye: Sadece mavi tiki olanlara airdrop yapan protokoller utansın."
        ]

    def connect_twitter(self):
        """Twitter API v2 bağlantısı kurar."""
        try:
            client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            logger.info("Twitter bağlantısı başarılı.")
            return client
        except Exception as e:
            logger.error(f"Bağlantı hatası: {e}")
            return None

    def tweet_at(self):
        """Rastgele bir tweet gönderir."""
        client = self.connect_twitter()
        if not client:
            return

        mesaj = random.choice(self.wisdom_pool)
        tarih = datetime.now().strftime("%H:%M")
        tam_mesaj = f"💡 Hoca Der Ki ({tarih}): {mesaj} #NasreddinAI #Web3"

        try:
            # GERÇEK TWEET ATMAK İÇİN AŞAĞIDAKİ SATIRIN BAŞINDAKİ '#' İŞARETİNİ SİL:
            # client.create_tweet(text=tam_mesaj)
            logger.info(f"Tweet Hazırlandı: {tam_mesaj}")
        except Exception as e:
            logger.error(f"Tweet gönderilirken hata oluştu: {e}")

    def calistir(self):
        """Botu döngüye sokar."""
        logger.info("Nasreddin Hoca Botu Başlatıldı!")
        while True:
            self.tweet_at()
            
            # 6 saat bekler (6 saat * 60 dakika * 60 saniye = 21600 saniye)
            # Test için burayı 30 yapabilirsin (30 saniyede bir çalışır).
            logger.info("Bir sonraki tweet için bekleniyor...")
            time.sleep(21600)

if __name__ == "__main__":
    bot = NasreddinBot()
    bot.calistir()
