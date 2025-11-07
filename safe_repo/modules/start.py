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
    channel_url = "https://t.me/RealOnlineIncomeEarningFreelance"
    
buttons = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Join Channel", url=channel_url)],
        [InlineKeyboardButton("Buy Premium", url="https://t.me/safe_repo_bot")]
        [InlineKeyboardButton("📖 Help", callback_data="help")]
])

@app.on_message(filters.command("start") & filters.private & ~filters.me)
async def start_command(client, message):
    join = await subscribe(client, message)
    if join == 1:
        return
    
    welcome_text = (
        f"👋 **Welcome, {message.from_user.first_name}!**\n\n"
        "🤖 **Advanced Content Saver Bot v3.0**\n\n"
        "📋 **How to use:**\n"
        "• First, login using `/login`\n"
        "• Send any **public** Telegram message link\n"
        "• Bot will fetch and save the content for you\n\n"
        "⚡ **Features:**\n"
        "• Single message saving\n"
        "• Batch downloading (up to 100 posts)\n"
        "• Custom captions & thumbnails\n"
        "• File renaming support\n\n"
        "⚠️ **Note:** Only **public** channels/groups are supported.\n\n"
        "For more details, use `/help` or check `/batch_download`\n\n"
        "✨ **Ready to get started!**"
    )
    
    await message.reply(welcome_text, reply_markup=buttons)
