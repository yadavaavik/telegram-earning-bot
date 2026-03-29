from database.mongo import users
from modules.balance import add_balance

REF_BONUS = 2

async def process_referral(new_user_id, ref_id):
    if not ref_id or ref_id == new_user_id:
        return

    ref_user = await users.find_one({"user_id": ref_id})
    if not ref_user:
        return

    await add_balance(ref_id, REF_BONUS)

    await users.update_one(
        {"user_id": ref_id},
        {"$inc": {"referrals": 1}}
    )
