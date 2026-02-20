#!/usr/bin/env python3
import tweepy
import os
import logging
import asyncio
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# ─── LOGGING AYARLARI ──────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("NasreddinAI_Agent")

# ─── YAPILANDIRMA & API ANAHTARLARI ────────────────────────────────────────
# Not: Bu anahtarları Render'da Environment Variables olarak tanımlamalısın.
TELEGRAM_TOKEN = "8575076029:AAEX99Azv0APOSg6WGI3lod5sn0lJokF81w"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
SYSTEM_PROMPT = (
    "Sen Nasreddin Hoca'sın. Samimi, bilge, iğneleyici ve çok komik bir Türk AI ajanımsın. "
    "Kripto para piyasasını (Bitcoin, Ethereum vb.) bir köylü bilgeliğiyle yorumluyorsun. "
    "Eşeğe ters binmek, kazan doğurması, göle maya çalmak gibi Nasreddin Hoca fıkralarına atıfta bulunursun."
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─── GLOBAL DEĞİŞKENLER (Fiyat Takibi İçin) ──────────────────────────────────
last_checked_price = None

# ─── BOT SINIFI ─────────────────────────────────────────────────────────────
class NasreddinBot:
    def __init__(self):
        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("tweet", self.tweet_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def get_twitter_client(self):
        try:
            return tweepy.Client(
                consumer_key=os.environ.get("TWITTER_API_KEY"),
                consumer_secret=os.environ.get("TWITTER_API_SECRET"),
                access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
                access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET")
            )
        except Exception as e:
            logger.error(f"Twitter Client hatası: {e}")
            return None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Selamünaleyküm ahali! Ben Nasreddin Hoca. Piyasayı izliyorum, eşeği sağlam kazığa bağladık! 🌙")

    async def tweet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        tweet_text = " ".join(context.args)
        if not tweet_text:
            await update.message.reply_text("Hocam, ne yazacağımı söylemedin!")
            return
        client = self.get_twitter_client()
        if client:
            client.create_tweet(text=tweet_text)
            await update.message.reply_text("Tweet başarıyla atıldı! ✅")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": update.message.text}]
            )
            await update.message.reply_text(response.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"Kafam karıştı evlat: {e}")

nasreddin = NasreddinBot()

# ─── PİYASA & AI FONKSİYONLARI ──────────────────────────────────────────────

def get_btc_price():
    """Binance'den güncel BTC fiyatını çeker."""
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        res = requests.get(url, timeout=10).json()
        return float(res['price'])
    except Exception as e:
        logger.error(f"Fiyat çekme hatası: {e}")
        return None

async def send_ai_tweet(custom_prompt):
    """AI'dan tweet metni alır ve Twitter'da paylaşır."""
    # Hashtag kuralını prompt'a ekliyoruz
    full_prompt = custom_prompt + " Tweetin sonuna mutlaka #Bitcoin #Kripto #NasreddinHoca etiketlerini ekle. Maksimum 280 karakter."
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": full_prompt}]
        )
        tweet_text = response.choices[0].message.content.strip()
        
        client = nasreddin.get_twitter_client()
        if client:
            client.create_tweet(text=tweet_text)
            logger.info(f"Tweet Atıldı: {tweet_text}")
    except Exception as e:
        logger.error(f"Tweet gönderme hatası: {e}")

# ─── ZAMANLANMIŞ GÖREVLER (SCHEDULER JOBS) ──────────────────────────────────

def job_scheduled_tweet():
    """Sabah, öğle, akşam rutin tweetleri."""
    price = get_btc_price()
    price_str = f"Şu an Bitcoin ${price:,.0f}." if price else ""
    prompt = f"{price_str} Günün bu saatinde piyasa hakkında bilgece ve komik bir yorum yap."
    asyncio.run(send_ai_tweet(prompt))

def job_price_movement_check():
    """Sert fiyat hareketlerini kontrol eder (%2 ve üzeri)."""
    global last_checked_price
    current_price = get_btc_price()
    
    if current_price and last_checked_price:
        change = ((current_price - last_checked_price) / last_checked_price) * 100
        
        if abs(change) >= 2.0: # %2 ve üzeri değişim
            durum = "fırladı, kazan doğurdu! 🚀" if change > 0 else "çakıldı, kazan öldü! 📉"
            prompt = f"Bitcoin fiyatı aniden %{abs(change):.1f} {durum} Şu an ${current_price:,.0f}. Çok şaşırmış veya heyecanlanmış bir Nasreddin Hoca tweeti yaz."
            asyncio.run(send_ai_tweet(prompt))
            
    last_checked_price = current_price

# ─── ZAMANLAYICI BAŞLATMA ───────────────────────────────────────────────────
scheduler = BackgroundScheduler()

# 1. Rutin Tweetler (TSİ 09:00, 15:00, 21:00) - UTC saatleri kullanılmıştır
scheduler.add_job(job_scheduled_tweet, 'cron', hour=6, minute=0)
scheduler.add_job(job_scheduled_tweet, 'cron', hour=12, minute=0)
scheduler.add_job(job_scheduled_tweet, 'cron', hour=18, minute=0)

# 2. Fiyat Hareket Kontrolü (Her 15 dakikada bir)
scheduler.add_job(job_price_movement_check, 'interval', minutes=15)

scheduler.start()

# ─── FASTAPI & LIFESPAN ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Botu başlat
    await nasreddin.app.initialize()
    await nasreddin.app.start()
    await nasreddin.app.updater.start_polling()
    logger.info("Nasreddin AI Ajanı Göreve Başladı!")
    yield
    # Botu durdur
    await nasreddin.app.updater.stop()
    await nasreddin.app.stop()

api = FastAPI(lifespan=lifespan)

@api.get("/")
async def root():
    return {"status": "online", "character": "Nasreddin Hoca", "btc_price": get_btc_price()}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(api, host="0.0.0.0", port=port)
