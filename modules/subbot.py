from database.mongo import bots
import time

async def add_bot(owner, token, username):
    await bots.insert_one({
        "owner": owner,
        "token": token,
        "username": username,
        "time": int(time.time())
    })

async def get_user_bots(owner):
    return [b async for b in bots.find({"owner": owner})]
