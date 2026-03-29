from database.db import users

async def show_profile(query, context):
    user_id = query.from_user.id
    user = await users.find_one({"user_id": user_id})

    text = f"""
👤 Profile

💰 Balance: ₹{user['balance']}
📈 Earned: ₹{user['user_earned']}
💸 Withdrawn: ₹{user['user_withdrawn']}
"""

    await query.edit_message_text(text)
