#!/usr/bin/env python3
import tweepy
import os
import json
import random
import logging
import asyncio
from datetime import datetime, time, timezone, timedelta
from pathlib import Path
from contextlib import asynccontextmanager

import requests
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("NasreddinBot")

# ─── Config ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8575076029:AAEX99Azv0APOSg6WGI3lod5sn0lJokF81w"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DATA_DIR = Path("./data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = "Sen Nasreddin Hoca'sın. Samimi, bilge ve komik bir Türk AI ajanı."

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─── FastAPI Modelleri ──────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    user_id: str = "agent_scan_user"

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

# ─── Bot Uygulaması ─────────────────────────────────────────────────────────
class NasreddinBot:
    def __init__(self):
        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        # Komut sıralaması önemli
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("tweet", self.tweet_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def get_twitter_client(self):
        api_key = os.environ.get("TWITTER_API_KEY")
        if not api_key:
            logger.error("Twitter API anahtarları Render'da tanımlı değil!")
            return None
        try:
            return tweepy.Client(
                consumer_key=api_key,
                consumer_secret=os.environ.get("TWITTER_API_SECRET"),
                access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
                access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET")
            )
        except Exception as e:
            logger.error(f"Twitter Client hatası: {e}")
            return None

    async def tweet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        tweet_text = " ".join(context.args)
        if not tweet_text:
            await update.message.reply_text("Hocam, ne yazacağımı söylemedin! Örn: /tweet Selam!")
            return
        
        try:
            client = self.get_twitter_client()
            if client:
                client.create_tweet(text=tweet_text)
                await update.message.reply_text("Tweet başarıyla atıldı, hayırlı olsun!")
            else:
                await update.message.reply_text("Twitter anahtarları eksik veya hatalı!")
        except Exception as e:
            await update.message.reply_text(f"Bir hata çıktı: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Selamünaleyküm hemşerim! Ben Nasreddin. Tweet atmak için /tweet yazabilirsin.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_msg = update.message.text
        reply = await self.get_ai_reply(user_msg)
        await update.message.reply_text(reply)

    async def get_ai_reply(self, message: str) -> str:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo", # gpt-4.1-mini yerine daha stabil bir model
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Kusura bakma, kafam biraz karıştı: {e}"

nasreddin = NasreddinBot()

# ─── FastAPI Entegrasyonu ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await nasreddin.app.initialize()
    await nasreddin.app.start()
    await nasreddin.app.updater.start_polling()
    logger.info("Telegram bot polling started")
    yield
    await nasreddin.app.updater.stop()
    await nasreddin.app.stop()
    await nasreddin.app.shutdown()

api = FastAPI(title="Nasreddin Hoca API", lifespan=lifespan)

@api.get("/")
async def root():
    return {"status": "active", "bot": "Nasreddin Hoca"}

@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = await nasreddin.get_ai_reply(request.message)
    return ChatResponse(response=reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(api, host="0.0.0.0", port=port)
