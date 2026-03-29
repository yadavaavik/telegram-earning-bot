from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["earning_bot"]

users = db["users"]
withdraws = db["withdraws"]
tasks = db["tasks"]
completed = db["completed_tasks"]
bots = db["bots"]
