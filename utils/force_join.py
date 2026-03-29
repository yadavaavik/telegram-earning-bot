import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_channels():
    return [ch.strip() for ch in os.getenv("FORCE_CHANNELS", "").split(",") if ch.strip()]


async def is_joined(user_id, context):
    channels = get_channels()

    if not channels:
        return True

    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False

    return True


def join_buttons():
    channels = get_channels()

    buttons = [
        [InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.replace('@','')}")]
        for ch in channels
    ]

    return InlineKeyboardMarkup(buttons)
