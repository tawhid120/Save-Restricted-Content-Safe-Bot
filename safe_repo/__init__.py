#safe_repo

import asyncio
import logging
from pyromod import listen
from pyrogram import Client
# from telethon import TelegramClient  <--- COMMENT OUT OR DELETE
from config import API_ID, API_HASH, BOT_TOKEN

loop = asyncio.get_event_loop()

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

# Telethon client (sexrepo)
# sex = TelegramClient('sexrepo', API_ID, API_HASH).start(bot_token=BOT_TOKEN) <--- COMMENT OUT OR DELETE THIS LINE

# Pyrogram bot client
app = Client(
    ":RestrictBot:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=10,
    sleep_threshold=20,
    max_concurrent_transmissions=5
)

# Userbot for handling sessions (initially None)
userbot = None

async def restrict_bot():
    global BOT_ID, BOT_NAME, BOT_USERNAME, userbot
    await app.start()
    getme = await app.get_me()
    BOT_ID = getme.id
    BOT_USERNAME = getme.username
    if getme.last_name:
        BOT_NAME = getme.first_name + " " + getme.last_name
    else:
        BOT_NAME = getme.first_name
    
    # Initialize userbot as None (will be created per-user in get_func.py)
    userbot = None

loop.run_until_complete(restrict_bot())
