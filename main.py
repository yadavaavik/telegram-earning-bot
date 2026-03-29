import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from pymongo import MongoClient

# ========= LOGGING =========
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]
withdraws = db["withdraws"]

# ========= MENU =========
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message is None:
            return

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
                "referred_by": None
            })

            # Referral logic
            if referrer_id and referrer_id != user_id:
                ref_user = users.find_one({"user_id": referrer_id})
                if ref_user:
                    users.update_one(
                        {"user_id": referrer_id},
                        {"$inc": {"balance": 10, "referrals": 1}}
                    )
                    users.update_one(
                        {"user_id": user_id},
                        {"$set": {"referred_by": referrer_id}}
                    )

            msg = f"🎉 Welcome {name}!\n\n💸 Earn ₹10 per referral"

        else:
            msg = f"👋 Welcome back {name}!"

        await update.message.reply_text(msg, reply_markup=main_menu())

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

        # ========= BALANCE =========
        if query.data == "balance":
            msg = f"💰 Balance: ₹{user['balance']}\n👥 Referrals: {user['referrals']}"
            await query.edit_message_text(msg, reply_markup=back_menu())

        # ========= REFER =========
        elif query.data == "refer":
            bot_username = (await context.bot.get_me()).username
            link = f"https://t.me/{bot_username}?start={user['user_id']}"

            msg = f"👥 Invite & Earn ₹10\n\n🔗 {link}"
            await query.edit_message_text(msg, reply_markup=back_menu())

        # ========= WITHDRAW =========
        elif query.data == "withdraw":
            if user["balance"] < 100:
                msg = "❌ Minimum withdraw ₹100"
                await query.edit_message_text(msg, reply_markup=back_menu())
            else:
                context.user_data["awaiting_wallet"] = True
                await query.message.reply_text(
                    "💸 Send your crypto wallet address\n\n(BTC / USDT / etc.)"
                )

        # ========= BACK =========
        elif query.data == "back":
            await query.edit_message_text(
                "🏠 Main Menu",
                reply_markup=main_menu()
            )

    except Exception as e:
        print("BUTTON ERROR:", e)

# ========= WITHDRAW INPUT =========
async def withdraw_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message is None:
            return

        if not context.user_data.get("awaiting_wallet"):
            return

        user_id = update.effective_user.id
        wallet = update.message.text

        user = users.find_one({"user_id": user_id})

        if user["balance"] < 100:
            await update.message.reply_text("❌ Minimum withdraw ₹100")
            context.user_data["awaiting_wallet"] = False
            return

        # Save withdraw
        withdraws.insert_one({
            "user_id": user_id,
            "wallet": wallet,
            "amount": user["balance"],
            "status": "pending"
        })

        # Reset balance
        users.update_one(
            {"user_id": user_id},
            {"$set": {"balance": 0}}
        )

        context.user_data["awaiting_wallet"] = False

        await update.message.reply_text(
            "✅ Withdraw request submitted\n\n💸 You will receive crypto soon",
            reply_markup=main_menu()
        )

    except Exception as e:
        print("WITHDRAW ERROR:", e)

# ========= ERROR HANDLER =========
async def error_handler(update, context):
    print("ERROR:", context.error)

# ========= MAIN =========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_input))

    app.add_error_handler(error_handler)

    print("✅ Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
