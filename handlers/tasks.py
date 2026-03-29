from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from modules.tasks import get_tasks, complete_task
from utils.helpers import safe_handler

@safe_handler
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = await get_tasks()

    if not tasks:
        await update.callback_query.edit_message_text("No tasks available")
        return

    buttons = []
    for t in tasks:
        buttons.append([
            InlineKeyboardButton(
                f"Task {t['_id']}",
                callback_data=f"task_{t['_id']}"
            )
        ])

    await update.callback_query.edit_message_text(
        "🎯 Available Tasks",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@safe_handler
async def task_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    task_id = query.data.split("_")[1]

    ok = await complete_task(user_id, task_id)

    if ok:
        await query.edit_message_text("✅ Task completed + reward added")
    else:
        await query.edit_message_text("❌ Already completed")
