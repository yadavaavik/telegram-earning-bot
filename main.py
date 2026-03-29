import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ================== DB ==================
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# ================== FLASK ==================
app = Flask(__name__)

# ================== TELEGRAM ==================
telegram_app = Application.builder().token(BOT_TOKEN).build()

# ================== START COMMAND ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"

    args = context.args  # referral code
    user = users.find_one({"user_id": user_id})

    # 🆕 NEW USER
    if not user:
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "referrals": 0
        })

        # 🔥 REFERRAL SYSTEM
        if args:
            try:
                referrer_id = int(args[0])

                if referrer_id != user_id:
                    ref_user = users.find_one({"user_id": referrer_id})

                    if ref_user:
                        users.update_one(
                            {"user_id": referrer_id},
                            {
                                "$inc": {
                                    "balance": 10,   # reward
                                    "referrals": 1
                                }
                            }
                        )
            except:
                pass

        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"

        await update.message.reply_text(
            f"🎉 Welcome {username}!\n\n"
            f"💰 Earn ₹10 per referral\n\n"
            f"🔗 Your link:\n{referral_link}"
        )

    # 👤 EXISTING USER
    else:
        balance = user.get("balance", 0)
        refs = user.get("referrals", 0)

        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"

        await update.message.reply_text(
            f"👋 Welcome back {username}!\n\n"
            f"💰 Balance: {balance}\n"
            f"👥 Referrals: {refs}\n\n"
            f"🔗 Your link:\n{referral_link}"
        )

# ================== HANDLER ==================
telegram_app.add_handler(CommandHandler("start", start))

# ================== WEBHOOK ==================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, telegram_app.bot)

        asyncio.run(telegram_app.process_update(update))

        return "ok"
    except Exception as e:
        print("Error:", e)
        return "error"

# ================== HOME ==================
@app.route("/")
def home():
    return "Bot is running!"

# ================== START ==================
if __name__ == "__main__":

    async def setup():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

    asyncio.run(setup())

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
