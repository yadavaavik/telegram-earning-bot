from telegram.ext import CommandHandler

async def start(update, context):
    await show_home(update.message, context)

async def show_home(message_or_query, context):
    text = "🏠 Welcome to Sxm Earning Bot"

    from keyboards.menu import main_menu
    await message_or_query.reply_text(text, reply_markup=main_menu())

def register(app):
    app.add_handler(CommandHandler("start", start))
