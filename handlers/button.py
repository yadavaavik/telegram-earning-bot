from telegram import Update
from telegram.ext import ContextTypes
from database.mongo import users
from utils.helpers import safe_handler

@safe_handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    user = await users.find_one({"user_id": user_id})

    if data == "balance":
        await query.edit_message_text(
            f"💰 Balance: {user['balance']}\nEarned: {user['earned']}"
        )

    elif data == "refer":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(f"👥 Your link:\n{link}")

    elif data == "withdraw":
        await query.edit_message_text("Send wallet address")
        context.user_data["await_wallet"] = True
