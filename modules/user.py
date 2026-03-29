from database.mongo import users

async def get_user(user_id):
    return await users.find_one({"user_id": user_id})

async def create_user(user_id, ref=None):
    user = await get_user(user_id)
    if user:
        return user

    data = {
        "user_id": user_id,
        "balance": 0,
        "earned": 0,
        "withdrawn": 0,
        "referrer": ref,
        "wallet": None
    }
    await users.insert_one(data)
    return data
