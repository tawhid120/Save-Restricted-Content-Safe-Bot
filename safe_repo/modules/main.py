#safe_repo

import time
import asyncio
from pyrogram import filters, Client
from safe_repo import app
from config import API_ID, API_HASH
from safe_repo.core.get_func import get_msg, process_msg
from safe_repo.core.func import chk_user, subscribe, get_link, E
from safe_repo.core.mongo import db
from pyrogram.errors import FloodWait


@app.on_message(filters.regex(r'https?://[^\s]+'))
async def single_link(_, message):
    user_id = message.chat.id
    
    # Check user permissions
    lol = await chk_user(message, user_id)
    if lol == 1:
        return
    
    link = get_link(message.text)
    
    try:
        # Check force subscribe
        join = await subscribe(_, message)
        if join == 1:
            return
     
        msg = await message.reply("Processing...")
        data = await db.get_data(user_id)
        
        # Get or create userbot
        userbot = None
        if data and data.get("session"):
            session = data.get("session")
            try:
                userbot = Client(f":userbot_{user_id}:", api_id=API_ID, api_hash=API_HASH, session_string=session)
                await userbot.start()
            except:
                await msg.edit_text("Login expired. Use /login again...")
                return
        else:
            await msg.edit_text(
                "**Access Denied!** 🚫\n\n"
                "Please login first using /login command."
            )
            return

        try:
            # Handle invite links
            if 't.me/+' in link:
                try:
                    await userbot.join_chat(link)
                    await msg.edit_text("Joined channel successfully!")
                except Exception as e:
                    await msg.edit_text(f"Could not join: {str(e)}")
                return
                                        
            # Handle normal message links
            if 't.me/' in link:
                chat_id, msg_id, link_type = E(link)

                if not chat_id:
                    await msg.edit_text("Invalid link format.")
                    return

                # Fetch message
                fetched_msg = await get_msg(app, userbot, chat_id, msg_id, link_type)

                if fetched_msg:
                    # Process and upload
                    result = await process_msg(app, userbot, fetched_msg, str(user_id), link_type, user_id, chat_id)
                    await msg.delete()
                else:
                    await msg.edit_text("Message not found. Make sure you've joined the channel/group in your logged account.")

        except Exception as e:
            await msg.edit_text(f"Error: {str(e)}")
        finally:
            # Cleanup userbot
            if userbot:
                await userbot.stop()
                    
    except FloodWait as fw:
        await message.reply_text(f'Try again after {fw.x} seconds due to floodwait.')
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")


users_loop = {}

@app.on_message(filters.command("batch"))
async def batch_link(_, message):
    user_id = message.chat.id
    
    # Check permissions
    lol = await chk_user(message, user_id)
    if lol == 1:
        return
    
    # Get start and end links
    start = await app.ask(message.chat.id, text="Send the start link:")
    start_id = start.text
    s = start_id.split("/")[-1]
    cs = int(s)
    
    last = await app.ask(message.chat.id, text="Send the end link:")
    last_id = last.text
    l = last_id.split("/")[-1]
    cl = int(l)

    if cl - cs > 10:
        await app.send_message(message.chat.id, "Only 10 messages allowed in batch. Purchase premium for more!")
        return
    
    try:
        data = await db.get_data(user_id)
        
        # Get or create userbot
        userbot = None
        if data and data.get("session"):
            session = data.get("session")
            try:
                userbot = Client(f":userbot_{user_id}:", api_id=API_ID, api_hash=API_HASH, session_string=session)
                await userbot.start()
            except:
                await app.send_message(message.chat.id, "Login expired. Use /login again...")
                return
        else:
            await app.send_message(message.chat.id, "Please login first using /login.")
            return

        try:
            users_loop[user_id] = True
            
            for i in range(int(s), int(l)):
                if user_id in users_loop and users_loop[user_id]:
                    msg = await app.send_message(message.chat.id, "Processing!")
                    try:
                        # Build link
                        x = start_id.split('/')
                        y = x[:-1]
                        result = '/'.join(y)
                        url = f"{result}/{i}"
                        link = get_link(url)
                        
                        chat_id, msg_id, link_type = E(link)

                        if not chat_id:
                            await msg.edit_text(f"Invalid link: {link}")
                            continue

                        # Fetch and process
                        fetched_msg = await get_msg(app, userbot, chat_id, msg_id, link_type)

                        if fetched_msg:
                            await process_msg(app, userbot, fetched_msg, str(user_id), link_type, user_id, chat_id)
                            await msg.delete()
                        else:
                            await msg.edit_text(f"Message not found: {link}")

                        # Sleep between messages
                        sleep_msg = await app.send_message(message.chat.id, "Sleeping for 10 seconds...")
                        await asyncio.sleep(8)
                        await sleep_msg.delete()
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        print(f"Error processing link {url}: {e}")
                        await msg.edit_text(f"Error: {str(e)[:30]}")
                        continue
                else:
                    break
            
            await app.send_message(message.chat.id, f'Batch completed!')
        
        finally:
            # Cleanup
            users_loop.pop(user_id, None)
            if userbot:
                await userbot.stop()
                    
    except FloodWait as fw:
        await app.send_message(message.chat.id, f'Try again after {fw.x} seconds.')
    except Exception as e:
        await app.send_message(message.chat.id, f"Error: {str(e)}")


@app.on_message(filters.command("cancel"))
async def stop_batch(_, message):
    user_id = message.chat.id
    if user_id in users_loop:
        users_loop[user_id] = False
        await app.send_message(message.chat.id, "Batch processing stopped.")
    else:
        await app.send_message(message.chat.id, "No active batch to stop.")
```

---

## **Testing Steps:**

1. **Test public channel:**
```
   https://t.me/examplechannel/123
```

2. **Test private channel (after /login):**
```
   https://t.me/c/1234567890/456
```

3. **Test batch:**
```
   /batch
   [Send start link: https://t.me/examplechannel/1]
   [Send end link: https://t.me/examplechannel/10]
