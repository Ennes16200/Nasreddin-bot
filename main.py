#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import random
import logging
import psutil
import requests
from datetime import datetime, timedelta
from openai import OpenAI
import tweepy

# =========================
# CONFIG
# =========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TW_API_KEY = os.getenv("TW_API_KEY")
TW_API_SECRET = os.getenv("TW_API_SECRET")
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TW_ACCESS_SECRET")

RESTART_INTERVAL = 60 * 60 * 6
MAX_MEMORY_MB = 450
TWEET_LIMIT_PER_HOUR = 10
PERSONA_FILE = "persona.json"

LOOP_MIN = 1800
LOOP_MAX = 7200

# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================
# OPENAI
# =========================

client_ai = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# TWITTER
# =========================

client_twitter = tweepy.Client(
    consumer_key=TW_API_KEY,
    consumer_secret=TW_API_SECRET,
    access_token=TW_ACCESS_TOKEN,
    access_token_secret=TW_ACCESS_SECRET
)

# =========================
# MEMORY GUARD
# =========================

def memory_guard():
    mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    if mem > MAX_MEMORY_MB:
        logging.warning("Memory exceeded -> Restarting")
        os._exit(1)

# =========================
# WATCHDOG
# =========================

start_time = time.time()

def restart_watchdog():
    if time.time() - start_time > RESTART_INTERVAL:
        logging.info("Scheduled restart")
        os._exit(1)

# =========================
# RATE LIMIT
# =========================

tweet_times = []

def can_tweet():
    global tweet_times
    now = datetime.now()
    tweet_times = [t for t in tweet_times if now - t < timedelta(hours=1)]
    if len(tweet_times) < TWEET_LIMIT_PER_HOUR:
        tweet_times.append(now)
        return True
    return False

# =========================
# PERSONA MEMORY
# =========================

def load_persona():
    if os.path.exists(PERSONA_FILE):
        with open(PERSONA_FILE,"r") as f:
            return json.load(f)
    return {"history":[]}

def save_persona(p):
    with open(PERSONA_FILE,"w") as f:
        json.dump(p,f)

persona = load_persona()

# =========================
# DATA SOURCES
# =========================

def get_gold_price():
    try:
        r = requests.get("https://api.metals.live/v1/spot/gold")
        return float(r.json()[0]["price"])
    except:
        return None

def get_nft_floor():
    # Buraya OpenSea API ekleyebiliriz
    return round(random.uniform(0.3, 1.7),2)

# =========================
# AI ENGINE
# =========================

def generate_tweet(gold, nft):

    system_prompt = """
Sen Nasreddin Hoca tarzında konuşan,
NFT bilen,
Kripto kültürüne hakim,
Türk mizahı yapan,
Altın ve BIST yorumlayan
bilge bir trader karakterisin.
"""

    user_prompt = f"""
Altın fiyatı: {gold}
NFT floor: {nft}
Buna göre 280 karakterlik eğlenceli tweet yaz.
"""

    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        max_completion_tokens=300
    )

    return response.choices[0].message.content.strip()

# =========================
# TWEET
# =========================

def send_tweet(text):
    if not can_tweet():
        logging.info("Rate limit reached")
        return

    try:
        client_twitter.create_tweet(text=text)
        logging.info("Tweet sent")
    except Exception as e:
        logging.error(f"Twitter error: {e}")

# =========================
# MAIN LOOP
# =========================

logging.info("BOT STARTED")

while True:
    try:
        restart_watchdog()
        memory_guard()

        gold = get_gold_price()
        nft = get_nft_floor()

        if gold is None:
            gold = "veri yok"

        tweet_text = generate_tweet(gold, nft)

        send_tweet(tweet_text)

        persona["history"].append(tweet_text)
        persona["history"] = persona["history"][-20:]
        save_persona(persona)

        wait_time = random.randint(LOOP_MIN, LOOP_MAX)
        logging.info(f"Sleeping {wait_time} seconds")

        time.sleep(wait_time)

    except Exception as e:
        logging.error(f"Crash caught: {e}")
        time.sleep(30)
