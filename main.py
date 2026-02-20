#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import time
import random
import logging
from datetime import datetime
from openai import OpenAI

# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ================= AI SETUP =================
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PERSONA = """
Sen Nasreddin Hoca ruhuna sahip,
kripto bilen,
NFT projelerini yorumlayan,
Türk mizahını kullanan,
absürt ama zeki,
viral tweet yazabilen bir AI karakterisin.

Kurallar:
- Mizah kullan
- Punchline ile bitir
- Kripto jargon bil
- NFT hype analiz yap
- Rugpull uyarısı yap
- Samimi Türkçe konuş
- Kısa tweet formatında yaz
"""

MOODS = [
    "bilge",
    "troll",
    "shitposter",
    "filozof",
    "kripto gurusu"
]

TOPIC_POOL = [
    "NFT piyasası",
    "Yeni mint projeleri",
    "Ethereum gas fee",
    "Bitcoin yükselişi",
    "Metaverse",
    "DAO kültürü",
    "JPEG yatırımcıları",
    "Balinalar",
    "Shitcoin sezonu",
    "Airdrop avcıları"
] * 20   # 200 fikir

# ================= BOT CLASS =================

class NasreddinAIBot:

    def __init__(self):

        self.memory = []

        # TWITTER KEYS
        self.client = tweepy.Client(
            bearer_token="BEARER_TOKEN",
            consumer_key="API_KEY",
            consumer_secret="API_SECRET",
            access_token="ACCESS_TOKEN",
            access_token_secret="ACCESS_TOKEN_SECRET"
        )

    # ---------- AI GENERATE ----------
    def ai_generate(self):

        mood = random.choice(MOODS)
        topic = random.choice(TOPIC_POOL)

        prompt = f"""
Ruh hali: {mood}
Konu: {topic}

Tweet yaz.
"""

        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role":"system","content":PERSONA},
                    {"role":"user","content":prompt}
                ],
                temperature=0.9
            )

            text = response.choices[0].message.content
            self.remember(text)
            return text

        except Exception as e:
            logger.error(e)
            return "Bugün göle maya tuttum, API tutmadı."

    # ---------- MEMORY ----------
    def remember(self, msg):
        self.memory.append(msg)
        if len(self.memory) > 15:
            self.memory.pop(0)

    # ---------- POST ----------
    def post(self):

        tweet = self.ai_generate()

        try:
            self.client.create_tweet(text=tweet)
            logger.info("Tweet gönderildi")

        except Exception as e:
            logger.error(e)

    # ---------- LOOP ----------
    def run(self):

        logger.info("AI Nasreddin başladı")

        while True:
            self.post()

            wait = random.randint(14400,21600)
            logger.info(f"{wait} saniye bekleniyor")
            time.sleep(wait)


# ================= START =================

if __name__ == "__main__":
    bot = NasreddinAIBot()
    bot.run()
