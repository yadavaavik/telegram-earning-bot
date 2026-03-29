import time
from database.mongo import users

COOLDOWN = 300  # 5 minutes

async def can_withdraw(user_id):
    user = await users.find_one({"user_id": user_id})

    now = int(time.time())
    last = user.get("last_withdraw", 0)

    if now - last < COOLDOWN:
        return False

    return True

async def set_withdraw_time(user_id):
    await users.update_one(
        {"user_id": user_id},
        {"$set": {"last_withdraw": int(time.time())}}
    )
