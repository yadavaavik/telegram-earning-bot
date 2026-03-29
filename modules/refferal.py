from database.mongo import users
from modules.balance import add_balance

async def process_referral(new_user, ref):
    if not ref or ref == new_user:
        return

    ref_user = await users.find_one({"user_id": ref})
    if not ref_user:
        return

    await add_balance(ref, 2)

    await users.update_one(
        {"user_id": ref},
        {"$inc": {"referrals": 1}}
    )
