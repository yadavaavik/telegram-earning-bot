async def handle_withdraw(update, context, user, users, withdraws, MIN_WITHDRAW, ADMIN_IDS):
    if not context.user_data.get("awaiting_wallet"):
        return False

    text = update.message.text
    user_id = update.effective_user.id

    amount = user.get("balance", 0)

    if amount < MIN_WITHDRAW:
        await update.message.reply_text("❌ Not enough balance")
        context.user_data["awaiting_wallet"] = False
        return True

    withdraws.insert_one({
        "user_id": user_id,
        "wallet": text,
        "amount": amount,
        "status": "pending"
    })

    users.update_one(
        {"user_id": user_id},
        {"$set": {"balance": 0}}
    )

    context.user_data["awaiting_wallet"] = False

    await update.message.reply_text("✅ Withdraw request sent")

    return True
