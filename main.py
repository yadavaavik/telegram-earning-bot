import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient

# ========= LOGGING =========
logging.basicConfig(level=logging.INFO)

# ========= ENV =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not MONGO_URI or not WEBHOOK_URL:
    raise Exception("Missing ENV variables!")

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# ========= FLASK =========
app = Flask(__name__)

# ========= EVENT LOOP =========
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ========= TELEGRAM =========
telegram_app = Application.builder().token(BOT_TOKEN).build()

# ========= MENU =========
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.first_name

    referrer_id = None

    # ✅ Get referral ID
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except:
            referrer_id = None

    existing_user = users.find_one({"user_id": user_id})

    # ========= NEW USER =========
    if not existing_user:
        users.insert_one({
            "user_id": user_id,
            "name": name,
            "balance": 0,
            "referrals": 0,
            "referred_by": referrer_id
        })

        # ✅ Referral reward
        if referrer_id and referrer_id != user_id:
            ref_user = users.find_one({"user_id": referrer_id})

            if ref_user:
                users.update_one(
                    {"user_id": referrer_id},
                    {
                        "$inc": {
                            "balance": 10,
                            "referrals": 1
                        }
                    }
                )

        await update.message.reply_text(
            f"🎉 *Welcome {name}!*\n\n"
            f"💸 Earn *₹10 per referral*\n"
            f"🚀 Invite friends & grow your balance!\n\n"
            f"👇 Choose an option below",
            reply_markup=menu(),
            parse_mode="Markdown"
        )

    # ========= EXISTING USER =========
    else:
        await update.message.reply_text(
            f"👋 *Welcome back {name}!*\n\n"
            f"💰 Keep earning with referrals!",
            reply_markup=menu(),
            parse_mode="Markdown"
        )

# ========= BUTTON =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = users.find_one({"user_id": user_id})

    if not user:
        return

    # ========= BALANCE =========
    if query.data == "balance":
        await query.edit_message_text(
            f"💰 *Your Balance:* ₹{user['balance']}\n"
            f"👥 *Total Referrals:* {user['referrals']}",
            reply_markup=menu(),
            parse_mode="Markdown"
        )

    # ========= REFER =========
    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={user_id}"

        await query.edit_message_text(
            f"👥 *Refer & Earn*\n\n"
            f"💸 Earn ₹10 per friend\n\n"
            f"🔗 Your link:\n{link}",
            reply_markup=menu(),
            parse_mode="Markdown"
        )

    # ========= WITHDRAW =========
    elif query.data == "withdraw":
        if user["balance"] < 100:
            msg = "❌ Minimum withdraw is ₹100"
        else:
            msg = "💸 Withdraw request received (manual process)"

        await query.edit_message_text(
            msg,
            reply_markup=menu()
        )

# ========= HANDLERS =========
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(button))

# ========= WEBHOOK =========
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, telegram_app.bot)

        asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            loop
        )

    except Exception as e:
        logging.error(f"Webhook error: {e}")

    return "ok"

@app.route("/")
def home():
    return "✅ Bot is running!"

# ========= MAIN =========
if __name__ == "__main__":
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())

    loop.run_until_complete(
        telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    )

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
