import tweepy#!/usr/bin/env python3
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

BRIEFING_FILE = DATA_DIR / "briefing_users.json"
ALARMS_FILE = DATA_DIR / "alarms.json"
TR_TZ = timezone(timedelta(hours=3))

openai_client = OpenAI()

# ─── Bot Mantığı (Önceki versiyondan aktarılanlar) ───────────────────────────
# (Fıkralar, API çağrıları, Sistem Prompt vb. buraya gelecek)
# Not: Kodun kısalığı için fıkralar listesini burada özetliyorum ama tam dosyada hepsi olacak.

SYSTEM_PROMPT = "Sen Nasreddin Hoca'sın. Samimi, bilge ve komik bir Türk AI ajanı."

FIKRALAR = [
    {"baslik": "Kazan Doğurdu", "fikra": "Hoca kazanı geri verirken içine tencere koymuş..."},
    # ... (Diğer 34 fıkra burada yer alacak)
]

# ─── FastAPI Modelleri ──────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    user_id: str = "agent_scan_user"

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

# ─── Bot Uygulaması ─────────────────────────────────────────────────────────
class NasreddinBot:
        # Twitter'a bağlanma ayarı
    def get_twitter_client(self):
        return tweepy.Client(
            consumer_key=os.environ.get("TWITTER_API_KEY"),
            consumer_secret=os.environ.get("TWITTER_API_SECRET"),
            access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET")
        )

    # Tweet atma komutu (Telegram için)
    async def tweet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        tweet_text = " ".join(context.args)
        if not tweet_text:
            await update.message.reply_text("Hocam, ne yazacağımı söylemedin! Örn: /tweet Selam!")
            return
        
        try:
            client = self.get_twitter_client()
            client.create_tweet(text=tweet_text)
            await update.message.reply_text("Tweet başarıyla atıldı, hayırlı olsun!")
        except Exception as e:
            await update.message.reply_text(f"Bir hata çıktı: {e}")
    def __init__(self):
        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("tweet", self.tweet_command))
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Selamünaleyküm hemşerim! Ben Nasreddin.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # AI Yanıt mantığı
        pass

    async def get_ai_reply(self, message: str) -> str:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message}]
        )
        return response.choices[0].message.content

nasreddin = NasreddinBot()

# ─── FastAPI Entegrasyonu ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Botu arka planda başlat
    asyncio.create_task(nasreddin.app.initialize())
    asyncio.create_task(nasreddin.app.start())
    asyncio.create_task(nasreddin.app.updater.start_polling())
    logger.info("Telegram bot polling started via FastAPI lifespan")
    yield
    # Kapatma işlemleri
    await nasreddin.app.updater.stop()
    await nasreddin.app.stop()
    await nasreddin.app.shutdown()

api = FastAPI(title="Nasreddin Hoca API", lifespan=lifespan)

@api.get("/")
async def root():
    return {
        "name": "Nasreddin Hoca AI Bot",
        "description": "Samimi, bilge ve komik Türk AI ajanı",
        "status": "active",
        "version": "2.1"
    }

@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = await nasreddin.get_ai_reply(request.message)
    return ChatResponse(response=reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(api, host="0.0.0.0", port=port)
