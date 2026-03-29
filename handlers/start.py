from utils.force_join import is_joined, join_buttons

ADMIN_ID = 123456789  # your id


async def start_cmd(update, context):
    user = update.effective_user

    if user.id != ADMIN_ID:
        if not await is_joined(user.id, context):
            await update.message.reply_text(
                "🚫 Join required channels first",
                reply_markup=join_buttons()
            )
            return

    # continue your existing menu logic BELOW (DO NOT REMOVE YOUR CODE)
