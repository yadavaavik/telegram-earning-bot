from utils.helpers import safe_handler
from database.mongo import users
from modules.daily import claim_daily
from utils.admin import is_admin

@safe_handler
async def button_handler(update, context):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    user = await users.find_one({"user_id": uid})

    if data == "balance":
        await q.edit_message_text(f"{user['balance']}")

    elif data == "refer":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await q.edit_message_text(link)

    elif data == "daily":
        ok = await claim_daily(uid)
        await q.edit_message_text("Done" if ok else "Wait")

    elif data == "withdraw":
        context.user_data["w"] = True
        await q.edit_message_text("Send wallet")

    elif data == "tasks":
        from handlers.tasks import show_tasks
        await show_tasks(update, context)

    elif data.startswith("task_"):
        from handlers.tasks import do_task
        await do_task(update, context)

    elif data == "subbot":
        from handlers.subbot import menu
        await menu(update, context)

    elif data == "admin" and is_admin(uid):
        from handlers.admin import panel
        await panel(update, context)
