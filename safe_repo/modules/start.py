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

@app.on_message(filters.command("help") & filters.private & ~filters.me)
async def help_command(client, message):
    help_text = (
        "📚 **Help & Commands Guide**\n\n"
        "**🔐 Login:**\n"
        "`/login` - Login with your phone number\n"
        "`/logout` - Remove your session\n\n"
        "**⚙️ Settings:**\n"
        "`/settings` - Configure bot preferences\n"
        "• Set custom caption\n"
        "• Set custom thumbnail\n"
        "• Set rename tag\n"
        "• Manage delete/replace words\n\n"
        "**📥 Download:**\n"
        "• Send any public channel/group link\n"
        "• Batch format: `https://t.me/channel/100-110`\n"
        "• Use `/cancel` to stop batch process\n\n"
        "**👤 Account:**\n"
        "`/myplan` - Check your premium status\n\n"
        "**📖 Examples:**\n"
        "**Single:** `https://t.me/channel/123`\n"
        "**Batch:** `https://t.me/channel/100-110`\n\n"
        "❓ **Need support?** Contact @safe_repo"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])
    
    await message.reply(help_text, reply_markup=buttons)

@app.on_message(filters.command("batch_download") & filters.private & ~filters.me)
async def batch_command(client, message):
    batch_help_text = (
        "📦 **Batch Download Guide**\n\n"
        "To save multiple posts at once, use the **range format**:\n\n"
        "**Format:**\n"
        "`https://t.me/channel_username/START_ID-END_ID`\n\n"
        "**Examples:**\n"
        "✅ `https://t.me/example/1001-1010` (10 posts)\n"
        "✅ `https://t.me/example/500-600` (100 posts)\n\n"
        "📌 **Rules:**\n"
        "• Maximum **100 posts** per batch\n"
        "• Only **public** channels/groups supported\n"
        "• Spaces in range are allowed: `101 - 120`\n\n"
        "🛑 **Stop batch:** Use `/cancel` command\n\n"
        "💡 **Tip:** Login first using `/login` for faster downloads!"
    )
    
    await message.reply(batch_help_text)
