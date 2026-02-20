#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import random
import logging
import base64
import requests

import tweepy
from openai import OpenAI


# ================= LOG =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger()


# ================= BOT =================
class HocaUltra:

    def __init__(self):

        # --- KEYS ---
        self.api_key=os.getenv("TW_API_KEY")
        self.api_secret=os.getenv("TW_API_SECRET")
        self.access=os.getenv("TW_ACCESS_TOKEN")
        self.access_secret=os.getenv("TW_ACCESS_SECRET")
        self.bearer=os.getenv("TW_BEARER")

        self.ai=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.last_mentions=None

        # --- Persona ---
        self.moods={
            "bilge":1,
            "troll":1,
            "absurt":1,
            "kriptofilozof":1,
            "nftseyyah":1
        }

        self.nft_list=[
            "Azuki","Doodles","Pudgy Penguins",
            "CoolCats","BoredApes"
        ]

        self.influencers=[
            "cz_binance",
            "VitalikButerin",
            "garyvee"
        ]

    # ================= TWITTER CLIENT =================
    def client(self):
        return tweepy.Client(
            bearer_token=self.bearer,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access,
            access_token_secret=self.access_secret
        )

    def media_api(self):
        auth=tweepy.OAuth1UserHandler(
            self.api_key,
            self.api_secret,
            self.access,
            self.access_secret
        )
        return tweepy.API(auth)

    # ================= MARKET =================
    def btc(self):
        try:
            r=requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            ).json()
            return r["bitcoin"]["usd"]
        except:
            return "?"

    def market(self):
        gold=random.randint(1800,2600)
        bist=random.randint(7000,12000)
        return f"BTC:{self.btc()}$ ALTIN:{gold}$ BIST:{bist}"

    # ================= AI =================
    def mood_pick(self):
        pool=[]
        for m,w in self.moods.items():
            pool += [m]*w
        return random.choice(pool)

    def evolve(self,m):
        self.moods[m]+=1

    def ai_tweet(self,mood,market,nft):
        prompt=f"""
Modern Nasreddin Hoca'sın.
Türk mizahı yap.
Kripto, NFT, borsa biliyorsun.

Mood:{mood}
Market:{market}
NFT:{nft}

Tweet yaz 280 karakter
"""
        try:
            r=self.ai.responses.create(
                model="gpt-5-mini",
                input=prompt,
                max_output_tokens=120
            )
            return r.output_text
        except:
            return "Eşeğe sordum piyasayı, long dedi 🫏"

    def ai_reply(self,text):
        prompt=f"""
Nasreddin Hoca karakterinde eğlenceli cevap yaz:

{text}
"""
        try:
            r=self.ai.responses.create(
                model="gpt-5-mini",
                input=prompt,
                max_output_tokens=80
            )
            return r.output_text
        except:
            return "Hoca düşündü ama cevap vermedi 🙂"

    # ================= IMAGE =================
    def image(self,prompt):
        try:
            img=self.ai.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024"
            )
            b=base64.b64decode(img.data[0].b64_json)
            with open("img.png","wb") as f:
                f.write(b)
            return "img.png"
        except:
            return None

    # ================= POST =================
    def tweet(self,text):
        self.client().create_tweet(text=text)

    def tweet_img(self,text,img):
        m=self.media_api().media_upload(img)
        self.client().create_tweet(
            text=text,
            media_ids=[m.media_id]
        )

    # ================= VIRAL =================
    def hashtags(self):
        tags=[
            "#Bitcoin","#NFT","#Web3",
            "#Kripto","#Borsa","#Altcoin"
        ]
        return " ".join(random.sample(tags,2))

    # ================= MENTIONS =================
    def reply_mentions(self):
        try:
            c=self.client()
            mentions=c.get_users_mentions(id=c.get_me().data.id)

            if mentions.data:
                for m in mentions.data:
                    if self.last_mentions==m.id:
                        return
                    r=self.ai_reply(m.text)
                    c.create_tweet(
                        text=r,
                        in_reply_to_tweet_id=m.id
                    )
                    self.last_mentions=m.id
        except:
            pass

    # ================= INFLUENCER WATCH =================
    def watch(self):
        try:
            c=self.client()
            for name in self.influencers:
                u=c.get_user(username=name)
                tweets=c.get_users_tweets(id=u.data.id,max_results=5)
                if tweets.data:
                    if random.random()>0.7:
                        t=random.choice(tweets.data)
                        self.tweet(
                            f"@{name} bunu dedi ki:\n{t.text[:150]}"
                        )
        except:
            pass

    # ================= LOOP =================
    def run(self):

        log.info("ULTRA BOT START")

        while True:
            try:

                self.reply_mentions()
                self.watch()

                mood=self.mood_pick()
                nft=random.choice(self.nft_list)
                market=self.market()

                txt=self.ai_tweet(mood,market,nft)
                final=f"{txt}\n\n📊 {market}\n🎨 {nft}\n{self.hashtags()}"

                if random.random()>0.5:
                    img=self.image(
                        f"Nasreddin hoca nft crypto art {mood}"
                    )
                    if img:
                        self.tweet_img(final,img)
                    else:
                        self.tweet(final)
                else:
                    self.tweet(final)

                self.evolve(mood)

                wait=random.randint(1800,7200)
                log.info(f"{wait}s sleep")
                time.sleep(wait)

            except Exception as e:
                log.error(e)
                time.sleep(120)


# ================= START =================
if __name__=="__main__":
    HocaUltra().run()
