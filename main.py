import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from pymongo import MongoClient
from bson import ObjectId

# ========= CONFIG =========
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

print("TOKEN:", BOT_TOKEN)
print("MONGO:", MONGO_URI)

ADMIN_IDS = [8250329715]  

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]
withdraws = db["withdraws"]

# ========= SETTINGS =========
REFERRAL_REWARD = 0.10
MIN_WITHDRAW = 1.0

# ========= MENUS =========
def main_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]

    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin_panel")])

    return InlineKeyboardMarkup(keyboard)


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Withdraws", callback_data="admin_withdraws")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        uid = user.id

        ref_id = None
        if context.args:
            try:
                ref_id = int(context.args[0])
            except:
                pass

        existing = users.find_one({"user_id": uid})

        if not existing:
            users.insert_one({
                "user_id": uid,
                "name": user.first_name,
                "balance": 0.0,
                "referrals": 0,
                "referred_by": None
            })

            # referral
            if ref_id and ref_id != uid:
                ref_user = users.find_one({"user_id": ref_id})
                if ref_user:
                    users.update_one(
    {"user_id": ref_id},
    {"$inc": {"balance": 0.10, "referrals": 1}}
)
                    users.update_one(
                        {"user_id": uid},
                        {"$set": {"referred_by": ref_id}}
                    )

        await update.message.reply_text(
            f"🎉 Welcome {user.first_name}!\nEarn $0.10 per referral 💸",
            reply_markup=main_menu(uid)
        )

    except Exception as e:
        print("START ERROR:", e)

# ========= BUTTON =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        user = users.find_one({"user_id": user_id})

        if not user:
            return

        # ===== BACK =====
        if query.data == "back":
            await query.edit_message_text(
                "🏠 Main Menu",
                reply_markup=main_menu(user_id)
            )

        # ===== BALANCE =====
        elif query.data == "balance":
            msg = f"💰 ${round(user['balance'], 2)}\n👥 {user['referrals']} referrals"
            await query.edit_message_text(msg, reply_markup=back_menu())

        # ===== REFER =====
        elif query.data == "refer":
            bot = await context.bot.get_me()
            link = f"https://t.me/{bot.username}?start={user_id}"
            await query.edit_message_text(link, reply_markup=back_menu())

        # ===== WITHDRAW =====
        elif query.data == "withdraw":
            if user["balance"] < MIN_WITHDRAW:
                await query.edit_message_text(
                    f"❌ Minimum ${MIN_WITHDRAW}",
                    reply_markup=back_menu()
                )
            else:
                context.user_data["awaiting_wallet"] = True
                await query.message.reply_text("Send crypto wallet address")

        # ===== ADMIN PANEL =====
        elif query.data == "admin_panel":
            if user_id not in ADMIN_IDS:
                await query.answer("Not allowed ❌", show_alert=True)
                return

            await query.edit_message_text(
                "👑 Admin Panel",
                reply_markup=admin_menu()
            )

        # ===== BROADCAST =====
        elif query.data == "broadcast":
            if user_id not in ADMIN_IDS:
                return

            context.user_data["broadcast"] = True
            await query.message.reply_text("Send message to broadcast")

    except Exception as e:
        print("BUTTON ERROR:", e)

# ========= MESSAGE =========
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        text = update.message.text

        # ===== BROADCAST =====
        if context.user_data.get("broadcast"):
            sent = 0

            for u in users.find():
                try:
                    await context.bot.send_message(u["user_id"], text)
                    sent += 1
                except:
                    pass

            context.user_data["broadcast"] = False
            await update.message.reply_text(f"✅ Sent to {sent} users")
            return

        # ===== WITHDRAW =====
        if context.user_data.get("awaiting_wallet"):
            user = users.find_one({"user_id": user_id})

            withdraws.insert_one({
                "user_id": user_id,
                "wallet": text,
                "amount": user["balance"],
                "status": "pending"
            })

            users.update_one(
                {"user_id": user_id},
                {"$set": {"balance": 0}}
            )

            context.user_data["awaiting_wallet"] = False

            await update.message.reply_text(
                "✅ Withdraw processed instantly 💸",
                reply_markup=main_menu(user_id)
            )

    except Exception as e:
        print("MSG ERROR:", e)

# ========= MAIN =========
def main():
    try:
        if not BOT_TOKEN:
            print("❌ BOT_TOKEN missing")
            return

        if not MONGO_URI:
            print("❌ MONGO_URI missing")
            return

        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

        print("🚀 Bot Running...")
        app.run_polling()

    except Exception as e:
        print("FATAL ERROR:", e)

if __name__ == "__main__":
    main()
