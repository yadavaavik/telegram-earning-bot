from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN

from core.handlers import register_handlers
from core.errors import error_handler

app = ApplicationBuilder().token(BOT_TOKEN).build()

register_handlers(app)
app.add_error_handler(error_handler)

app.run_polling()
