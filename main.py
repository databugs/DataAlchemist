from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder
from os import getenv
from bot import conversation_handler

TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    raise ValueError('TELEGRAM_TOKEN is not set')

app = FastAPI()
bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

bot.add_handler(conversation_handler)

@app.post("/webhook/{token}")
async def telegram_webhook(token: str, update: Update):
    await bot.process_update(update)

bot.run_webhook(url_path="https://your-app.com/webhook/{token}")