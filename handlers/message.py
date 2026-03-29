from telegram.ext import MessageHandler, filters

async def msg_handler(update, context):
    await update.message.reply_text("📩 Message received")

def register(app):
    app.add_handler(MessageHandler(filters.TEXT, msg_handler))
