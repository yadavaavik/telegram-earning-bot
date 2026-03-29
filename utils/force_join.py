import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Get channels from ENV
def get_channels():
    channels = os.getenv("FORCE_CHANNELS", "")
    return [ch.strip() for ch in channels.split(",") if ch.strip()]


# Check if user joined all channels
async def check_force_join(user_id, context):
    channels = get_channels()

    if not channels:
        return True  # No force join set

    for channel in channels:
        try:
            member = await context.bot.get_chat_member(channel, user_id)

            if member.status not in ["member", "administrator", "creator"]:
                return False

        except Exception:
            return False

    return True


# Create join buttons
def get_join_buttons():
    channels = get_channels()

    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                f"Join {ch}",
                url=f"https://t.me/{ch.replace('@','')}"
            )
        ])

    return InlineKeyboardMarkup(buttons)
