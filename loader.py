import os
import importlib

def setup_handlers(app):
    for file in os.listdir("handlers"):
        if file.endswith(".py"):
            module = importlib.import_module(f"handlers.{file[:-3]}")

            if hasattr(module, "register"):
                module.register(app)
