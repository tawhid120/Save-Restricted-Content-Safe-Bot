# safe_repo/core/get_func.py
# এই ফাইলটি devgaganin (batch.py) এবং tawhid120 (original_func.py) এর সমন্বয়ে তৈরি করা হয়েছে।
# (উন্নত সংস্করণ: ৪জিবি সাপোর্ট, টেক্সট রুলস এবং কাস্টম থাম্বনেইল সহ)

import os
import re
import time
import asyncio
import cv2
import subprocess
import math
from datetime import datetime as dt
from typing import Optional, Tuple

# Pyrogram ইম্পোর্ট
from pyrogram import enums
from pyrogram.errors import (
    FloodWait, InviteHashInvalid, InviteHashExpired, 
    UserAlreadyParticipant, UserNotParticipant
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# tawhid120 প্রজেক্টের নিজস্ব ইম্পোর্ট
from config import CHANNEL_ID, OWNER_ID, LOG_GROUP
from safe_repo.core import script
from safe_repo.core.mongo import db
from safe_repo.core.func import rename_file # আপনার নির্দেশনা অনুযায়ী ইম্পোর্ট

# devgaganin (batch.py) থেকে আনা ক্লায়েন্ট ইম্পোর্ট
try:
    from safe_repo import userbot as Y
except ImportError:
    Y = None # যদি userbot সেটআপ করা না থাকে

# devgaganin (batch.py) থেকে আনা গ্লোবাল ভেরিয়েবল
P = {}
emp = {}


# --- devgaganin (batch.py) থেকে আনা ফাংশন ---

def sanitize(filename: str) -> str:
    """
    ফাইল ও ডিরেক্টরির নামে অবৈধ ক্যারেক্টারগুলো প্রতিস্থাপন করে।
    """
    return re.sub(r'[<>:"/\\|?*\']', '_', filename).strip(" .")[:255]


async def upd_dlg(c) -> bool:
    """
    ইউজারবটের ডায়ালগ লিস্ট আপডেট করে।
    """
    try:
        async for _ in c.get_dialogs(limit=100):
            pass
        return True
    except Exception as e:
        print(f'Failed to update dialogs: {e}')
        return False


async def get_msg(c, u, i: str, d: int, lt: str):
    """
    সোর্স চ্যাট থেকে মেসেজ আনে। (devgaganin লজিক)
    """
    try:
        if lt == 'public':
            try:
                if str(i).lower().endswith('bot'):
                    emp[i] = False
                    xm = await u.get_messages(i, d)
                    emp[i] = getattr(xm, "empty", False)
                    if not emp[i]:
                        emp[i] = True
                        print(f"Bot chat found successfully...")
                        return xm
                    
                if emp[i]:
                    xm = await c.get_messages(i, d)
                    print(f"fetched by {c.me.username}")
                    emp[i] = getattr(xm, "empty", False)
                    if emp[i]:
                        print(f"Not fetched by {c.me.username}")
                        try: await u.join_chat(i)
                        except: pass
                        xm = await u.get_messages((await u.get_chat(f"@{i}")).id, d)
                    
                    return xm                   
            except Exception as e:
                print(f'Error fetching public message: {e}')
                return None
        else: # private
            if u:
                try:
                    async for _ in u.get_dialogs(limit=50): pass
                    
                    if str(i).startswith('-100'):
                        chat_id_100 = int(i)
                        base_id = str(i)[4:]
                        chat_id_dash = int(f"-{base_id}")
                    elif i.isdigit():
                        chat_id_100 = int(f"-100{i}")
                        chat_id_dash = int(f"-{i}")
                    else:
                        chat_id_100 = int(i)
                        chat_id_dash = int(i)
                    
                    # Try -100 format first
                    try:
                        result = await u.get_messages(chat_id_100, d)
                        if result and not getattr(result, "empty", False):
                            return result
                    except Exception:
                        pass
                    
                    # Try - format second
                    try:
                        result = await u.get_messages(chat_id_dash, d)
                        if result and not getattr(result, "empty", False):
                            return result
                    except Exception:
                        pass
                    
                    # Final fallback
                    try:
                        async for _ in u.get_dialogs(limit=200): pass
                        result = await u.get_messages(int(i), d) # মূল 'i' দিয়ে চেষ্টা
                        if result and not getattr(result, "empty", False):
                            return result
                    except Exception:
                        pass
                    
                    return None
                            
                except Exception as e:
                    print(f'Private channel error: {e}')
                    return None
            return None
    except Exception as e:
        print(f'Error fetching message: {e}')
        return None


async def prog(c, t, C, h, m, st):
    """
    ডাউনলোড/আপলোড პროগ্রেস বার দেখায়।
    """
    global P
    if t == 0: return # ZeroDivisionError এড়াতে
    
    p = c / t * 100
    interval = 10 if t >= 100 * 1024 * 1024 else 20 if t >= 50 * 1024 * 1024 else 30 if t >= 10 * 1024 * 1024 else 50
    step = int(p // interval) * interval
    if m not in P or P[m] != step or p >= 100:
        P[m] = step
        c_mb = c / (1024 * 1024)
        t_mb = t / (1024 * 1024)
        bar = '🟢' * int(p / 10) + '🔴' * (10 - int(p / 10))
        
        diff = time.time() - st
        if diff == 0: diff = 0.001 # ZeroDivisionError এড়াতে
            
        speed = c / diff / (1024 * 1024)
        eta = time.strftime('%M:%S', time.gmtime((t - c) / (speed * 1024 * 1024))) if speed > 0 else '00:00'
        
        try:
            await C.edit_message_text(h, m, f"__**Pyro Handler...**__\n\n{bar}\n\n⚡**__Completed__**: {c_mb:.2f} MB / {t_mb:.2f} MB\n📊 **__Done__**: {p:.2f}%\n🚀 **__Speed__**: {speed:.2f} MB/s\n⏳ **__ETA__**: {eta}\n\n**__Powered by @tawhid120__**")
        except:
            pass
        if p >= 100: P.pop(m, None)


async def send_direct(c, m, tcid, ft=None, rtmid=None):
    """
    মিডিয়া ফাইল সরাসরি ফরওয়ার্ড/সেন্ড করে (যদি সম্ভব হয়)।
    """
    try:
        if m.video:
            await c.send_video(tcid, m.video.file_id, caption=ft, duration=m.video.duration, width=m.video.width, height=m.video.height, reply_to_message_id=rtmid)
        elif m.video_note:
            await c.send_video_note(tcid, m.video_note.file_id, reply_to_message_id=rtmid)
        elif m.voice:
            await c.send_voice(tcid, m.voice.file_id, reply_to_message_id=rtmid)
        elif m.sticker:
            await c.send_sticker(tcid, m.sticker.file_id, reply_to_message_id=rtmid)
        elif m.audio:
            await c.send_audio(tcid, m.audio.file_id, caption=ft, duration=m.audio.duration, performer=m.audio.performer, title=m.audio.title, reply_to_message_id=rtmid)
        elif m.photo:
            photo_id = m.photo.file_id if hasattr(m.photo, 'file_id') else m.photo[-1].file_id
            await c.send_photo(tcid, photo_id, caption=ft, reply_to_message_id=rtmid)
        elif m.document:
            await c.send_document(tcid, m.document.file_id, caption=ft, file_name=m.document.file_name, reply_to_message_id=rtmid)
        else:
            return False
        return True
    except Exception as e:
        print(f'Direct send error: {e}')
        return False


# --- নতুন যুক্ত করা উন্নত ফাংশন ---

async def process_text_with_rules(user_data: dict, text: str) -> str:
    """
    ক্যাপশন থেকে শব্দ ডিলেট এবং রিপ্লেস করে।
    """
    if not user_data:
        return text

    delete_words = user_data.get('delete_words', [])
    replacement_words = user_data.get('replacement_words', {})

    if not delete_words and not replacement_words:
        return text

    # শব্দ ডিলেট করা
    if delete_words:
        for word in delete_words:
            text = text.replace(word, "")

    # শব্দ রিপ্লেস করা
    if replacement_words:
        for old, new in replacement_words.items():
            text = text.replace(old, new)
            
    # অতিরিক্ত স্পেস পরিষ্কার করা
    text = ' '.join(text.split())
    return text


async def get_thumbnail(user_data: dict, video_file: str, duration: int, user_id: int) -> Optional[str]:
    """
    প্রথমে কাস্টম থাম্বনেইল খোঁজে, না পেলে নতুন জেনারেট করে।
    """
    custom_thumb = user_data.get('thumb')
    
    if custom_thumb and os.path.exists(custom_thumb):
        return custom_thumb
    
    # কাস্টম থাম্বনেইল না থাকলে, নতুন জেনারেট করা
    return await screenshot(video_file, duration, user_id)


# --- মূল প্রসেসিং ফাংশন (উন্নত সংস্করণ) ---

async def process_msg(c, u, m, d, lt, uid, i):
    """
    মেসেজ প্রসেস, ডাউনলোড এবং আপলোড করে। (উন্নত সংস্করণ)
    """
    try:
        # --- Tawhid120 রিফ্যাক্টরিং: ইউজার ডেটাবেস থেকে সেটিংস আনা ---
        user_data = await db.get_data(d) # 'd' হলো user_id
        if not user_data:
            user_data = {} 
        
        cfg_chat = user_data.get('chat_id', None)
        
        tcid = d
        rtmid = None
        if cfg_chat:
            if '/' in cfg_chat:
                parts = cfg_chat.split('/', 1)
                tcid = int(parts[0])
                rtmid = int(parts[1]) if len(parts) > 1 else None
            else:
                tcid = int(cfg_chat)
        
        if m.media:
            orig_text = m.caption.markdown if m.caption else ''
            
            # --- উন্নত ফিচার: টেক্সট প্রসেসিং ---
            proc_text = await process_text_with_rules(user_data, orig_text)
            
            user_cap = user_data.get('caption', '')
            ft = f'{proc_text}\n\n{user_cap}' if proc_text and user_cap else user_cap if user_cap else proc_text
            
            if lt == 'public' and not emp.get(i, False):
                await send_direct(c, m, tcid, ft, rtmid)
                return 'Sent directly.'
            
            st = time.time()
            p = await c.send_message(d, 'Downloading...')

            c_name = f"{time.time()}"
            file_name = None

            if m.video: file_name = m.video.file_name
            elif m.audio: file_name = m.audio.file_name
            elif m.document: file_name = m.document.file_name
            
            if file_name:
                c_name = sanitize(file_name)
            else:
                ext = ".mp4" if m.video else ".mp3" if m.audio else ".jpg" if m.photo else ""
                c_name = sanitize(f"{time.time()}{ext}")


            f = await u.download_media(m, file_name=c_name, progress=prog, progress_args=(c, d, p.id, st))
            
            if not f:
                await c.edit_message_text(d, p.id, 'Failed to download.')
                return 'Failed.'
            
            await c.edit_message_text(d, p.id, 'Renaming...')
            if file_name: # যদি মূল ফাইলের নাম থাকে তবেই রিনেম চেষ্টা করা
                f = await rename_file(f, d, p)
            
            fsize_bytes = os.path.getsize(f)
            fsize_gb = fsize_bytes / (1024 * 1024 * 1024)
            
            # --- উন্নত ফিচার: ৪জিবি সাপোর্ট (devgaganin লজিক) ---
            if fsize_gb > 2 and Y: # Y হলো userbot
                st = time.time()
                await c.edit_message_text(d, p.id, 'File is larger than 2GB. Using Userbot...')
                await upd_dlg(Y)
                
                mtd = video_metadata(f)
                dur, h, w = mtd['duration'], mtd['height'], mtd['width']
                th = await get_thumbnail(user_data, f, dur, d) # কাস্টম থাম্বনেইল চেক
                
                sent = None
                try:
                    if m.video:
                        sent = await Y.send_video(LOG_GROUP, f, thumb=th, caption=ft,
                                                duration=dur, height=h, width=w,
                                                reply_to_message_id=rtmid, progress=prog, progress_args=(c, d, p.id, st))
                    elif m.audio:
                         sent = await Y.send_audio(LOG_GROUP, f, thumb=th, caption=ft,
                                                 duration=dur,
                                                 reply_to_message_id=rtmid, progress=prog, progress_args=(c, d, p.id, st))
                    else: # ডকুমেন্ট হিসেবে পাঠানো
                        sent = await Y.send_document(LOG_GROUP, f, thumb=th, caption=ft,
                                                    reply_to_message_id=rtmid, progress=prog, progress_args=(c, d, p.id, st))
                    
                    if sent:
                        await c.copy_message(d, LOG_GROUP, sent.id)
                    else:
                        raise Exception("Userbot failed to send.")
                        
                except Exception as e:
                    print(f"4GB Upload Error: {e}")
                    await c.edit_message_text(d, p.id, f'Userbot upload failed: {e}')
                    if os.path.exists(f): os.remove(f)
                    if th and os.path.exists(th) and th != user_data.get('thumb'): os.remove(th)
                    return 'Failed (Userbot).'

                if os.path.exists(f): os.remove(f)
                if th and os.path.exists(th) and th != user_data.get('thumb'): os.remove(th)
                await c.delete_messages(d, p.id)
                
                return 'Done (Large file via Userbot).'
            
            # --- ২জিবির কম ফাইলের জন্য সাধারণ আপলোড ---
            
            await c.edit_message_text(d, p.id, 'Uploading...')
            st = time.time()
            th = None # রিসেট

            try:
                video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ogv']
                audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.aiff', '.ac3']
                file_ext = os.path.splitext(f)[1].lower() if f else ""

                if m.video or (m.document and file_ext in video_extensions):
                    mtd = video_metadata(f) 
                    dur, h, w = mtd['duration'], mtd['height'], mtd['width']
                    th = await get_thumbnail(user_data, f, dur, d) # কাস্টম থাম্বনেইল চেক
                    await c.send_video(tcid, video=f, caption=ft, 
                                    thumb=th, width=w, height=h, duration=dur, 
                                    progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.video_note:
                    await c.send_video_note(tcid, video_note=f, progress=prog, 
                                        progress_args=(c, d, p.id, st), reply_to_message_id=rtmid)
                elif m.voice:
                    await c.send_voice(tcid, f, progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.sticker:
                    await c.send_sticker(tcid, m.sticker.file_id, reply_to_message_id=rtmid)
                elif m.audio or (m.document and file_ext in audio_extensions):
                    # অডিওর জন্য কাস্টম থাম্বনেইল
                    th = user_data.get('thumb') if user_data.get('thumb') and os.path.exists(user_data.get('thumb')) else None
                    await c.send_audio(tcid, audio=f, caption=ft, 
                                    thumb=th, progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.photo:
                    await c.send_photo(tcid, photo=f, caption=ft, 
                                    progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.document:
                    # ডকুমেন্টের জন্য কাস্টম থাম্বনেইল
                    th = user_data.get('thumb') if user_data.get('thumb') and os.path.exists(user_data.get('thumb')) else None
                    await c.send_document(tcid, document=f, caption=ft, thumb=th,
                                        progress=prog, progress_args=(c, d, p.id, st), 
                                        reply_to_message_id=rtmid)
                else:
                    await c.send_document(tcid, document=f, caption=ft,
                                        progress=prog, progress_args=(c, d, p.id, st), 
                                        reply_to_message_id=rtmid)
            except Exception as e:
                await c.edit_message_text(d, p.id, f'Upload failed: {str(e)[:30]}')
                if os.path.exists(f): os.remove(f)
                if th and os.path.exists(th) and th != user_data.get('thumb'): os.remove(th)
                return 'Failed.'
            
            if os.path.exists(f): os.remove(f)
            if th and os.path.exists(th) and th != user_data.get('thumb'): os.remove(th)
            await c.delete_messages(d, p.id)
            
            return 'Done.'
            
        elif m.text:
            await c.send_message(tcid, text=m.text.markdown, reply_to_message_id=rtmid)
            return 'Sent.'
    except Exception as e:
        print(f"Process_msg Error: {e}")
        return f'Error: {str(e)[:50]}'


# --- tawhid120 (original_func.py) থেকে আনা হেল্পার ফাংশন ---
# (কিছু ফাংশন process_msg-এর জন্য জরুরি, বাকিগুলো সম্পূর্ণতার জন্য রাখা হলো)

async def chk_user(message, user_id):
    return 0 # প্রিমিয়াম চেক আপাতত বাইপাস করা হলো

async def gen_link(app,chat_id):
   link = await app.export_chat_invite_link(chat_id)
   return link

async def subscribe(app, message):
   update_channel = CHANNEL_ID
   if not update_channel:
       return 0 # চ্যানেল সেট করা না থাকলে বাইপাস
       
   url = await gen_link(app, update_channel)
   if update_channel:
      try:
         user = await app.get_chat_member(update_channel, message.from_user.id)
         if user.status == enums.ChatMemberStatus.KICKED: # enums ব্যবহার
            await message.reply_text("You are Banned. Contact -- @safe_repo")
            return 1
      except UserNotParticipant:
         await message.reply_photo(photo="https://graph.org/file/d44f024a08ded19452152.jpg",caption=script.FORCE_MSG.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Now...", url=f"{url}")]]))
         return 1
      except Exception as e:
         print(e)
         await message.reply_text("Something Went Wrong. Contact us @safe_repo...")
         return 1
   return 0


async def get_seconds(time_string: str) -> int:
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:].lstrip()
        if value:
            value = int(value)
        return value, unit

    value, unit = extract_value_and_unit(time_string)

    if unit == 's': return value
    elif unit == 'min': return value * 60
    elif unit == 'hour': return value * 3600
    elif unit == 'day': return value * 86400
    elif unit == 'month': return value * 86400 * 30
    elif unit == 'year': return value * 86400 * 365
    else: return 0

PROGRESS_BAR = """\n
**__Completed__** : {1}/{2}
**__Bytes__** : {0}%
**__Speed__** : {3}/s
**__Time__** : {4}
"""

async def progress_bar(current, total, ud_type, message, start):
    if total == 0: return
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_str = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time_str = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["🟢" for i in range(math.floor(percentage / 10))]),
            ''.join(["🔴" for i in range(10 - math.floor(percentage / 10))]))
            
        tmp = progress + PROGRESS_BAR.format( 
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time_str if estimated_total_time_str != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n\n{}".format(ud_type, tmp),)             
        except:
            pass

def humanbytes(size: int) -> str:
    if not size: return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2] 

def convert(seconds: int) -> str:
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60      
    return "%d:%02d:%02d" % (hour, minutes, seconds)

async def userbot_join(userbot, invite_link: str) -> str:
    try:
        await userbot.join_chat(invite_link)
        return "Successfully joined the Channel"
    except UserAlreadyParticipant:
        return "User is already a participant."
    except (InviteHashInvalid, InviteHashExpired):
        return "Could not join. Maybe your link is expired or Invalid."
    except FloodWait as e:
        return f"Too many requests, try again after {e.value} seconds."
    except Exception as e:
        print(e)
        return "Could not join, try joining manually."

def get_link(string: str) -> Optional[str]:
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)   
    try:
        link = [x[0] for x in url][0]
        if link:
            return link
        else:
            return None
    except Exception:
        return None

def video_metadata(file: str) -> dict:
    """
    ভিডিও ফাইলের মেটাডেটা (duration, width, height) বের করে।
    """
    default_values = {'width': 0, 'height': 0, 'duration': 0}
    try:
        vcap = cv2.VideoCapture(file)
        if not vcap.isOpened():
            return default_values

        width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = vcap.get(cv2.CAP_PROP_FPS)
        frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)

        if fps > 0 and frame_count > 0:
            duration = round(frame_count / fps)
        else:
            duration = 0 # ডিফল্ট

        vcap.release()
        
        # যদি কোনো কারণে 0 ভ্যালু আসে, সেগুলোকে 1 দিয়ে রিপ্লেস করা (আপলোড ফেইল এড়াতে)
        return {
            'width': width if width > 0 else 1, 
            'height': height if height > 0 else 1, 
            'duration': duration if duration > 0 else 1
        }

    except Exception as e:
        print(f"Error in video_metadata: {e}")
        return {'width': 1, 'height': 1, 'duration': 1} # ফেইল করলে ডিফল্ট
    
def hhmmss(seconds: int) -> str:
    """
    সেকেন্ডকে H:M:S ফরম্যাটে রূপান্তর করে।
    """
    return time.strftime('%H:%M:%S', time.gmtime(seconds))

async def screenshot(video: str, duration: int, sender: int) -> Optional[str]:
    """
    ভিডিও থেকে স্ক্রিনশট নেয়।
    """
    thumb_path = f'{sender}.jpg'
    if os.path.exists(thumb_path):
        try: os.remove(thumb_path) # পুরানো থাম্বনেইল ডিলেট করা
        except: pass

    # সময়কে ০ এর বেশি হতে বাধ্য করা
    ss_time = max(0.1, int(duration) / 2)
    time_stamp = hhmmss(ss_time)
    
    out = dt.now().isoformat("_", "seconds") + ".jpg"
    cmd = ["ffmpeg",
           "-ss", f"{time_stamp}", 
           "-i", f"{video}",
           "-frames:v", "1", 
           f"{out}",
           "-y"
          ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    x = stderr.decode().strip()
    y = stdout.decode().strip()
    
    if os.path.isfile(out):
        return out
    else:
        print(f"Screenshot failed: {x} {y}")
        return None


