#safe_repo

import time
import asyncio
from pyrogram import filters, Client
from safe_repo import app
from config import API_ID, API_HASH
# এখানে 'process_msg' ইম্পোর্ট করা হয়েছে
from safe_repo.core.get_func import get_msg, process_msg # এটি ঠিক আছে
from safe_repo.core.func import * # এটিও ঠিক আছে
from safe_repo.core.mongo import db
from pyrogram.errors import FloodWait

# ... আপনার বাকি কোড (যেমনে আছে) ...


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
            await msg.edit_text(
                "**Access Denied!** 🚫\n\n"
                "It looks like you're not logged in.\n"
                "To use this feature, please authenticate your account first.\n\n"
                "**Here's how:**\n"
                "1. Simply send the /login command.\n"
                "2. Follow the on-screen instructions to connect your account.\n\n"
                "It's quick and secure! 🔒"
            )
            return

        try:
            if 't.me/+' in link:
                q = await userbot_join(userbot, link)
                await msg.edit_text(q)
                return
                                        
            if 't.me/' in link:
                # --- পুরোনো কোড প্রতিস্থাপিত ---
                
                # 'E' এবং 'get_link' উপরে func.* থেকে ইম্পোর্ট করা হয়েছে
                # 'get_msg' এবং 'process_msg' উপরে get_func থেকে ইম্পোর্ট করা হয়েছে
                # 'app' উপরে safe_repo থেকে ইম্পোর্ট করা হয়েছে

                chat_id, msg_id, link_type = E(link)

                if not chat_id:
                    await msg.edit_text("লিঙ্কটি ভুল।")
                    return

                # নতুন get_msg কল করা
                fetched_msg = await get_msg(app, userbot, chat_id, msg_id, link_type)

                if fetched_msg:
                    # নতুন process_msg কল করা
                    await process_msg(app, userbot, fetched_msg, str(user_id), link_type, user_id, chat_id)
                    await msg.delete() # সফল হলে প্রসেসিং মেসেজ ডিলিট করুন
                else:
                    await msg.edit_text("মেসেজ পাওয়া যায়নি।")
                # --- নতুন কোড শেষ ---

        except Exception as e:
            await msg.edit_text(f"Link: `{link}`\n\n**Error:** {str(e)}")
                    
    except FloodWait as fw:
        await msg.edit_text(f'Try again after {fw.x} seconds due to floodwait from telegram.')
    except Exception as e:
        await msg.edit_text(f"Link: `{link}`\n\n**Error:** {str(e)}")


users_loop = {}

@app.on_message(filters.command("batch"))
async def batch_link(_, message):
    user_id = message.chat.id    
    lol = await chk_user(message, user_id)
    if lol == 1:
        return    
        
    start = await app.ask(message.chat.id, text="Please send the start link.")
    start_id = start.text
    s = start_id.split("/")[-1]
    cs = int(s)
    
    last = await app.ask(message.chat.id, text="Please send the end link.")
    last_id = last.text
    l = last_id.split("/")[-1]
    cl = int(l)

    if cl - cs > 10:
        await app.send_message(message.chat.id, "Only 10 messages allowed in batch size... Purchase premium to fly 💸")
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
            await app.send_message(message.chat.id, "Login in bot first ...")

        try:
            users_loop[user_id] = True
            
            for i in range(int(s), int(l)):
                if user_id in users_loop and users_loop[user_id]:
                    msg = await app.send_message(message.chat.id, "Processing!")
                    try:
                        x = start_id.split('/')
                        y = x[:-1]
                        result = '/'.join(y)
                        url = f"{result}/{i}"
                        link = get_link(url)
                        
                        # --- পুরোনো কোড প্রতিস্থাপিত ---
                        chat_id, msg_id, link_type = E(link)

                        if not chat_id:
                            await msg.edit_text(f"লিঙ্কটি ভুল: {link}")
                            continue # পরবর্তী লিঙ্কে যান

                        # নতুন get_msg কল করা
                        fetched_msg = await get_msg(app, userbot, chat_id, msg_id, link_type)

                        if fetched_msg:
                            # নতুন process_msg কল করা
                            await process_msg(app, userbot, fetched_msg, str(user_id), link_type, user_id, chat_id)
                            await msg.delete() # সফল হলে প্রসেসিং মেসেজ ডিলিট করুন
                        else:
                            await msg.edit_text(f"মেসেজ পাওয়া যায়নি: {link}")
                        # --- নতুন কোড শেষ ---

                        sleep_msg = await app.send_message(message.chat.id, "Sleeping for 10 seconds to avoid flood...")
                        await asyncio.sleep(8)
                        await sleep_msg.delete()
                        await asyncio.sleep(2)                                                
                    except Exception as e:
                        print(f"Error processing link {url}: {e}")
                        await msg.edit_text(f"Error processing link {url}: {e}")
                        continue
                else:
                    break
        except Exception as e:
            await app.send_message(message.chat.id, f"Error: {str(e)}")
                    
    except FloodWait as fw:
        await app.send_message(message.chat.id, f'Try again after {fw.x} seconds due to floodwait from Telegram.')
    except Exception as e:
        await app.send_message(message.chat.id, f"Error: {str(e)}")


@app.on_message(filters.command("cancel"))
async def stop_batch(_, message):
    user_id = message.chat.id
    if user_id in users_loop:
        users_loop[user_id] = False
        await app.send_message(message.chat.id, "Batch processing stopped.")
    else:
        await app.send_message(message.chat.id, "No active batch processing to stop.")
