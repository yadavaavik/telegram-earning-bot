from telegram import Update
from telegram.ext import ContextTypes
from database.mongo import users, withdraws
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

        amount = user["balance"]

        tx = await send_crypto(text, amount)

        await deduct_balance(user_id, amount)

        await withdraws.insert_one({
            "user_id": user_id,
            "amount": amount,
            "wallet": text,
            "tx": tx
        })

        await update.message.reply_text(f"✅ Withdraw sent\nTX: {tx}")

        context.user_data["await_wallet"] = False
