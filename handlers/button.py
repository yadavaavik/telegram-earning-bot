from telegram.ext import CallbackQueryHandler

async def button_router(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data

    # 🔥 ROUTING SYSTEM
    if data == "profile":
        from handlers.profile import show_profile
        await show_profile(query, context)

    elif data == "withdraw":
        from handlers.withdraw import start_withdraw
        await start_withdraw(query, context)

    elif data == "back":
        from handlers.start import show_home
        await show_home(query, context)

    else:
        await query.edit_message_text("❌ Unknown action")

def register(app):
    app.add_handler(CallbackQueryHandler(button_router))
