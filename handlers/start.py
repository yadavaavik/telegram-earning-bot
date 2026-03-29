from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from modules.user import create_user
from utils.helpers import safe_handler

@safe_handler
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    ref = None
    if context.args:
        try:
            ref = int(context.args[0])
        except:
            pass

    await create_user(user_id, ref)

    kb = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]

    await update.message.reply_text(
        "🚀 Welcome to Earning Bot",
        reply_markup=InlineKeyboardMarkup(kb)
    )
