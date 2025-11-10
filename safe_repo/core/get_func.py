# safe_repo/get_func.py
import asyncio
import time
import os
import subprocess
import requests
from safe_repo import app
import pymongo
from pyrogram.types import InlineKeyboardButton, CallbackQuery
from pyrogram import filters
from pyrogram.errors import (
    ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, 
    ChatInvalid, PeerIdInvalid, FloodWait, UserNotParticipant
)
from pyrogram.enums import MessageMediaType, ParseMode
from safe_repo.core.func import progress_bar, video_metadata, screenshot
from safe_repo.core.mongo import db as mongo_db_core
from pyrogram.types import Message
from config import MONGO_DB as MONGODB_CONNECTION_STRING, LOG_GROUP
import cv2
import re
from pyrogram.types import messages_and_media

# --- এই ফাংশনটি অপরিবর্তিত আছে ---
def thumbnail(sender):
    return f'{sender}.jpg' if os.path.exists(f'{sender}.jpg') else None

# ---!!! নতুন: Vj's Logic (start.py থেকে হুবহু কপি করা) !!!---
def get_message_type(msg: messages_and_media.message.Message):
    """
    Vj's get_message_type logic to identify media type.
    """
    try:
        msg.document.file_id
        return "Document"
    except:
        pass
    try:
        msg.video.file_id
        return "Video"
    except:
        pass
    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass
    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass
    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass
    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass
    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass
    try:
        msg.text
        return "Text"
    except:
        pass

# ---!!! সম্পূর্ণ নতুনভাবে লেখা get_msg (Vj's Logic + Safe Repo Features) !!!---
async def get_msg(userbot, sender, edit_id, msg_link, i, message):
    edit = ""
    chat = ""
    if "?single" in msg_link:
        msg_link = msg_link.split("?single")[0]
    msg_id = int(msg_link.split("/")[-1]) + int(i)

    
    if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
        if 't.me/b/' not in msg_link:
            chat = int('-100' + str(msg_link.split("/")[-2]))
        else:
            chat = msg_link.split("/")[-2]       
        
        try:
            chatx = message.chat.id
            msg = await userbot.get_messages(chat, msg_id)
            
            # --- Vj's Logic (Empty/Service Check) ---
            if msg.empty: return None 
            if msg.service: return None

            # --- Vj's Logic (Media Type Check) ---
            msg_type = get_message_type(msg)
            
            if not msg_type:
                # যদি কোনো মিডিয়া টাইপ না পায় (যেমন, পোল, গেম)
                await app.edit_message_text(sender, edit_id, f"Skipped: `{msg_link}`\n\n**Reason:** This message type is not downloadable.")
                return

            target_chat_id = user_chat_ids.get(chatx, chatx)

            # --- হ্যান্ডলিং: টেক্সট মেসেজ (Vj's Logic) ---
            if "Text" == msg_type or msg.media == MessageMediaType.WEB_PAGE:
                edit = await app.edit_message_text(target_chat_id, edit_id, "Cloning...")
                safe_repo = await app.send_message(sender, msg.text.html, parse_mode=ParseMode.HTML)
                if msg.pinned_message:
                    try: await safe_repo.pin(both_sides=True)
                    except: await safe_repo.pin()
                await safe_repo.copy(LOG_GROUP)                  
                await edit.delete()
                return

            # --- হ্যান্ডলিং: মিডিয়া মেসেজ (Vj's Logic + Safe Repo Features) ---
            
            edit = await app.edit_message_text(sender, edit_id, "Trying to Download...")
            
            # --- Safe Repo Feature: Download (with error checking) ---
            try:
                file = await userbot.download_media(
                    msg,
                    progress=progress_bar,
                    progress_args=("**__Downloading: __**\n",edit,time.time()))
            except ValueError:
                # Vj's get_message_type যদি কোনো কারণে ফেইল হয়, এটি ধরবে
                await app.edit_message_text(sender, edit_id, f"Failed to save: `{msg_link}`\n\n**Error:** This message doesn't contain downloadable media.")
                return
            except Exception as e:
                await app.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nDownload Error: {str(e)}')
                return
            
            # --- Safe Repo Feature: File Renaming ---
            custom_rename_tag = get_user_rename_preference(chatx)
            last_dot_index = str(file).rfind('.')
            if last_dot_index != -1 and last_dot_index != 0:
                safe_repo_ext = str(file)[last_dot_index + 1:]
                if safe_repo_ext.isalpha() and len(safe_repo_ext) <= 4:
                    original_file_name = str(file)[:last_dot_index]
                    file_extension = 'mp4' if safe_repo_ext.lower() == 'mov' else safe_repo_ext
                else:
                    original_file_name = str(file)
                    file_extension = 'mp4'
            else:
                original_file_name = str(file)
                file_extension = 'mp4'

            delete_words = load_delete_words(chatx)
            for word in delete_words:
                original_file_name = original_file_name.replace(word, "")
            new_file_name = original_file_name + " " + custom_rename_tag + "." + file_extension
            os.rename(file, new_file_name)
            file = new_file_name
            # --- রিনেম শেষ ---
            
            await edit.edit('Trying to Uplaod ...')
            
            # --- Safe Repo Feature: (HTML-Safe) Caption ---
            custom_caption = get_user_caption_preference(sender)
            original_caption = msg.caption.html if msg.caption else ''
            caption = f"{original_caption}"
            if custom_caption:
                caption = f"{caption}\n\n__**{custom_caption}**__"
            # --- ক্যাপশন শেষ ---

            safe_repo = None
            thumb_path = None

            # --- Vj's Logic: if/elif based on msg_type ---
            
            if "Document" == msg_type:
                thumb_path = thumbnail(chatx) 
                safe_repo = await app.send_document(
                    chat_id=target_chat_id,
                    document=file,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    thumb=thumb_path,
                    progress=progress_bar,
                    progress_args=('**`Uploading...`**\n', edit, time.time())
                )
                    
            elif "Video" == msg_type:
                # --- Safe Repo Feature: Video Handling ---
                metadata = video_metadata(file)      
                width = metadata['width']
                height = metadata['height']
                duration = metadata['duration']
                thumb_path = await screenshot(file, duration, chatx)              

                if duration <= 300: # শর্ট ভিডিও
                    safe_repo = await app.send_video(
                        chat_id=target_chat_id, video=file, caption=caption,
                        parse_mode=ParseMode.HTML, height=height, width=width, 
                        duration=duration, thumb=thumb_path, progress=progress_bar, 
                        progress_args=('**UPLOADING:**\n', edit, time.time())
                    ) 
                else: # লং ভিডিও
                    safe_repo = await app.send_video(
                        chat_id=target_chat_id, video=file, caption=caption,
                        parse_mode=ParseMode.HTML, supports_streaming=True,
                        height=height, width=width, duration=duration,
                        thumb=thumb_path, progress=progress_bar,
                        progress_args=('**__Uploading...__**\n', edit, time.time())
                       )
                
            elif "Animation" == msg_type:
                safe_repo = await app.send_animation(target_chat_id, file, caption=caption, parse_mode=ParseMode.HTML)

            elif "Sticker" == msg_type:
                safe_repo = await app.send_sticker(target_chat_id, file) # Stickers don't have captions

            elif "Voice" == msg_type:
                safe_repo = await app.send_voice(target_chat_id, file, caption=caption, parse_mode=ParseMode.HTML)

            elif "Audio" == msg_type:
                thumb_path = thumbnail(chatx) # Audio can have thumbs
                safe_repo = await app.send_audio(
                    chat_id=target_chat_id, audio=file, caption=caption,
                    thumb=thumb_path, parse_mode=ParseMode.HTML,
                    progress=progress_bar,
                    progress_args=('**`Uploading...`**\n', edit, time.time())
                )
            
            elif "Photo" == msg_type:
                safe_repo = await app.send_photo(target_chat_id, file, caption=caption, parse_mode=ParseMode.HTML)

            # --- আপলোড পরবর্তী কাজ ---
            if safe_repo and msg.pinned_message:
                try: await safe_repo.pin(both_sides=True)
                except: await safe_repo.pin()
            
            if safe_repo:
                await safe_repo.copy(LOG_GROUP)
            
            if os.path.exists(file):
                os.remove(file)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
                        
            await edit.delete()
        
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, UserNotParticipant):
            await app.edit_message_text(sender, edit_id, "Bot or User is not in the channel. Please join.")
            return
        except Exception as e:
            await app.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')       
        
    else: # --- পাবলিক চ্যানেল হ্যান্ডলিং (HTML-Safe Caption) ---
        edit = await app.edit_message_text(sender, edit_id, "Cloning...")
        try:
            chat = msg_link.split("/")[-2]
            await copy_message_with_chat_id(app, sender, chat, msg_id) 
            await edit.delete()
        except Exception as e:
            await app.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')

# --- এই ফাংশনটি সংশোধন করা হয়েছে (HTML-Safe Caption) ---
async def copy_message_with_chat_id(client, sender, chat_id, message_id):
    target_chat_id = user_chat_ids.get(sender, sender)
    try:
        msg = await client.get_messages(chat_id, message_id)
        
        # ---!!! সমাধান: উন্নত ক্যাপশন প্রসেসিং (Vj's Logic) !!!---
        custom_caption = get_user_caption_preference(sender)
        original_caption = msg.caption.html if msg.caption else ''
        
        final_caption = f"{original_caption}"
        if custom_caption:
            final_caption = f"{final_caption}\n\n__**{custom_caption}**__"
            
        caption = final_caption
        # ---!!! সমাধান শেষ !!!---
        
        if msg.media:
            if msg.media == MessageMediaType.VIDEO:
                result = await client.send_video(target_chat_id, msg.video.file_id, caption=caption, parse_mode=ParseMode.HTML)
            elif msg.media == MessageMediaType.DOCUMENT:
                result = await client.send_document(target_chat_id, msg.document.file_id, caption=caption, parse_mode=ParseMode.HTML)
            elif msg.media == MessageMediaType.PHOTO:
                result = await client.send_photo(target_chat_id, msg.photo.file_id, caption=caption, parse_mode=ParseMode.HTML)
            else:
                result = await client.copy_message(target_chat_id, chat_id, message_id)
        else:
            if msg.text:
                result = await client.send_message(target_chat_id, msg.text.html, parse_mode=ParseMode.HTML)
            else:
                result = await client.copy_message(target_chat_id, chat_id, message_id)

        try: await result.copy(LOG_GROUP)
        except: pass
            
        if msg.pinned_message:
            try: await result.pin(both_sides=True)
            except: await result.pin()

    except Exception as e:
        error_message = f"Error occurred while sending message to chat ID {target_chat_id}: {str(e)}"
        await client.send_message(sender, error_message)
        await client.send_message(sender, f"Make Bot admin in your Channel - {target_chat_id} and restart the process after /cancel")

# -------------- FFMPEG CODES --------------- (অপরিবর্তিত)
# (আপনার মূল কোডের এই অংশটি এখানে অপরিবর্তিত থাকবে)
# ...

# ------------------------ Button Mode Editz FOR SETTINGS ---------------------------- (অপরিবর্তিত)
# (আপনার মূল কোডের এই অংশটি এখানে অপরিবর্তিত থাকবে)
# ...

# --- ডাটাবেস সেকশন (সংশোধিত এবং উন্নত) ---
# (আগের উত্তরের বাগ ফিক্সগুলো এখানেও অন্তর্ভুক্ত আছে)

# MongoDB database name and collection names
DB_NAME = "smart_users"
SUPER_USER_COLLECTION = "super_user"
SETTINGS_COLLECTION = "user_settings" # <-- নতুন: ইউজার সেটিংসের জন্য আলাদা কালেকশন

# Establish a connection to MongoDB
mongo_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = mongo_client[DB_NAME]
collection = db[SUPER_USER_COLLECTION] # <-- এটি শুধু সুপার ইউজারদের জন্য
settings_collection = db[SETTINGS_COLLECTION] # <-- এটি ইউজার সেটিংসের জন্য

def load_authorized_users():
    authorized_users = set()
    for user_doc in collection.find():
        if "user_id" in user_doc:
            authorized_users.add(user_doc["user_id"])
    return authorized_users

def save_authorized_users(authorized_users):
    collection.delete_many({})
    for user_id in authorized_users:
        collection.insert_one({"user_id": user_id})

SUPER_USERS = load_authorized_users()
user_chat_ids = {}

# MongoDB database name and collection name for SESSIONS
MDB_NAME = "logins"
MCOLLECTION_NAME = "stringsession"

m_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
mdb = m_client[MDB_NAME]
mcollection = mdb[MCOLLECTION_NAME] # <-- এটি সেশনের জন্য

def load_delete_words(user_id):
    try:
        words_data = settings_collection.find_one({"_id": user_id})
        if words_data:
            return set(words_data.get("delete_words", []))
        else:
            return set()
    except Exception as e:
        print(f"Error loading delete words: {e}")
        return set()

def save_delete_words(user_id, delete_words):
    try:
        settings_collection.update_one(
            {"_id": user_id},
            {"$set": {"delete_words": list(delete_words)}},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving delete words: {e}")

def load_replacement_words(user_id):
    try:
        words_data = settings_collection.find_one({"_id": user_id})
        if words_data:
            return words_data.get("replacement_words", {})
        else:
            return {}
    except Exception as e:
        print(f"Error loading replacement words: {e}")
        return {}

def save_replacement_words(user_id, replacements):
    try:
        settings_collection.update_one(
            {"_id": user_id},
            {"$set": {"replacement_words": replacements}},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving replacement words: {e}")

user_rename_preferences = {}
user_caption_preferences = {}

def load_user_session(sender_id):
    # --- গুরুতর বাগ ফিক্স: সেশন লোড 'mcollection' (stringsession) থেকে করা ---
    user_data = mcollection.find_one({"user_id": sender_id})
    if user_data:
        return user_data.get("session_string") 
    else:
        return None

async def set_rename_command(user_id, custom_rename_tag):
    user_rename_preferences[str(user_id)] = custom_rename_tag

def get_user_rename_preference(user_id):
    return user_rename_preferences.get(str(user_id), 'safe_repo')

async def set_caption_command(user_id, custom_caption):
    user_caption_preferences[str(user_id)] = custom_caption

def get_user_caption_preference(user_id):
    return user_caption_preferences.get(str(user_id), '')

sessions = {}
SET_PIC = "settings.jpg"
MESS = "Customize by your end and Configure your settings ..."

@app.on_message(filters.command("settings"))
async def settings_command(event):
    buttons = [
        [Button.inline("Set Chat ID", b'setchat'), Button.inline("Set Rename Tag", b'setrename')],
        [Button.inline("Caption", b'setcaption'), Button.inline("Replace Words", b'setreplacement')],
        [Button.inline("Remove Words", b'delete'), Button.inline("Reset", b'reset')],
        [Button.inline("Login", b'addsession'), Button.inline("Logout", b'logout')],
        [Button.inline("Set Thumbnail", b'setthumb'), Button.inline("Remove Thumbnail", b'remthumb')],
        [Button.url("Report Errors", "https://t.me/safe_repo")]
    ]
    
    await gf.send_message(
        event.chat_id,
        message=MESS,
        buttons=buttons
    )

pending_photos = {}

@app.on_callback_query()
async def callback_query_handler(event):
    user_id = event.sender_id

    if event.data == b'setchat':
        await callback_query.answer("Send me the ID of that chat:")
        sessions[user_id] = 'setchat'

    elif event.data == b'setrename':
        await callback_query.answer("Send me the rename tag:")
        sessions[user_id] = 'setrename'

    elif event.data == b'setcaption':
        await callback_query.answer("Send me the caption:")
        sessions[user_id] = 'setcaption'

    elif event.data == b'setreplacement':
        await callback_query.answer("Send me the replacement words in the format: 'WORD(s)' 'REPLACEWORD'")
        sessions[user_id] = 'setreplacement'

    elif event.data == b'addsession':
        await callback_query.answer("This method depreciated ... use /login")

    elif event.data == b'delete':
        await callback_query.answer("Send words seperated by space to delete them from caption/filename ...")
        sessions[user_id] = 'deleteword'
        
    elif event.data == b'logout':
        result = mcollection.delete_one({"user_id": user_id})
        if result.deleted_count > 0:
          await callback_query.answer("Logged out and deleted session successfully.")
        else:
          await callback_query.answer("You are not logged in")   

    elif event.data == b'setthumb':
        pending_photos[user_id] = True
        await callback_query.answer('Please send the photo you want to set as the thumbnail.')

    elif event.data == b'reset':
        try:
            settings_collection.update_one(
                {"_id": user_id},
                {"$unset": {"delete_words": ""}}
            )
            await callback_query.answer("All words have been removed from your delete list.")
        except Exception as e:
            await callback_query.answer(f"Error clearing delete list: {e}")
    
    elif event.data == b'remthumb':
        try:
            os.remove(f'{user_id}.jpg')
            await callback_query.answer('Thumbnail removed successfully!')
        except FileNotFoundError:
            await callback_query.answer("No thumbnail found to remove.")


@gf.on(events.NewMessage(func=lambda e: e.sender_id in pending_photos))
async def save_thumbnail(event):
    user_id = event.sender_id
    if event.photo:
        temp_path = await event.download_media()
        if os.path.exists(f'{user_id}.jpg'):
            os.remove(f'{user_id}.jpg')
        os.rename(temp_path, f'./{user_id}.jpg')
        await callback_query.answer('Thumbnail saved successfully!')
    else:
        await callback_query.answer('Please send a photo... Retry')
    pending_photos.pop(user_id, None)


@gf.on(events.NewMessage)
async def handle_user_input(event):
    user_id = event.sender_id
    if user_id in sessions:
        session_type = sessions[user_id]

        if session_type == 'setchat':
            try:
                chat_id = int(event.text)
                user_chat_ids[user_id] = chat_id
                await callback_query.answer("Chat ID set successfully!")
            except ValueError:
                await callback_query.answer("Invalid chat ID!")
        
        elif session_type == 'setrename':
            custom_rename_tag = event.text
            await set_rename_command(user_id, custom_rename_tag)
            await callback_query.answer(f"Custom rename tag set to: {custom_rename_tag}")
        
        elif session_type == 'setcaption':
            custom_caption = event.text
            await set_caption_command(user_id, custom_caption)
            await callback_query.answer(f"Custom caption set to: {custom_caption}")

        elif session_type == 'setreplacement':
            match = re.match(r"'(.+)' '(.+)'", event.text)
            if not match:
                await callback_query.answer("Usage: 'WORD(s)' 'REPLACEWORD'")
            else:
                word, replace_word = match.groups()
                delete_words = load_delete_words(user_id)
                if word in delete_words:
                    await callback_query.answer(f"The word '{word}' is in the delete set and cannot be replaced.")
                else:
                    replacements = load_replacement_words(user_id)
                    replacements[word] = replace_word
                    save_replacement_words(user_id, replacements)
                    await callback_query.answer(f"Replacement saved: '{word}' will be replaced with '{replace_word}'")

        elif session_type == 'addsession':
            session_data = {
                "user_id": user_id,
                "session_string": event.text
            }
            mcollection.update_one(
                {"user_id": user_id},
                {"$set": session_data},
                upsert=True
            )
            await callback_query.answer("Session string added successfully.")
                
        elif session_type == 'deleteword':
            words_to_delete = event.message.text.split()
            delete_words = load_delete_words(user_id)
            delete_words.update(words_to_delete)
            save_delete_words(user_id, delete_words)
            await callback_query.answer(f"Words added to delete list: {', '.join(words_to_delete)}")

        del sessions[user_id]
