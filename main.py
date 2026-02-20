#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import logging
from datetime import datetime

import tweepy
from openai import OpenAI


# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ---------------- API CLIENTS ----------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

twitter = tweepy.Client(
    bearer_token=os.getenv("TW_BEARER"),
    consumer_key=os.getenv("TW_API_KEY"),
    consumer_secret=os.getenv("TW_API_SECRET"),
    access_token=os.getenv("TW_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TW_ACCESS_SECRET"),
)


# ---------------- CHARACTER PROMPT ----------------
SYSTEM_PROMPT = """
Sen Nasreddin Hoca tarzında konuşan bir AI karakterisin.

Kişiliğin:
- Türk mizahı
- Kripto bilgili
- NFT kültürüne hakim
- Hafif taşlayıcı
- Zeki ve kısa tweet üretir

Kurallar:
- 1 tweet uzunluğu
- Türkçe yaz
- Komik ol
- Hashtag kullan (#crypto #nft #NasreddinAI)
- Emoji olabilir
"""


# ---------------- AI TWEET GENERATOR ----------------
def generate_tweet():

    topic = random.choice([
        "Bitcoin düşüşü",
        "NFT koleksiyonu",
        "Kripto balinaları",
        "Altcoin sezonu",
        "Metaverse",
        "DeFi",
        "Yeni NFT projeleri",
        "Web3 geleceği",
        "Pump dump olayları",
        "Airdrop kovalamak"
    ])

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{topic} hakkında tweet üret"}
            ],
            max_completion_tokens=80
        )

        tweet = response.choices[0].message.content.strip()
        return tweet

    except Exception as e:
        logger.error(f"AI üretim hatası: {e}")
        return None


# ---------------- SEND TWEET ----------------
def send_tweet(text):
    try:
        twitter.create_tweet(text=text)
        logger.info("Tweet atıldı:")
        logger.info(text)

    except Exception as e:
        logger.error(f"Tweet gönderme hatası: {e}")


# ---------------- LOOP ----------------
def run_bot():
    logger.info("Bot başlatıldı 🚀")

    while True:
        tweet = generate_tweet()

        if tweet:
            send_tweet(tweet)

        wait = random.randint(5, 10)  # 4-6 saat
        logger.info(f"{wait} saniye bekleniyor...")
        time.sleep(wait)


# ---------------- START ----------------
if __name__ == "__main__":
    run_bot()
