from database.mongo import users

async def create_user(user_id, ref=None):
    user = await users.find_one({"user_id": user_id})
    if user:
        return user

    data = {
        "user_id": user_id,
        "balance": 0,
        "earned": 0,
        "withdrawn": 0,
        "referrer": ref,
        "wallet": None,
        "referrals": 0,
        "last_daily": 0,
        "last_withdraw": 0   # 🔥 added
    }

    await users.insert_one(data)
    data["new"] = True
    return data
