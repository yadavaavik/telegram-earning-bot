import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient

# ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# MongoDB
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# Flask
app = Flask(__name__)

# Telegram App
telegram_app = Application.builder().token(BOT_TOKEN).build()

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"

    args = context.args  # referral code

    user = users.find_one({"user_id": user_id})

    # NEW USER
    if not user:
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "referrals": 0
        })

        # 🔥 REFERRAL LOGIC
        if args:
            referrer_id = int(args[0])

            if referrer_id != user_id:
                ref_user = users.find_one({"user_id": referrer_id})

                if ref_user:
                    users.update_one(
                        {"user_id": referrer_id},
                        {
                            "$inc": {
                                "balance": 10,      # 💰 reward
                                "referrals": 1
                            }
                        }
                    )

        await update.message.reply_text("✅ You are registered!")

    # EXISTING USER
    else:
        balance = user.get("balance", 0)
        refs = user.get("referrals", 0)

        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"

        await update.message.reply_text(
            f"👋 Welcome back {username}!\n\n"
            f"💰 Balance: {balance}\n"
            f"👥 Referrals: {refs}\n\n"
            f"🔗 Your referral link:\n{referral_link}"
        )

# Add handler
telegram_app.add_handler(CommandHandler("start", start))

# 🔥 WEBHOOK (FIXED)
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)

    asyncio.run(telegram_app.process_update(update))

    return "ok"

# Home route
@app.route("/")
def home():
    return "Bot is running!"

# START
if __name__ == "__main__":

    async def setup():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

    asyncio.run(setup())

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
