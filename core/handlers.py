from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters

from handlers.start import start_cmd
from handlers.button import button_handler
from handlers.message import msg_handler

def register_handlers(app):
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
