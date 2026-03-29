from utils.helpers import safe_handler
from database.mongo import users, withdraws
from payments.crypto import send_crypto
from modules.balance import deduct_balance
from handlers.subbot import token_handler

@safe_handler
async def msg_handler(update, context):
    uid = update.effective_user.id
    text = update.message.text

    await token_handler(update, context)

    if context.user_data.get("w"):
        user = await users.find_one({"user_id": uid})

        if user["balance"] < 10:
            await update.message.reply_text("Min not reached")
            return

        tx = await send_crypto(text, user["balance"])
        await deduct_balance(uid, user["balance"])

        await withdraws.insert_one({
            "user_id": uid,
            "amount": user["balance"],
            "tx": tx
        })

        await update.message.reply_text(f"Sent {tx}")
        context.user_data["w"] = False
