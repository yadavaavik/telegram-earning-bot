from utils.helpers import safe_handler
from database.mongo import users, withdraws
from payments.crypto import send_crypto
from modules.balance import deduct_balance
from handlers.subbot import token_handler
from modules.security import can_withdraw, set_withdraw_time

MIN_WITHDRAW = 10

@safe_handler
async def msg_handler(update, context):
    uid = update.effective_user.id
    text = update.message.text

    # sub-bot token handler
    await token_handler(update, context)

    if context.user_data.get("w"):
        user = await users.find_one({"user_id": uid})

        # ❌ minimum check
        if user["balance"] < MIN_WITHDRAW:
            await update.message.reply_text("❌ Minimum withdraw not reached")
            return

        # ❌ cooldown check
        if not await can_withdraw(uid):
            await update.message.reply_text("⏳ Wait before next withdraw")
            return

        # ❌ wallet validation (TRC20)
        if not text.startswith("T"):
            await update.message.reply_text("❌ Invalid TRC20 wallet")
            return

        amount = user["balance"]

        # 💰 send crypto
        tx = await send_crypto(text, amount)

        # 💰 update balance
        await deduct_balance(uid, amount)

        # ⏱ set cooldown
        await set_withdraw_time(uid)

        # 💾 save withdraw
        await withdraws.insert_one({
            "user_id": uid,
            "amount": amount,
            "wallet": text,
            "tx": tx
        })

        await update.message.reply_text(
            f"✅ Withdraw Sent\n\nTX ID: {tx}"
        )

        context.user_data["w"] = False
