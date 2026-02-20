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

# ========= LOG =========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========= OPENAI =========
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========= TWITTER =========
twitter = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
)

# ========= NFT DATA =========
COLLECTIONS = [
    "boredapeyachtclub",
    "azuki",
    "doodles-official",
    "pudgypenguins"
]

def get_real_floor():
    try:
        slug = random.choice(COLLECTIONS)
        url = f"https://api.opensea.io/api/v2/collections/{slug}/stats"
        r = requests.get(url)
        data = r.json()
        floor = data["stats"]["floor_price"]
        volume = data["stats"]["total_volume"]
        return slug, floor, volume
    except:
        # API başarısız olursa rastgele floor ve volume
        slug = random.choice(COLLECTIONS)
        floor = round(random.uniform(0.3,1.7),2)
        volume = round(random.uniform(100,10000),0)
        return slug, floor, volume

# ========= WHALE ANALYZER =========
def whale_signal(volume):
    score = 0
    if volume > 5000:
        score += 2
    if random.random() > 0.7:
        score += 1
    signals = [
        "balinalar sessizce topluyor",
        "dump hazırlığı kokusu var",
        "hacim köpürmüş gibi",
        "likidite oyunları dönüyor"
    ]
    return score, random.choice(signals)

# ========= TREND ENGINE =========
def trend_prediction(floor, whale_score):
    trend = floor * random.uniform(0.8,1.2) + whale_score
    if trend > 3:
        return "Yükseliş ihtimali güçlü"
    elif trend > 1.5:
        return "Dalgalı ama umut var"
    else:
        return "Hoca eşeğe binmez bu piyasada"

# ========= AI TWEET =========
def generate_tweet():
    slug, floor, volume = get_real_floor()
    whale_score, whale_text = whale_signal(volume)
    trend = trend_prediction(floor, whale_score)

    prompt = f"""
Sen Nasreddin Hoca ruhuna sahip kripto filozofu AI'sın.
NFT Koleksiyon: {slug}
Floor: {floor}
Hacim: {volume}
Whale analiz: {whale_text}
Trend tahmini: {trend}
Türk mizahı, zeka ve taşlama içeren tweet yaz. Max 260 karakter.
"""

    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_completion_tokens=120
    )

    return response.choices[0].message.content.strip()

# ========= TWEET GUARD =========
tweet_times = []
TWEET_LIMIT_PER_HOUR = 20

def can_tweet():
    global tweet_times
    now = datetime.now()
    tweet_times = [t for t in tweet_times if now - t < timedelta(hours=1)]
    if len(tweet_times) < TWEET_LIMIT_PER_HOUR:
        tweet_times.append(now)
        return True
    return False

def send_tweet(text):
    if can_tweet():
        try:
            twitter.create_tweet(text=text)
            logger.info("Tweet sent: %s", text)
        except Exception as e:
            logger.error("Twitter fail: %s", e)
    else:
        logger.info("Rate limit reached, tweet skipped")

# ========= WATCHDOG =========
start_time = time.time()
RESTART_INTERVAL = 60*60*6
MAX_MEMORY_MB = 450
import psutil

def memory_guard():
    mem = psutil.Process(os.getpid()).memory_info().rss / 1024 /1024
    if mem > MAX_MEMORY_MB:
        logger.warning("Memory exceeded -> Restarting")
        os._exit(1)

def restart_watchdog():
    if time.time() - start_time > RESTART_INTERVAL:
        logger.info("Scheduled restart")
        os._exit(1)

# ========= MAIN LOOP =========
logger.info("NFT/AI Twitter Bot STARTED")

while True:
    try:
        restart_watchdog()
        memory_guard()
        tweet_text = generate_tweet()
        send_tweet(tweet_text)
        wait = random.randint(1800,7200)
        logger.info(f"{wait} saniye bekleniyor")
        time.sleep(wait)
    except Exception as e:
        logger.error("Crash caught: %s", e)
        time.sleep(30)
