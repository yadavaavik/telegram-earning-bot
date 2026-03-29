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
ADMIN_ID = 123456789  # 🔥 CHANGE THIS

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]
withdraws = db["withdraws"]

# ========= MENUS =========
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

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Withdraws", callback_data="admin_withdraws")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return

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
                "balance": 0,
                "referrals": 0,
                "referred_by": None
            })

            # referral logic
            if ref_id and ref_id != uid:
                ref_user = users.find_one({"user_id": ref_id})
                if ref_user:
                    users.update_one(
                        {"user_id": ref_id},
                        {"$inc": {"balance": 10, "referrals": 1}}
                    )
                    users.update_one(
                        {"user_id": uid},
                        {"$set": {"referred_by": ref_id}}
                    )

        await update.message.reply_text(
            f"🎉 Welcome {user.first_name}!",
            reply_markup=main_menu()
        )

    except Exception as e:
        print("START ERROR:", e)

# ========= BUTTON =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        user = users.find_one({"user_id": query.from_user.id})

        if not user:
            return

        # ===== BACK =====
        if query.data == "back":
            await query.edit_message_text("🏠 Main Menu", reply_markup=main_menu())

        # ===== BALANCE =====
        elif query.data == "balance":
            msg = f"💰 ₹{user['balance']}\n👥 {user['referrals']} referrals"
            await query.edit_message_text(msg, reply_markup=back_menu())

        # ===== REFER =====
        elif query.data == "refer":
            bot = await context.bot.get_me()
            link = f"https://t.me/{bot.username}?start={user['user_id']}"
            await query.edit_message_text(link, reply_markup=back_menu())

        # ===== WITHDRAW =====
        elif query.data == "withdraw":
            if user["balance"] < 100:
                await query.edit_message_text(
                    "❌ Minimum ₹100",
                    reply_markup=back_menu()
                )
            else:
                context.user_data["awaiting_wallet"] = True
                await query.message.reply_text("Send crypto wallet address")

        # ===== ADMIN WITHDRAWS =====
        elif query.data == "admin_withdraws":
            if query.from_user.id != ADMIN_ID:
                return

            data = withdraws.find({"status": "pending"})

            text = "📤 Withdraws:\n\n"
            buttons = []

            for w in data:
                wid = str(w["_id"])
                text += f"{w['user_id']} | ₹{w['amount']}\n"

                buttons.append([
                    InlineKeyboardButton("✅", callback_data=f"ok_{wid}"),
                    InlineKeyboardButton("❌", callback_data=f"no_{wid}")
                ])

            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back")])

            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

        # ===== APPROVE =====
        elif query.data.startswith("ok_"):
            wid = query.data.split("_")[1]

            withdraws.update_one(
                {"_id": ObjectId(wid)},
                {"$set": {"status": "approved"}}
            )

            await query.answer("Approved")

        # ===== REJECT =====
        elif query.data.startswith("no_"):
            wid = query.data.split("_")[1]

            w = withdraws.find_one({"_id": ObjectId(wid)})

            users.update_one(
                {"user_id": w["user_id"]},
                {"$inc": {"balance": w["amount"]}}
            )

            withdraws.update_one(
                {"_id": ObjectId(wid)},
                {"$set": {"status": "rejected"}}
            )

            await query.answer("Rejected")

        # ===== BROADCAST =====
        elif query.data == "broadcast":
            if query.from_user.id != ADMIN_ID:
                return

            context.user_data["broadcast"] = True
            await query.message.reply_text("Send message")

    except Exception as e:
        print("BUTTON ERROR:", e)

# ========= MESSAGE HANDLER =========
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return

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
            await update.message.reply_text(f"✅ Sent to {sent}")
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

            await update.message.reply_text("✅ Withdraw submitted", reply_markup=main_menu())

    except Exception as e:
        print("MSG ERROR:", e)

# ========= ADMIN =========
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("👑 Admin", reply_markup=admin_menu())

# ========= MAIN =========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🚀 Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
