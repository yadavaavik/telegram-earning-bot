import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient

# ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# Flask App
app = Flask(__name__)

# Telegram Bot App
telegram_app = Application.builder().token(BOT_TOKEN).build()

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    user = users.find_one({"user_id": user_id})

    if not user:
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "referrals": 0
        })

    await update.message.reply_text(
        f"👋 Welcome {username}!\n\n💰 Balance: 0\n👥 Referrals: 0"
    )

telegram_app.add_handler(CommandHandler("start", start))

# WEBHOOK ROUTE
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"

# HOME ROUTE
@app.route("/")
def home():
    return "Bot is running!"

# START SERVER
if __name__ == "__main__":
    import asyncio

    async def setup():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

    asyncio.run(setup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
