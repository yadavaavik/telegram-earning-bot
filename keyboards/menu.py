from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ])
