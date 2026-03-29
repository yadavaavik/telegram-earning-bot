from database.mongo import users, db
from modules.balance import add_balance

tasks_col = db["tasks"]
completed_col = db["completed_tasks"]

# sample task reward
TASK_REWARD = 1

async def get_tasks():
    tasks = []
    async for t in tasks_col.find():
        tasks.append(t)
    return tasks

async def complete_task(user_id, task_id):
    already = await completed_col.find_one({
        "user_id": user_id,
        "task_id": task_id
    })

    if already:
        return False

    await completed_col.insert_one({
        "user_id": user_id,
        "task_id": task_id
    })

    await add_balance(user_id, TASK_REWARD)
    return True
