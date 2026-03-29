async def handle_admin(update, context, user, users):
    if not context.user_data.get("ban_mode"):
        return False

    try:
        target_id = int(update.message.text)

        users.update_one(
            {"user_id": target_id},
            {"$set": {"is_banned": True}}
        )

        await update.message.reply_text("✅ User banned")

    except:
        await update.message.reply_text("❌ Invalid ID")

    context.user_data["ban_mode"] = False
    return True
