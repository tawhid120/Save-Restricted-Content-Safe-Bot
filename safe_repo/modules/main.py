import time
import asyncio
from pyrogram import filters, Client
from safe_repo import app, USER_CLIENTS # <--- USER_CLIENTS এখানে ইম্পোর্ট করা হয়েছে
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

# এই ডিকশনারি ব্যাচ প্রসেসিং ট্র্যাক করার জন্য
users_loop = {}

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

        # --- সেশন ক্যাশ সমাধান ---
        # ১. প্রথমে ক্যাশ (USER_CLIENTS) থেকে অ্যাক্টিভ সেশন খুঁজুন
        userbot = USER_CLIENTS.get(user_id)

        if not userbot:
            # ২. যদি ক্যাশে না থাকে (যেমন বট রিস্টার্ট হলে), তাহলে ডাটাবেস থেকে লোড করুন
            data = await db.get_data(user_id)
            if data and data.get("session"):
                session = data.get("session")
                try:
                    # একটি নতুন নাম ব্যবহার করুন (e.g., user_id) সেশন কনফ্লিক্ট এড়ানোর জন্য
                    userbot_session_name = f"userbot_{user_id}"
                    userbot = Client(userbot_session_name, api_id=API_ID, api_hash=API_HASH, session_string=session, in_memory=True)
                    await userbot.start()
                    USER_CLIENTS[user_id] = userbot  # ৩. এবং চালু করে আবার ক্যাশে সেভ করুন
                except Exception as e:
                    print(f"Failed to start session from DB for user {user_id}: {e}")
                    return await msg.edit_text(f"Login expired or session invalid: {e}. Please /login again.")
            else:
                # যদি ডাটাবেসেও সেশন না থাকে, তাহলে লগইন করতে বলুন
                await msg.edit_text(LOGIN_ERROR_MESSAGE, parse_mode=ParseMode.MARKDOWN)
                return
        # --- সেশন ক্যাশ সমাধান শেষ ---
        
        # এখন userbot একটি "গরম" এবং অ্যাক্টিভ সেশন
        try:
            if '?' in link: # এটি একটি ব্যাচ লিঙ্ক
                
                # ... (আপনার ব্যাচ লজিক এখানে শুরু) ...
                links = link.split('?')
                if len(links) != 2:
                    await msg.edit_text("Invalid batch link format!")
                    return

                try:
                    from_msg_id = int(links[0].split('/')[-1])
                    to_msg_id = int(links[1].split('/')[-1])
                except ValueError:
                    await msg.edit_text("Invalid message IDs in batch link.")
                    return

                # ইউজারকে লুপে যোগ করা
                users_loop[user_id] = True
                
                total_messages = to_msg_id - from_msg_id
                if total_messages > 100: # একটি লিমিট সেট করা ভালো
                     await msg.edit(f"Batch too large (max 100). Processing first 100 messages.")
                     to_msg_id = from_msg_id + 100

                process_msg = await msg.edit_text(f"Batch processing started for {total_messages} messages.\n\nTo stop, send /cancel.")
                
                # ব্যাচ প্রসেসিং লুপ
                count = 0
                for i in range(from_msg_id, to_msg_id + 1):
                    if users_loop.get(user_id) == False: # যদি ইউজার /cancel করে
                        break 
                    
                    url = f"{links[0].rsplit('/', 1)[0]}/{i}"
                    try:
                        await get_msg(userbot, _, message, url)
                        count += 1
                        if count % 10 == 0: # প্রতি ১০টি মেসেজের পর আপডেট দিন
                            await process_msg.edit_text(f"Processing... {count}/{total_messages} done.")
                        time.sleep(1) # টেলিগ্রাম ফ্লাড এড়াতে সামান্য দেরি
                    except FloodWait as fw:
                        await app.send_message(message.chat.id, f'Flood wait: Pausing for {fw.value} seconds...')
                        await asyncio.sleep(fw.value)
                    except Exception as e:
                        print(f"Error processing link {url}: {e}")
                        await app.send_message(message.chat.id, f"Failed to process link: {url}\nError: {e}")
                        continue
                
                # লুপ শেষ হলে একটি ফাইনাল মেসেজ
                if users_loop.get(user_id): # যদি cancel না হয়ে থাকে
                    await process_msg.edit_text(f"**Batch processing completed!**\nTotal {count} messages processed.")
                        
            else: # এটি একটি সিঙ্গেল লিঙ্ক
                await get_msg(userbot, _, message, link)
                await msg.delete() # সফল হলে "Processing..." মেসেজ ডিলিট করুন

        except Exception as e:
            await msg.edit_text(f"Error: {str(e)}")
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
        await app.send_message(message.chat.id, "No active batch process to stop.")
