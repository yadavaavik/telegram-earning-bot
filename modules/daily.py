import time
from database.mongo import users
from modules.balance import add_balance

async def claim_daily(user_id):
    user = await users.find_one({"user_id": user_id})
    now = int(time.time())

    if now - user.get("last_daily", 0) < 86400:
        return False

    await add_balance(user_id, 1)

    await users.update_one(
        {"user_id": user_id},
        {"$set": {"last_daily": now}}
    )

    return True
