from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import safe_handler
from modules.user import create_user
from modules.referral import process_referral
from utils.force_join import check_join
from utils.admin import is_admin

@safe_handler
async def start_cmd(update, context):
    if not await check_join(update, context):
        await update.message.reply_text("Join channels first")
        return

    uid = update.effective_user.id

    ref = int(context.args[0]) if context.args else None

    user = await create_user(uid, ref)

    if user.get("new"):
        await process_referral(uid, ref)

    kb = [
        ["💰 Balance", "balance"],
        ["👥 Refer", "refer"],
        ["🎯 Tasks", "tasks"],
        ["🎁 Daily", "daily"],
        ["💸 Withdraw", "withdraw"],
        ["🤖 My Bots", "subbot"]
    ]

    buttons = [[InlineKeyboardButton(t, callback_data=d)] for t, d in kb]

    if is_admin(uid):
        buttons.append([InlineKeyboardButton("👑 Admin", callback_data="admin")])

    await update.message.reply_text(
        "Welcome",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
