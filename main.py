import os
import logging
import asyncio
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

# ========= TELEGRAM =========
telegram_app = Application.builder().token(BOT_TOKEN).build()

# ========= GLOBAL LOOP =========
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

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
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except:
            pass

    existing = users.find_one({"user_id": user_id})

    if not existing:
        users.insert_one({
            "user_id": user_id,
            "name": name,
            "balance": 0,
            "referrals": 0,
            "referred_by": referrer_id
        })

        # Referral reward
        if referrer_id and referrer_id != user_id:
            ref_user = users.find_one({"user_id": referrer_id})
            if ref_user:
                users.update_one(
                    {"user_id": referrer_id},
                    {"$inc": {"balance": 10, "referrals": 1}}
                )

        msg = f"🎉 Welcome {name}!\n\n💸 Earn ₹10 per referral"

    else:
        msg = f"👋 Welcome back {name}!"

    await update.message.reply_text(msg, reply_markup=menu())

# ========= BUTTON =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = users.find_one({"user_id": query.from_user.id})
    if not user:
        return

    if query.data == "balance":
        msg = f"💰 Balance: ₹{user['balance']}\n👥 Referrals: {user['referrals']}"

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={user['user_id']}"
        msg = f"👥 Invite & Earn ₹10\n\n🔗 {link}"

    elif query.data == "withdraw":
        if user["balance"] < 100:
            msg = "❌ Minimum withdraw ₹100"
        else:
            msg = "💸 Withdraw request received"

    await query.edit_message_text(msg, reply_markup=menu())

# ========= HANDLERS =========
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(button))

# ========= INIT FUNCTION =========
async def init_bot():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Bot initialized & webhook set")

# ========= WEBHOOK =========
@app.route("/", methods=["POST"])
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

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is running"

# ========= STARTUP =========
def start_background_loop():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_bot())
    loop.run_forever()

# ========= MAIN =========
if __name__ == "__main__":
    import threading

    # Start async loop in background thread
    t = threading.Thread(target=start_background_loop)
    t.start()

    # Start Flask (this opens port for Render)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
