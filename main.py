#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import tweepy
from openai import OpenAI

# --- AYARLAR VE API ANAHTARLARI ---
# Render veya yerel ortamdaki Environment Variables'dan çekilir
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

auth = tweepy.OAuth1UserHandler(
    os.getenv("TWITTER_API_KEY"), 
    os.getenv("TWITTER_API_SECRET"),
    os.getenv("TWITTER_ACCESS_TOKEN"), 
    os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
)
api = tweepy.API(auth)
client_v2 = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_key_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
)

# --- HAFIZA YÖNETİMİ (AYNI TWEETE TEKRAR CEVAP VERMEME) ---
REPLIED_FILE = "replied_tweets.txt"

def get_replied_ids():
    if not os.path.exists(REPLIED_FILE):
        return set()
    with open(REPLIED_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_replied_id(tweet_id):
    with open(REPLIED_FILE, "a") as f:
        f.write(f"{tweet_id}\n")

# --- ANA FONKSİYONLAR ---
def generate_hoca_reply(tweet_text):
    system_prompt = (
        "Sen Nasreddin Hoca'sın. Kripto, NFT ve blockchain dünyası hakkında "
        "Türk mizahı, fıkraları ve hazırcevaplığıyla yorumlar yapıyorsun. "
        "ÖNEMLİ KURALLAR: "
        "1. Cevaplarını ASLA tırnak işareti (\" \") içine alma. "
        "2. 'Nasreddin Hoca:' gibi isim ön ekleri kullanma. "
        "3. Doğrudan karakterin kendisi olarak konuş. "
        "4. Esprili, bilge ama hafif iğneleyici ol."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Bu tweete Hoca gibi cevap ver: {tweet_text}"}
            ],
            temperature=0.8
        )
        # Tırnakları ve gereksiz boşlukları temizle
        reply = response.choices[0].message.content.strip().replace('"', '')
        return reply
    except Exception as e:
        print(f"OpenAI Hatası: {e}")
        return None

def check_and_reply():
    print("Yeni tweetler kontrol ediliyor...")
    replied_ids = get_replied_ids()
    
    # Takip ettiğin kelimeler veya mentionlar (Örn: #DeptOfDeath veya @bot_ismin)
    query = "#DeptOfDeath -is:retweet" 
    
    try:
        tweets = client_v2.search_recent_tweets(query=query, max_results=10, tweet_fields=['author_id', 'text'])
        
        if tweets.data:
            for tweet in tweets.data:
                if str(tweet.id) not in replied_ids:
                    print(f"Yeni tweet bulundu: {tweet.text}")
                    
                    hoca_reply = generate_hoca_reply(tweet.text)
                    
                    if hoca_reply:
                        client_v2.create_reply(text=hoca_reply, in_reply_to_tweet_id=tweet.id)
                        save_replied_id(tweet.id)
                        print(f"Cevap gönderildi: {hoca_reply}")
                        time.sleep(10) # Rate limit koruması
                else:
                    print(f"Bu tweete zaten cevap verilmiş: {tweet.id}")
        else:
            print("Yeni tweet yok.")
            
    except Exception as e:
        print(f"Twitter Hatası: {e}")

# --- DÖNGÜ ---
if __name__ == "__main__":
    while True:
        check_and_reply()
        print("60 saniye bekleniyor...")
        time.sleep(60)
