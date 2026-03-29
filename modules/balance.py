from database.mongo import users

async def add_balance(user_id, amount):
    await users.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": amount, "earned": amount}}
    )

async def deduct_balance(user_id, amount):
    await users.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": -amount, "withdrawn": amount}}
    )
