from telegram import Update
from telegram.ext import ContextTypes
from database.mongo import users
from modules.balance import deduct_balance
from payments.crypto import send_crypto
from utils.helpers import safe_handler

MIN_WITHDRAW = 10

@safe_handler
async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if context.user_data.get("await_wallet"):
        user = await users.find_one({"user_id": user_id})

        if user["balance"] < MIN_WITHDRAW:
            await update.message.reply_text("❌ Minimum withdraw not reached")
            return

        tx = await send_crypto(text, user["balance"])
        await deduct_balance(user_id, user["balance"])

        await update.message.reply_text(f"✅ Withdraw sent\nTX: {tx}")
        context.user_data["await_wallet"] = False
