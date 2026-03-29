from telegram.ext import CallbackQueryHandler

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "profile":
        await query.edit_message_text("👤 Profile opened")

def register(app):
    app.add_handler(CallbackQueryHandler(button_handler))
