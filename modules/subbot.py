from database.mongo import db
import time

bots_col = db["bots"]

async def add_bot(owner_id, token, username):
    await bots_col.insert_one({
        "owner_id": owner_id,
        "token": token,
        "username": username,
        "created_at": int(time.time())
    })

async def get_user_bots(owner_id):
    bots = []
    async for b in bots_col.find({"owner_id": owner_id}):
        bots.append(b)
    return bots
