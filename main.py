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
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
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
            f"🎉 Welcome {user.first_name}!\nEarn $0.10 per referral 💸",
            reply_markup=main_menu(uid)
        )

    except Exception as e:
        print(e)

# ========= BUTTON =========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        user = users.find_one({"user_id": user_id})

        if not user:
            return

        if query.data == "back":
            await query.edit_message_text(
                "🏠 Main Menu",
                reply_markup=main_menu(user_id)
            )

        elif query.data == "balance":
            msg = (
                f"💰 Balance: ${round(user['balance'], 2)}\n"
                f"👥 Referrals: {user['referrals']}\n"
                f"📈 Earned: ${round(user.get('user_earned', 0), 2)}\n"
                f"💸 Withdrawn: ${round(user.get('user_withdrawn', 0), 2)}"
            )
            await query.edit_message_text(msg, reply_markup=back_menu())

        elif query.data == "refer":
            bot = await context.bot.get_me()
            link = f"https://t.me/{bot.username}?start={user_id}"

            await query.edit_message_text(
                f"🔗 Your Referral Link:\n{link}",
                reply_markup=back_menu()
            )

        elif query.data == "withdraw":
            if user["balance"] < MIN_WITHDRAW:
                await query.edit_message_text(
                    f"❌ Minimum ${MIN_WITHDRAW}",
                    reply_markup=back_menu()
                )
            else:
                context.user_data["awaiting_wallet"] = True
               await query.message.reply_text("💳 Send your wallet address")

        elif query.data == "admin_panel":
            if user_id not in ADMIN_IDS:
                await query.answer("Not allowed ❌", show_alert=True)
                return

            await query.edit_message_text(
                "👑 Admin Panel",
                reply_markup=admin_menu()
            )

        elif query.data == "admin_stats":
            if user_id not in ADMIN_IDS:
                return

            total_users = users.count_documents({})
            total_withdraw = sum(u.get("user_withdrawn", 0) for u in users.find())
            total_earned = sum(u.get("user_earned", 0) for u in users.find())

            profit = total_earned - total_withdraw

            text = (
                "📊 Bot Stats\n\n"
                f"👥 Users: {total_users}\n"
                f"📈 Earned: ${round(total_earned, 2)}\n"
                f"💸 Withdrawn: ${round(total_withdraw, 2)}\n"
                f"💰 Profit: ${round(profit, 2)}"
            )

            await query.edit_message_text(text, reply_markup=back_menu())

        elif query.data == "broadcast":
            if user_id not in ADMIN_IDS:
                return

            context.user_data["broadcast"] = True
            await query.message.reply_text("Send message to broadcast")

        elif query.data.startswith("approve_"):
            if user_id not in ADMIN_IDS:
                return

        elif query.data.startswith("reject_"):
            if user_id not in ADMIN_IDS:
                return

    
        # ===== APPROVE WITHDRAW =====


    target_id = int(query.data.split("_")[1])

    req = withdraws.find_one({
        "user_id": target_id,
        "status": "pending"
    })

    if not req:
        await query.answer("Already processed")
        return

    amount = req["amount"]

    withdraws.update_one(
        {"_id": req["_id"]},
        {"$set": {"status": "approved"}}
    )

    users.update_one(
        {"user_id": target_id},
        {"$inc": {"user_withdrawn": amount}}
    )

    await context.bot.send_message(
        target_id,
        f"✅ Withdraw Approved!\n\n💰 Amount: ${amount}"
    )

    await query.edit_message_text("✅ Approved")


# ===== REJECT WITHDRAW =====

    target_id = int(query.data.split("_")[1])

    req = withdraws.find_one({
        "user_id": target_id,
        "status": "pending"
    })

    if not req:
        await query.answer("Already processed")
        return

    amount = req["amount"]

    withdraws.update_one(
        {"_id": req["_id"]},
        {"$set": {"status": "rejected"}}
    )

    # refund balance
    users.update_one(
        {"user_id": target_id},
        {"$inc": {"balance": amount}}
    )

    await context.bot.send_message(
        target_id,
        "❌ Withdraw Rejected (amount refunded)"
    )

    await query.edit_message_text("❌ Rejected")

    except Exception as e:
        print("BUTTON ERROR:", e)

# ========= MESSAGE =========
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

        # ===== WITHDRAW REQUEST =====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        text = update.message.text

        if context.user_data.get("awaiting_wallet"):
               user = users.find_one({"user_id": user_id})
               amount = user["balance"]

               if amount < MIN_WITHDRAW:
                   await update.message.reply_text("❌ Not enough balance")
                   return

    # Create withdraw request
    withdraws.insert_one({
        "user_id": user_id,
        "wallet": text,
        "amount": amount,
        "status": "pending"
    })

    # lock balance (optional advanced logic)
    users.update_one(
        {"user_id": user_id},
        {"$set": {"balance": 0}}
    )

    context.user_data["awaiting_wallet"] = False

    # Notify admin
    for admin in ADMIN_IDS:
        try:
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
        except:
            pass

    await update.message.reply_text(
        "⏳ Withdraw request sent for approval",
        reply_markup=main_menu(user_id)
    )
    return
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
