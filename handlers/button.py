from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.mongo import users
from utils.force_join import check_join
from utils.helpers import safe_handler

@safe_handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    # 👉 JOIN CHECK BUTTON
    if query.data == "check_join":
        if await check_join(context.bot, user_id):
            await query.message.edit_text("✅ Joined successfully!\n\nUse /start")
        else:
            await query.answer("❌ You haven't joined yet", show_alert=True)

    # 👉 BALANCE
    elif query.data == "balance":
        user = await users.find_one({"user_id": user_id})

        text = (
            f"💰 Balance: ${user['balance']}\n"
            f"👥 Referrals: {user['referrals']}\n"
            f"📈 Earned: ${user['earned']}\n"
            f"💸 Withdrawn: ${user['withdrawn']}"
        )

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # 👉 BACK
    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("💰 Balance", callback_data="balance")],
            [InlineKeyboardButton("👥 Refer", callback_data="refer")],
            [InlineKeyboardButton("🧩 Tasks", callback_data="tasks")],
            [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        ]

        import os
        ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])

        await query.message.edit_text(
            "🏠 Main Menu",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 👉 REFER
    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username

        link = f"https://t.me/{bot_username}?start={user_id}"

        await query.message.edit_text(
            f"👥 Your Referral Link:\n{link}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # 👉 TASKS
    elif query.data == "tasks":
        await query.message.edit_text(
            "🧩 Tasks coming soon...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # 👉 WITHDRAW
    elif query.data == "withdraw":
        context.user_data["w"] = True

        await query.message.edit_text(
            "💸 Send your USDT (TRC20) wallet address:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

    # 👉 ADMIN
    elif query.data == "admin":
        import os
        ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

        if user_id != ADMIN_ID:
            await query.answer("❌ Not allowed", show_alert=True)
            return

        await query.message.edit_text(
            "👑 Admin Panel",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )
