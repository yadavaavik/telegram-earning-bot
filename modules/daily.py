import time
from database.mongo import users
from modules.balance import add_balance

DAILY_BONUS = 1

async def claim_daily(user_id):
    user = await users.find_one({"user_id": user_id})

    now = int(time.time())
    last = user.get("last_daily", 0)

    if now - last < 86400:
        return False

    await add_balance(user_id, DAILY_BONUS)

    await users.update_one(
        {"user_id": user_id},
        {"$set": {"last_daily": now}}
    )

    return True
