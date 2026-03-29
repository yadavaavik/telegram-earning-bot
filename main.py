import os
import logging
from telegram.ext import Application

from core.handlers import register_handlers
from core.errors import error_handler


# =========================
# LOGGING SYSTEM (VERY IMPORTANT)
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN")

        if not BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN not found in environment")

        # =========================
        # CREATE APPLICATION
        # =========================
        app = Application.builder().token(BOT_TOKEN).build()

        # =========================
        # REGISTER HANDLERS
        # =========================
        register_handlers(app)

        # =========================
        # ERROR HANDLER
        # =========================
        app.add_error_handler(error_handler)

        print("🚀 Bot started successfully...")

        # =========================
        # RUN BOT (POLLING)
        # =========================
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=None
        )

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        logger.exception("Bot crashed")


if __name__ == "__main__":
    main()
