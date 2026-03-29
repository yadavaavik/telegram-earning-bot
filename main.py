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
withdraws = db["withdraws"]

# ========= APP =========
app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

# ========= MENU =========
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"

    args = context.args
    user = users.find_one({"user_id": user_id})

    if not user:
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "referrals": 0
        })

        # REFERRAL
        if args:
            try:
                ref_id = int(args[0])
                if ref_id != user_id:
                    ref_user = users.find_one({"user_id": ref_id})
                    if ref_user:
                        users.update_one(
                            {"user_id": ref_id},
                            {"$inc": {"balance": 10, "referrals": 1}}
                        )
            except:
                pass

        await update.message.reply_text(
            f"🎉 Welcome {username}!\n\nEarn money using this bot 👇",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            f"👋 Welcome back {username}!",
            reply_markup=main_menu()
        )

# ========= BUTTON HANDLER =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = users.find_one({"user_id": user_id})

    if query.data == "balance":
        await query.edit_message_text(
            f"💰 Balance: {user.get('balance',0)}\n👥 Referrals: {user.get('referrals',0)}",
            reply_markup=main_menu()
        )

    elif query.data == "refer":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(
            f"👥 Invite & Earn ₹10\n\n🔗 Your link:\n{link}",
            reply_markup=main_menu()
        )

    elif query.data == "withdraw":
        balance = user.get("balance", 0)

        if balance < 50:
            await query.edit_message_text(
                "❌ Minimum withdraw is ₹50",
                reply_markup=main_menu()
            )
        else:
            withdraws.insert_one({
                "user_id": user_id,
                "amount": balance,
                "status": "pending"
            })

            users.update_one(
                {"user_id": user_id},
                {"$set": {"balance": 0}}
            )

            await query.edit_message_text(
                "✅ Withdraw request sent!",
                reply_markup=main_menu()
            )

# ========= HANDLERS =========
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(button))

# ========= WEBHOOK =========
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.get_event_loop().create_task(
        telegram_app.process_update(update)
    )
    return "ok"

@app.route("/")
def home():
    return "Bot is running!"

# ========= MAIN =========
if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(
        telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    )

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
