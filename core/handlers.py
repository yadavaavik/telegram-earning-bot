from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 👉 Import all handlers
from handlers.start import start_cmd
from handlers.button import button_handler
from handlers.message import msg_handler


def register_handlers(app):
    # =========================
    # COMMAND HANDLERS
    # =========================
    app.add_handler(CommandHandler("start", start_cmd), group=0)

    # =========================
    # CALLBACK BUTTON HANDLERS
    # =========================
    app.add_handler(CallbackQueryHandler(button_handler), group=1)

    # =========================
    # MESSAGE HANDLER (LAST)
    # =========================
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler),
        group=2
    )

    print("✅ Handlers registered successfully")
