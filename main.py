import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from pymongo import MongoClient

# ========= CONFIG =========
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

ADMIN_IDS = [8250329715]

REFERRAL_REWARD = 0.10
MIN_WITHDRAW = 1.0

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users = db["users"]
withdraws = db["withdraws"]

# ========= MENUS =========
def main_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]

    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])

    return InlineKeyboardMarkup(keyboard)


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "user_earned": 0.0,
            "user_withdrawn": 0.0,
            "referred_by": None
        })

        if ref_id and ref_id != uid:
            ref_user = users.find_one({"user_id": ref_id})
            if ref_user:
                users.update_one(
                    {"user_id": ref_id},
                    {"$inc": {
                        "balance": REFERRAL_REWARD,
                        "referrals": 1,
                        "user_earned": REFERRAL_REWARD
                    }}
                )
                users.update_one(
                    {"user_id": uid},
                    {"$set": {"referred_by": ref_id}}
                )

    await update.message.reply_text(
        f"🎉 Welcome {user.first_name}!\nEarn ${REFERRAL_REWARD} per referral 💸",
        reply_markup=main_menu(uid)
    )

# ========= BUTTON HANDLER =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = users.find_one({"user_id": user_id})

    if not user:
        return

    data = query.data

    # ===== BACK =====
    if data == "back":
        await query.edit_message_text("🏠 Main Menu", reply_markup=main_menu(user_id))

    # ===== BALANCE =====
    elif data == "balance":
        msg = (
            f"💰 Balance: ${round(user['balance'], 2)}\n"
            f"👥 Referrals: {user['referrals']}\n"
            f"📈 Earned: ${round(user['user_earned'], 2)}\n"
            f"💸 Withdrawn: ${round(user['user_withdrawn'], 2)}"
        )
        await query.edit_message_text(msg, reply_markup=back_menu())

    # ===== REFER =====
    elif data == "refer":
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={user_id}"

        await query.edit_message_text(
            f"🔗 Your Referral Link:\n{link}",
            reply_markup=back_menu()
        )

    # ===== WITHDRAW =====
    elif data == "withdraw":
        if user["balance"] < MIN_WITHDRAW:
            await query.edit_message_text(
                f"❌ Minimum withdraw is ${MIN_WITHDRAW}",
                reply_markup=back_menu()
            )
        else:
            context.user_data["awaiting_wallet"] = True
            await query.message.reply_text("💳 Send your wallet address")

    # ===== ADMIN PANEL =====
    elif data == "admin":
        if user_id not in ADMIN_IDS:
            return
        await query.edit_message_text("👑 Admin Panel", reply_markup=admin_menu())

    # ===== STATS =====
    elif data == "stats":
        if user_id not in ADMIN_IDS:
            return

        total_users = users.count_documents({})
        total_earned = sum(u.get("user_earned", 0) for u in users.find())
        total_withdrawn = sum(u.get("user_withdrawn", 0) for u in users.find())

        profit = total_earned - total_withdrawn

        text = (
            f"📊 Stats\n\n"
            f"👥 Users: {total_users}\n"
            f"📈 Earned: ${round(total_earned,2)}\n"
            f"💸 Withdrawn: ${round(total_withdrawn,2)}\n"
            f"💰 Profit: ${round(profit,2)}"
        )

        await query.edit_message_text(text, reply_markup=back_menu())

    # ===== BROADCAST =====
    elif data == "broadcast":
        if user_id not in ADMIN_IDS:
            return

        context.user_data["broadcast"] = True
        await query.message.reply_text("Send message to broadcast")

    # ===== APPROVE =====
    elif data.startswith("approve_"):
        if user_id not in ADMIN_IDS:
            return

        target_id = int(data.split("_")[1])
        req = withdraws.find_one({"user_id": target_id, "status": "pending"})

        if not req:
            await query.answer("Already processed")
            return

        amount = req["amount"]

        withdraws.update_one({"_id": req["_id"]}, {"$set": {"status": "approved"}})
        users.update_one({"user_id": target_id}, {"$inc": {"user_withdrawn": amount}})

        await context.bot.send_message(target_id, f"✅ Withdraw Approved\n💰 ${amount}")
        await query.edit_message_text("✅ Approved")

    # ===== REJECT =====
    elif data.startswith("reject_"):
        if user_id not in ADMIN_IDS:
            return

        target_id = int(data.split("_")[1])
        req = withdraws.find_one({"user_id": target_id, "status": "pending"})

        if not req:
            await query.answer("Already processed")
            return

        amount = req["amount"]

        withdraws.update_one({"_id": req["_id"]}, {"$set": {"status": "rejected"}})
        users.update_one({"user_id": target_id}, {"$inc": {"balance": amount}})

        await context.bot.send_message(target_id, "❌ Withdraw Rejected (Refunded)")
        await query.edit_message_text("❌ Rejected")

# ========= MESSAGE HANDLER =========
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # ===== WITHDRAW FLOW =====
    if context.user_data.get("awaiting_wallet"):
        user = users.find_one({"user_id": user_id})
        amount = user["balance"]

        if amount < MIN_WITHDRAW:
            await update.message.reply_text("❌ Not enough balance")
            return

        withdraws.insert_one({
            "user_id": user_id,
            "wallet": text,
            "amount": amount,
            "status": "pending"
        })

        users.update_one({"user_id": user_id}, {"$set": {"balance": 0}})
        context.user_data["awaiting_wallet"] = False

        # notify admin
        for admin in ADMIN_IDS:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                ]
            ])

            await context.bot.send_message(
                admin,
                f"💸 Withdraw Request\n\nUser: {user_id}\nAmount: ${amount}\nWallet: {text}",
                reply_markup=keyboard
            )

        await update.message.reply_text("⏳ Request sent", reply_markup=main_menu(user_id))

# ========= MAIN =========
def main():
    if not BOT_TOKEN or not MONGO_URI:
        print("❌ Missing ENV")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🚀 Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
