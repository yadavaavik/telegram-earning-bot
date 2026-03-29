import os
import logging
from datetime import datetime
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

ADMIN_IDS = [8250329715]

REFERRAL_REWARD = 0.10
MIN_WITHDRAW = 1.0

# ========= DB =========
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

users = db["users"]
withdraws = db["withdraws"]
tasks = db["tasks"]   # 🔥 PRO FEATURE

# ========= USER STRUCTURE =========
def create_user(uid, name):
    return {
        "user_id": uid,
        "name": name,
        "balance": 0.0,
        "referrals": 0,
        "user_earned": 0.0,
        "user_withdrawn": 0.0,
        "referred_by": None,
        "join_date": str(datetime.now().date()),
        "is_banned": False
    }

# ========= MENUS =========
def main_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("🧩 Tasks", callback_data="tasks")],  # 🔥 NEW
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
        [InlineKeyboardButton("🏆 Top Users", callback_data="top_users")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
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
        users.insert_one(create_user(uid, user.first_name))

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
        f"🎉 Welcome {user.first_name}!\nEarn money easily 💸",
        reply_markup=main_menu(uid)
    )

# ========= BUTTON HANDLER =========

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # =========================
    # 🛡️ SAFE USER LOAD
    # =========================
    user = users.find_one({"user_id": user_id})

    if not user:
        users.insert_one(create_user(user_id, query.from_user.first_name))
        user = users.find_one({"user_id": user_id})

    if user.get("is_banned", False):
        await query.edit_message_text("🚫 You are banned from using this bot")
        return

    # =========================
    # 🔙 BACK
    # =========================
    if data == "back":
        return await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=main_menu(user_id)
        )

    # =========================
    # 💰 BALANCE
    # =========================
    if data == "balance":
        return await query.edit_message_text(
            f"💰 Balance: ${round(user.get('balance',0),2)}\n"
            f"👥 Referrals: {user.get('referrals',0)}\n"
            f"📈 Earned: ${round(user.get('user_earned',0),2)}\n"
            f"💸 Withdrawn: ${round(user.get('user_withdrawn',0),2)}",
            reply_markup=back_menu()
        )

    # =========================
    # 👥 REFER
    # =========================
    if data == "refer":
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={user_id}"

        return await query.edit_message_text(
            f"🔗 Your Referral Link:\n\n{link}\n\n"
            f"💰 Earn ${REFERRAL_REWARD} per referral",
            reply_markup=back_menu()
        )

    # =========================
    # 🧩 TASK LIST
    # =========================
    if data == "tasks":
        all_tasks = list(tasks.find({}, {"title": 1, "reward": 1}))

        if not all_tasks:
            return await query.edit_message_text(
                "❌ No tasks available",
                reply_markup=back_menu()
            )

        keyboard = [
            [InlineKeyboardButton(f"{t['title']} (${t['reward']})", callback_data=f"do_task_{t['_id']}")]
            for t in all_tasks
        ]

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])

        return await query.edit_message_text(
            "🧩 Complete tasks & earn 💰",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # 🧩 OPEN TASK
    # =========================
    if data.startswith("do_task_"):
        task_id = data.split("_")[2]

        try:
            task = tasks.find_one({"_id": ObjectId(task_id)})
        except:
            return await query.answer("Invalid task")

        if not task:
            return await query.answer("Task not found")

        return await query.edit_message_text(
            f"🧩 {task['title']}\n\n"
            f"🔗 {task['link']}\n\n"
            f"💰 Reward: ${task['reward']}\n\n"
            f"📌 Send: /done_{task_id}",
            reply_markup=back_menu()
        )

    # =========================
    # 💸 WITHDRAW
    # =========================
    if data == "withdraw":
        balance = user.get("balance", 0)

        if balance < MIN_WITHDRAW:
            return await query.edit_message_text(
                f"❌ Min withdraw: ${MIN_WITHDRAW}\nYour Balance: ${balance}",
                reply_markup=back_menu()
            )

        context.user_data["awaiting_wallet"] = True

        return await query.message.reply_text(
            f"💳 Send wallet / UPI\n💰 Amount: ${balance}"
        )

    # =========================
    # 👑 ADMIN PANEL
    # =========================
    if data == "admin":
        if user_id not in ADMIN_IDS:
            return

        return await query.edit_message_text(
            "👑 Admin Panel",
            reply_markup=admin_menu()
        )

    # =========================
    # 📊 STATS
    # =========================
    if data == "stats":
        if user_id not in ADMIN_IDS:
            return

        total_users = users.count_documents({})

        total_earned = sum(u.get("user_earned", 0) for u in users.find({}, {"user_earned":1}))
        total_withdrawn = sum(u.get("user_withdrawn", 0) for u in users.find({}, {"user_withdrawn":1}))

        return await query.edit_message_text(
            f"📊 Stats\n\n"
            f"👥 Users: {total_users}\n"
            f"📈 Earned: ${round(total_earned,2)}\n"
            f"💸 Withdrawn: ${round(total_withdrawn,2)}\n"
            f"💰 Profit: ${round(total_earned-total_withdrawn,2)}",
            reply_markup=back_menu()
        )

    # =========================
    # 🏆 TOP USERS
    # =========================
    if data == "top_users":
        if user_id not in ADMIN_IDS:
            return

        top = users.find().sort("user_earned", -1).limit(20)

        text = "🏆 Top 20 Earners\n\n"
        for i, u in enumerate(top, 1):
            text += f"{i}. {u.get('name','User')} - ${round(u.get('user_earned',0),2)}\n"

        return await query.edit_message_text(text, reply_markup=back_menu())

    # =========================
    # 🚫 BAN USER
    # =========================
    if data == "ban_user":
        if user_id not in ADMIN_IDS:
            return

        context.user_data["ban_mode"] = True
        return await query.message.reply_text("Send USER ID to ban")

    # =========================
    # ➕ ADD TASK
    # =========================
    if data == "add_task":
        if user_id not in ADMIN_IDS:
            return

        context.user_data["add_task"] = True
        return await query.message.reply_text("Title | Link | Reward")

    # =========================
    # 📢 BROADCAST
    # =========================
    if data == "broadcast":
        if user_id not in ADMIN_IDS:
            return

        context.user_data["broadcast"] = True
        return await query.message.reply_text("Send message to broadcast")

    # =========================
    # ✅ APPROVE
    # =========================
    if data.startswith("approve_"):
        if user_id not in ADMIN_IDS:
            return

        target_id = int(data.split("_")[1])
        req = withdraws.find_one({"user_id": target_id, "status": "pending"})

        if not req:
            return await query.answer("Already done")

        amount = req["amount"]

        withdraws.update_one({"_id": req["_id"]}, {"$set": {"status": "approved"}})
        users.update_one({"user_id": target_id}, {"$inc": {"user_withdrawn": amount}})

        await context.bot.send_message(target_id, f"✅ Approved\n💰 ${amount}")
        return await query.edit_message_text("✅ Done")

    # =========================
    # ❌ REJECT
    # =========================
    if data.startswith("reject_"):
        if user_id not in ADMIN_IDS:
            return

        target_id = int(data.split("_")[1])
        req = withdraws.find_one({"user_id": target_id, "status": "pending"})

        if not req:
            return await query.answer("Already done")

        amount = req["amount"]

        withdraws.update_one({"_id": req["_id"]}, {"$set": {"status": "rejected"}})
        users.update_one({"user_id": target_id}, {"$inc": {"balance": amount}})

        await context.bot.send_message(target_id, "❌ Rejected (Refunded)")
        return await query.edit_message_text("❌ Done")

    
# ========= MESSAGE HANDLER =========
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    user = users.find_one({"user_id": user_id})
    if not user:
        return

    # =========================
    # 🚫 BAN CHECK
    # =========================
    if user.get("is_banned", False):
        await update.message.reply_text("🚫 You are banned from using this bot")
        return

    # =========================
    # 🚫 BAN USER SYSTEM (ADMIN)
    # =========================
    if context.user_data.get("ban_mode"):
        try:
            target_id = int(text)

            users.update_one(
                {"user_id": target_id},
                {"$set": {"is_banned": True}}
            )

            await update.message.reply_text(f"✅ User {target_id} banned")

        except:
            await update.message.reply_text("❌ Invalid user ID")

        context.user_data["ban_mode"] = False
        return

    # =========================
    # ➕ ADD TASK (ADMIN)
    # =========================
    if context.user_data.get("add_task"):
        try:
            title, link, reward = text.split("|")

            tasks.insert_one({
                "title": title.strip(),
                "link": link.strip(),
                "reward": float(reward.strip())
            })

            await update.message.reply_text("✅ Task added successfully")

        except:
            await update.message.reply_text("❌ Format:\nTitle | Link | Reward")

        context.user_data["add_task"] = False
        return

    # =========================
    # 📢 BROADCAST (ADMIN)
    # =========================
    if context.user_data.get("broadcast"):
        sent = 0

        for u in users.find({}, {"user_id": 1}):
            try:
                await context.bot.send_message(u["user_id"], text)
                sent += 1
            except:
                pass

        context.user_data["broadcast"] = False
        await update.message.reply_text(f"✅ Broadcast sent to {sent} users")
        return

    # =========================
    # 💸 WITHDRAW FLOW
    # =========================
    if context.user_data.get("awaiting_wallet"):
        amount = user.get("balance", 0)

        if amount < MIN_WITHDRAW:
            await update.message.reply_text("❌ Not enough balance")
            context.user_data["awaiting_wallet"] = False
            return

        # Save withdraw request
        withdraws.insert_one({
            "user_id": user_id,
            "wallet": text,
            "amount": amount,
            "status": "pending",
            "date": str(datetime.now())
        })

        # Reset balance
        users.update_one(
            {"user_id": user_id},
            {"$set": {"balance": 0}}
        )

        context.user_data["awaiting_wallet"] = False

        # Notify admins
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
                    f"💸 Withdraw Request\n\n"
                    f"👤 User: {user_id}\n"
                    f"💰 Amount: ${amount}\n"
                    f"🏦 Wallet: {text}",
                    reply_markup=keyboard
                )
            except:
                pass

        await update.message.reply_text("⏳ Withdraw request sent")
        return

    # =========================
    # 🧩 TASK COMPLETION (ULTIMATE)
    # =========================
    if text.startswith("/done_"):
        try:
            parts = text.split("_")

            if len(parts) < 2:
                return await update.message.reply_text("❌ Invalid format")

            task_id = parts[1]

            # Validate ObjectId
            try:
                obj_id = ObjectId(task_id)
            except:
                return await update.message.reply_text("❌ Invalid task ID")

            task = tasks.find_one({"_id": obj_id})

            if not task:
                return await update.message.reply_text("❌ Task not found")

            # Ensure completed_tasks exists
            if "completed_tasks" not in user:
                users.update_one(
                    {"user_id": user_id},
                    {"$set": {"completed_tasks": []}}
                )

            # Refresh user
            user = users.find_one({"user_id": user_id})
            completed_tasks = user.get("completed_tasks", [])

            # Prevent duplicate
            if task_id in completed_tasks:
                return await update.message.reply_text("⚠️ Already completed")

            reward = float(task.get("reward", 0))

            if reward <= 0:
                return await update.message.reply_text("❌ Invalid reward")

            # Credit reward
            users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {
                        "balance": reward,
                        "user_earned": reward
                    },
                    "$push": {"completed_tasks": task_id}
                }
            )

            await update.message.reply_text(
                f"✅ Task completed!\n💰 +${round(reward,2)}"
            )

        except Exception as e:
            print("Task Error:", e)
            await update.message.reply_text("❌ Something went wrong")

        return

# ========= MAIN =========
def main():
    if not BOT_TOKEN or not MONGO_URI:
        print("Missing ENV")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🚀 Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
