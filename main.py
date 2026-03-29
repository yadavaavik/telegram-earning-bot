import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient

# ========= LOGGING =========
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]

# ========= MENU =========
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user

        # SAFETY CHECK
        if update.message is None:
            return

        users.update_one(
            {"user_id": user.id},
            {"$setOnInsert": {
                "user_id": user.id,
                "name": user.first_name,
                "balance": 0,
                "referrals": 0
            }},
            upsert=True
        )

        await update.message.reply_text(
            f"🎉 Welcome {user.first_name}!\nEarn ₹10 per referral 💸",
            reply_markup=menu()
        )

    except Exception as e:
        print("START ERROR:", e)

# ========= BUTTON =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        if not query:
            return

        await query.answer()

        user = users.find_one({"user_id": query.from_user.id})

        if not user:
            return

        if query.data == "balance":
            msg = f"💰 Balance: ₹{user['balance']}\n👥 Referrals: {user['referrals']}"

        elif query.data == "refer":
            bot_username = (await context.bot.get_me()).username
            msg = f"https://t.me/{bot_username}?start={query.from_user.id}"

        else:
            msg = "Withdraw coming soon"

        await query.edit_message_text(msg, reply_markup=menu())

    except Exception as e:
        print("BUTTON ERROR:", e)
        
# ========= MAIN =========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("✅ Bot running (polling)...")
    app.run_polling()

if __name__ == "__main__":
    main()

from telegram.ext import Application

async def error_handler(update, context):
    print(f"ERROR: {context.error}")

app.add_error_handler(error_handler)
