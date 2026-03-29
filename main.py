import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

app = Flask(__name__)

telegram_app = Application.builder().token(BOT_TOKEN).build()

# ✅ FIXED START FUNCTION
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"

    user = users.find_one({"user_id": user_id})

    if user:
        await update.message.reply_text(
            f"👋 Welcome back {username}!\n\n💰 Balance: {user.get('balance', 0)}\n👥 Referrals: {user.get('referrals', 0)}"
        )
    else:
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "referrals": 0
        })

        await update.message.reply_text("✅ You are registered!")

telegram_app.add_handler(CommandHandler("start", start))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json(force=True)

    update = Update.de_json(json_data, telegram_app.bot)

    import asyncio
    asyncio.run(telegram_app.process_update(update))

    return "ok"

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    import asyncio

    async def setup():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

    asyncio.run(setup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
