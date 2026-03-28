import telebot
import os
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

bot = telebot.TeleBot(BOT_TOKEN)

client = MongoClient(MONGO_URI)
db = client["earnbot"]

users = db["users"]


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    user = users.find_one({"user_id": user_id})

    if not user:
        users.insert_one({
            "user_id": user_id,
            "balance": 0,
            "wallet": None,
            "created_at": message.date
        })

    bot.reply_to(message, "✅ You are registered!")


print("Bot running...")
bot.infinity_polling()
