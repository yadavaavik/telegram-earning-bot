from telegram import Update
from telegram.ext import ContextTypes
from utils.force_join import check_force_join, get_join_buttons

ADMIN_ID = 123456789  # replace with your telegram id


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Admin bypass
    if user.id != ADMIN_ID:
        joined = await check_force_join(user.id, context)

        if not joined:
            await update.message.reply_text(
                "🚫 Please join all required channels first!",
                reply_markup=get_join_buttons()
            )
            return

    # Main menu
    await update.message.reply_text(
        "🏠 *Main Menu*\n\n"
        "💰 Balance\n"
        "👥 Refer\n"
        "🧩 Tasks\n"
        "💸 Withdraw\n"
        "👑 Admin",
        parse_mode="Markdown"
    )
