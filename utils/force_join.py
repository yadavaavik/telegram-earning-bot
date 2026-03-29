from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 👉 ADD YOUR CHANNEL USERNAMES HERE
CHANNELS = [
    "@milkyxbubble"
]

ADMIN_ID = int(__import__("os").getenv("ADMIN_ID", "0"))


async def check_join(bot, user_id):
    # 👉 Admin bypass
    if user_id == ADMIN_ID:
        return True

    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)

            if member.status not in ["member", "administrator", "creator"]:
                return False

        except:
            return False

    return True


def join_button():
    buttons = []

    for ch in CHANNELS:
        buttons.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch.replace('@','')}")])

    buttons.append([InlineKeyboardButton("✅ I Joined", callback_data="check_join")])

    return InlineKeyboardMarkup(buttons)
