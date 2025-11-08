import time
import asyncio
from pyrogram import filters, Client
from safe_repo import app
from config import API_ID, API_HASH
from safe_repo.core.get_func import get_msg
from safe_repo.core.func import *
from safe_repo.core.mongo import db
from pyrogram.errors import FloodWait
from pyrogram.enums import ParseMode

# আমরা লগইন মেসেজটিকে একটি ভেরিয়েবলে রাখছি যাতে দুই জায়গায় ব্যবহার করা যায়
LOGIN_ERROR_MESSAGE = """**Access Denied! 🚫**

It looks like you're not logged in.
To use this feature, please authenticate your account first.

**Here's how:**
1. Simply send the /login command.
2. Follow the on-screen instructions to connect your account.

**It's quick and secure! 🔒**

If you want to use it without logging in, you can use this bot (@Save_restricted_content_pbot), but it will only work in public channels or groups. In private channels or groups, this bot will need a user account to use it.
"""


@app.on_message(filters.regex(r'https?://[^\s]+'))
async def single_link(_, message):
    user_id = message.chat.id
    lol = await chk_user(message, user_id)
    if lol == 1:
        return
    
    link = get_link(message.text) 
    
    try:
        join = await subscribe(_, message)
        if join == 1:
            return
     
        msg = await message.reply("Processing...")
        data = await db.get_data(user_id)
        
        if data and data.get("session"):
            session = data.get("session")
            try:
                userbot = Client(":userbot:", api_id=API_ID, api_hash=API_HASH, session_string=session)
                await userbot.start()                
            except:
                return await msg.edit_text("Login expired /login again...")
        else:
            # ঠিক করা হয়েছে: এখানে ParseMode.MARKDOWN যোগ করা হয়েছে
            await msg.edit_text(LOGIN_ERROR_MESSAGE, parse_mode=ParseMode.MARKDOWN)
            return

        try:
            if 't.me/+' in link:
                q = await userbot_join(userbot, link)
                await msg.edit_text(q)
                return
                                        
            if 't.me/' in link:
                await get_msg(userbot, user_id, msg.id, link, 0, message)
        except Exception as e:
            # ঠিক করা হয়েছে: আপনার কথামতো এরর মেসেজ থেকে `` চিহ্ন বাদ দেওয়া হয়েছে
            await msg.edit_text(f"Link: {link}\n\n**Error:** {str(e)}")
                    
    except FloodWait as fw:
        await msg.edit_text(f'Try again after {fw.x} seconds due to floodwait from telegram.')
    except Exception as e:
        # ঠিক করা হয়েছে: আপনার কথামতো এরর মেসেজ থেকে `` চিহ্ন বাদ দেওয়া হয়েছে
        await msg.edit_text(f"Link: {link}\n\n**Error:** {str(e)}")


users_loop = {}

@app.on_message(filters.command("batch"))
async def batch_link(_, message):
    user_id = message.chat.id    
    lol = await chk_user(message, user_id)
    if lol == 1:
        return    
    
    try:
        start = await app.ask(message.chat.id, text="Please send the start link.")
        start_id = start.text
        s = start_id.split("/")[-1]
        cs = int(s)
    except ValueError:
        await app.send_message(message.chat.id, "Invalid start link. Please enter a valid message link.")
        return
    except Exception as e:
        await app.send_message(message.chat.id, f"Error reading start link: {e}")
        return

    try:
        last = await app.ask(message.chat.id, text="Please send the end link.")
        last_id = last.text
        l = last_id.split("/")[-1]
        cl = int(l)
    except ValueError:
        await app.send_message(message.chat.id, "Invalid end link. Please enter a valid message link.")
        return
    except Exception as e:
        await app.send_message(message.chat.id, f"Error reading end link: {e}")
        return

    if cl <= cs:
        await app.send_message(message.chat.id, "End link must be after the start link.")
        return

    # ঠিক করা হয়েছে: আসল সংখ্যা গণনা
    total_messages = (cl + 1) - cs

    if total_messages > 10: # আপনার আসল কোডে 10 ছিল
        await app.send_message(message.chat.id, f"Batch size is too large ({total_messages} messages). Maximum allowed is 10... Purchase premium to fly 💸")
        return
    
    try:     
        data = await db.get_data(user_id)
        
        if data and data.get("session"):
            session = data.get("session")
            try:
                userbot = Client(":userbot:", api_id=API_ID, api_hash=API_HASH, session_string=session)
                await userbot.start()                
            except:
                return await app.send_message(message.chat.id, "Your login expired ... /login again")
        else:
            # ঠিক করা হয়েছে: এখানেও একই সুন্দর লগইন মেসেজ এবং ParseMode যোগ করা হয়েছে
            await app.send_message(message.chat.id, LOGIN_ERROR_MESSAGE, parse_mode=ParseMode.MARKDOWN)
            return

        try:
            users_loop[user_id] = True
            
            # ঠিক করা হয়েছে: মেসেজ স্প্যাম কমানো
            process_msg = await app.send_message(message.chat.id, f"Batch processing started for {total_messages} messages...")
            
            # ঠিক করা হয়েছে: লুপটি cl + 1 পর্যন্ত চলবে (যাতে শেষ মেসেজটিও প্রসেস হয়)
            for i in range(cs, cl + 1):
                if user_id in users_loop and users_loop[user_id]:
                    current_count = (i - cs) + 1
                    try:
                        x = start_id.split('/')
                        y = x[:-1]
                        result = '/'.join(y)
                        url = f"{result}/{i}"
                        link = get_link(url)

                        await process_msg.edit_text(f"**Processing: {current_count}/{total_messages}**\nLink: {url}")
                        
                        await get_msg(userbot, user_id, process_msg.id, link, 0, message)
                        
                        # স্লিপ মেসেজটি এডিট করা হচ্ছে
                        await process_msg.edit_text(f"**Processed: {current_count}/{total_messages}**\nSleeping for 10 seconds to avoid flood...")
                        await asyncio.sleep(10)                                                
                    except Exception as e:
                        print(f"Error processing link {url}: {e}")
                        await app.send_message(message.chat.id, f"Failed to process link: {url}\nError: {e}")
                        continue
                else:
                    await app.send_message(message.chat.id, "Batch processing stopped by user.")
                    break
            
            # লুপ শেষ হলে একটি ফাইনাল মেসেজ
            if users_loop.get(user_id): # যদি cancel না হয়ে থাকে
                await process_msg.edit_text(f"**Batch processing completed!**\nTotal {total_messages} messages processed.")
                    
        except Exception as e:
            await app.send_message(message.chat.id, f"Error: {str(e)}")
        finally:
            # ব্যাচ শেষ হলে বা বাতিল হলে ইউজারকে লুপ থেকে রিমুভ করা
            users_loop.pop(user_id, None) 
                    
    except FloodWait as fw:
        await app.send_message(message.chat.id, f'Try again after {fw.x} seconds due to floodwait from Telegram.')
    except Exception as e:
        await app.send_message(message.chat.id, f"Error: {str(e)}")


@app.on_message(filters.command("cancel"))
async def stop_batch(_, message):
    user_id = message.chat.id
    if user_id in users_loop:
        users_loop[user_id] = False
        await app.send_message(message.chat.id, "Batch processing stopping... Please wait.")
    else:
        await app.send_message(message.chat.id, "No active batch processing to stop.")
