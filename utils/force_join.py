CHANNELS = ["@yourchannel"]

async def check_join(update, context):
    user_id = update.effective_user.id

    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False

    return True
