from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CHANNELS = [
    "@milkyxbubble"  # <-- put your channel
]

ADMIN_ID = 8250329715 # <-- your telegram id


async def check_force_join(bot, user_id):
    if user_id == ADMIN_ID:
        return True

    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False

    return True


def get_join_buttons():
    buttons = []

    for channel in CHANNELS:
        link = f"https://t.me/{channel.replace('@','')}"
        buttons.append([InlineKeyboardButton("📢 Join Channel", url=link)])

    buttons.append([InlineKeyboardButton("✅ Check", callback_data="check_join")])

    return InlineKeyboardMarkup(buttons)
