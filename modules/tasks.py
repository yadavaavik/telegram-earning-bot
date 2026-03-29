from database.mongo import tasks, completed
from modules.balance import add_balance

async def get_tasks():
    return [t async for t in tasks.find()]

async def complete_task(user_id, task):
    exists = await completed.find_one({
        "user_id": user_id,
        "task_id": task["_id"]
    })

    if exists:
        return False

    await completed.insert_one({
        "user_id": user_id,
        "task_id": task["_id"]
    })

    await add_balance(user_id, task.get("reward", 1))
    return True
