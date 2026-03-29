@safe_handler
async def token_handler(update, context):
    if not context.user_data.get("await_bot_token"):
        return

    token = update.message.text
    user_id = update.effective_user.id

    try:
        from telegram import Bot
        bot = Bot(token)
        me = await bot.get_me()
    except:
        await update.message.reply_text("❌ Invalid token")
        return

    await add_bot(user_id, token, me.username)

    await update.message.reply_text(f"✅ Bot added: @{me.username}")

    context.user_data["await_bot_token"] = False
