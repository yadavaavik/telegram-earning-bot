import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient

# ========= ENV =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# ========= APP =========
app = Flask(__name__)

# ✅ IMPORTANT: create global loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

telegram_app = Application.builder().token(BOT_TOKEN).build()

# ========= MENU =========
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name

    user = users.find_one({"user_id": user_id})

    if not user:
        users.insert_one({
            "user_id": user_id,
            "name": name,
            "balance": 0,
            "referrals": 0
        })

        await update.message.reply_text(
            f"🎉 Welcome {name}!\n\nEarn ₹10 per referral 💸",
            reply_markup=menu()
        )
    else:
        await update.message.reply_text(
            f"👋 Welcome back {name}!\n\nChoose option 👇",
            reply_markup=menu()
        )

# ========= BUTTON =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = users.find_one({"user_id": query.from_user.id})

    if query.data == "balance":
        await query.edit_message_text(
            f"💰 Balance: ₹{user['balance']}\n👥 Referrals: {user['referrals']}",
            reply_markup=menu()
        )

    elif query.data == "refer":
        link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"
        await query.edit_message_text(
            f"👥 Invite friends\nEarn ₹10 each\n\n🔗 {link}",
            reply_markup=menu()
        )

    elif query.data == "withdraw":
        await query.edit_message_text(
            "💸 Withdraw feature coming soon",
            reply_markup=menu()
        )

# ========= HANDLERS =========
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(button))

# ========= WEBHOOK =========
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    # ✅ CORRECT processing
    loop.create_task(telegram_app.process_update(update))

    return "ok"

@app.route("/")
def home():
    return "Bot is running!"

# ========= MAIN =========
if __name__ == "__main__":
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_until_complete(
        telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    )

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
