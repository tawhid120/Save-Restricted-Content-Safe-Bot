import os
from pyrogram import filters
from safe_repo import app
from safe_repo.core import script
from safe_repo.core.func import subscribe
from config import OWNER_ID
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# ------------------- Start-Buttons ------------------- #
FORCE_SUB_USERNAME = os.environ.get("FORCE_SUB")

if FORCE_SUB_USERNAME:
    channel_url = f"https://t.me/{FORCE_SUB_USERNAME}"
else:
    channel_url = "https://t.me/safe_repo"
    
buttons = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Join Channel", url=channel_url)],
        [InlineKeyboardButton("Buy Premium", url="https://t.me/safe_repo_bot")]
    ]
)

@app.on_message(filters.command("start"))
async def start(_, message):
    join = await subscribe(_, message)
    if join == 1:
        return
    await message.reply_text(text=script.START_TXT.format(message.from_user.mention), 
                              reply_markup=buttons)
