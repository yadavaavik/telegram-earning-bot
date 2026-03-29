def safe_handler(func):
    async def wrapper(update, context):
        try:
            return await func(update, context)
        except Exception as e:
            print("ERROR:", e)
    return wrapper
