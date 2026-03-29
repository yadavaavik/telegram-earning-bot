from db import db

tasks_col = db["tasks"]
users_col = db["users"]


# ✅ GET OR CREATE USER (SAFE)
async def get_user(user_id):
    user = await users_col.find_one({"user_id": user_id})

    if not user:
        user = {
            "user_id": user_id,
            "balance": 0,
            "earned": 0,
            "withdrawn": 0,
            "tasks_done": []
        }
        await users_col.insert_one(user)

    else:
        # 🔥 fix old users automatically
        if "tasks_done" not in user:
            await users_col.update_one(
                {"user_id": user_id},
                {"$set": {"tasks_done": []}}
            )
            user["tasks_done"] = []

    return user


# ✅ GET ALL ACTIVE TASKS
async def get_tasks():
    return await tasks_col.find({"active": True}).to_list(length=50)


# ✅ COMPLETE TASK (ANTI DUPLICATE)
async def complete_task(user_id, task):
    user = await get_user(user_id)

    if task["task_id"] in user["tasks_done"]:
        return False, "already"

    reward = int(task.get("reward", 0))

    await users_col.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": reward,
                "earned": reward
            },
            "$push": {
                "tasks_done": task["task_id"]
            }
        }
    )

    return True, reward
