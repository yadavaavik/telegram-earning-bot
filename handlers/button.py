from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.mongo import users
from modules.daily import claim_daily
from utils.helpers import safe_handler

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🎯 Tasks", callback_data="tasks")]
    ])

@safe_handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    user = await users.find_one({"user_id": user_id})

    if data == "balance":
        await query.edit_message_text(
            f"💰 Balance: {user['balance']}\nEarned: {user['earned']}\nWithdrawn: {user['withdrawn']}",
            reply_markup=menu()
        )

    elif data == "refer":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(
            f"👥 Invite & earn\n{link}",
            reply_markup=menu()
        )

    elif data == "daily":
        ok = await claim_daily(user_id)
        if ok:
            text = "🎁 Bonus claimed!"
        else:
            text = "⏳ Come back tomorrow"

        await query.edit_message_text(text, reply_markup=menu())

    elif data == "withdraw":
        await query.edit_message_text("💸 Send wallet address")
        context.user_data["await_wallet"] = True
        
    elif data == "tasks":
        from handlers.tasks import show_tasks
        await show_tasks(update, context)

    elif data.startswith("task_"):
        from handlers.tasks import task_click
        await task_click(update, context)
