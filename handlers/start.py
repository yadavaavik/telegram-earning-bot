from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database.mongo import users
from utils.force_join import check_join, join_button
from utils.helpers import safe_handler

@safe_handler
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # 👉 Create user if not exists
    if not await users.find_one({"user_id": user_id}):
        await users.insert_one({
            "user_id": user_id,
            "balance": 0,
            "referrals": 0,
            "earned": 0,
            "withdrawn": 0
        })

    # 👉 FORCE JOIN CHECK
    if not await check_join(context.bot, user_id):
        await update.message.reply_text(
            "⚠️ Please join our channel first",
            reply_markup=join_button()
        )
        return

    # 👉 MAIN MENU
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("🧩 Tasks", callback_data="tasks")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
    ]

    # 👉 Admin button
    import os
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])

    await update.message.reply_text(
        "🏠 Main Menu",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
