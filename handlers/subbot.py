from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.helpers import safe_handler
from modules.subbot import add_bot, get_user_bots

@safe_handler
async def subbot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("➕ Create Bot", callback_data="create_bot")],
        [InlineKeyboardButton("📊 My Bots", callback_data="my_bots")]
    ]

    await update.callback_query.edit_message_text(
        "🤖 Sub Bot Panel",
        reply_markup=InlineKeyboardMarkup(kb)
    )

@safe_handler
async def create_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "Send your bot token"
    )
    context.user_data["await_bot_token"] = True

@safe_handler
async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text(
        f"✅ Bot added: @{me.username}\n\n"
        f"👉 Add this to your bot:\n"
        f"https://t.me/{context.bot.username}"
    )

    context.user_data["await_bot_token"] = False

@safe_handler
async def my_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    bots = await get_user_bots(user_id)

    if not bots:
        await update.callback_query.edit_message_text("No bots found")
        return

    text = "📊 Your Bots:\n\n"
    for b in bots:
        text += f"@{b['username']}\n"

    await update.callback_query.edit_message_text(text)
