# safe_repo/core/get_func.py
# এই ফাইলটি এখন safe_repo/core/func.py থেকে হেল্পার ফাংশন ইম্পোর্ট করে।

import os
import re
import time
import asyncio
from typing import Optional

# Pyrogram ইম্পোর্ট
from pyrogram.errors import UserNotParticipant

# tawhid120 প্রজেক্টের নিজস্ব ইম্পোর্ট
from config import LOG_GROUP
from safe_repo.core.mongo import db

# --- func.py থেকে হেল্পার ফাংশন ইম্পোর্ট করা ---
from safe_repo.core.func import (
    rename_file,
    get_video_metadata as video_metadata, # <--- এখানে পরিবর্তন করা হয়েছে
    screenshot,
    hhmmss,
    humanbytes,
    TimeFormatter
)

# devgaganin (batch.py) থেকে আনা ক্লায়েন্ট ইম্পোর্ট
try:
    from safe_repo import userbot as Y
except ImportError:
    Y = None # যদি userbot সেটআপ করা না থাকে
# ... বাকি কোড অপরিবর্তিত
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
    ডাউনলোড/আপলোড პროগ্রেস বার দেখায়। (devgaganin-এর টেক্সট-ভিত্তিক)
    """
    global P
    if t == 0: return 
    
    p = c / t * 100
    interval = 10 if t >= 100 * 1024 * 1024 else 20 if t >= 50 * 1024 * 1024 else 30 if t >= 10 * 1024 * 1024 else 50
    step = int(p // interval) * interval
    if m not in P or P[m] != step or p >= 100:
        P[m] = step
        c_mb = c / (1024 * 1024)
        t_mb = t / (1024 * 1024)
        bar = '🟢' * int(p / 10) + '🔴' * (10 - int(p / 10))
        
        diff = time.time() - st
        if diff == 0: diff = 0.001 
            
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

    if delete_words:
        for word in delete_words:
            text = text.replace(word, "")

    if replacement_words:
        for old, new in replacement_words.items():
            text = text.replace(old, new)
            
    text = ' '.join(text.split())
    return text


async def get_thumbnail(user_data: dict, video_file: str, duration: int, user_id: int) -> Optional[str]:
    """
    প্রথমে কাস্টম থাম্বনেইল খোঁজে, না পেলে নতুন জেনারেট করে।
    এটি func.py থেকে screenshot ইম্পোর্ট করে।
    """
    custom_thumb = user_data.get('thumb')
    
    if custom_thumb and os.path.exists(custom_thumb):
        return custom_thumb
    
    return await screenshot(video_file, duration, user_id)


# --- মূল প্রসেসিং ফাংশন (উন্নত সংস্করণ) ---

async def process_msg(c, u, m, d, lt, uid, i):
    """
    মেসেজ প্রসেস, ডাউনলোড এবং আপলোড করে। (উন্নত সংস্করণ)
    এটি func.py থেকে video_metadata, screenshot, rename_file ইম্পোর্ট করে।
    """
    try:
        user_data = await db.get_data(d) 
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
            if file_name: 
                f = await rename_file(f, d, p)
            
            fsize_bytes = os.path.getsize(f)
            fsize_gb = fsize_bytes / (1024 * 1024 * 1024)
            
            if fsize_gb > 2 and Y: 
                st = time.time()
                await c.edit_message_text(d, p.id, 'File is larger than 2GB. Using Userbot...')
                await upd_dlg(Y)
                
                mtd = await video_metadata(f) # func.py থেকে ইম্পোর্ট করা
                dur, h, w = mtd['duration'], mtd['height'], mtd['width']
                th = await get_thumbnail(user_data, f, dur, d)
                
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
                    else: 
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
            
            await c.edit_message_text(d, p.id, 'Uploading...')
            st = time.time()
            th = None 

            try:
                video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ogv']
                audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.aiff', '.ac3']
                file_ext = os.path.splitext(f)[1].lower() if f else ""

                if m.video or (m.document and file_ext in video_extensions):
                    mtd = await video_metadata(f) # func.py থেকে ইম্পোর্ট করা
                    dur, h, w = mtd['duration'], mtd['height'], mtd['width']
                    th = await get_thumbnail(user_data, f, dur, d)
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
                    th = user_data.get('thumb') if user_data.get('thumb') and os.path.exists(user_data.get('thumb')) else None
                    await c.send_audio(tcid, audio=f, caption=ft, 
                                    thumb=th, progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.photo:
                    await c.send_photo(tcid, photo=f, caption=ft, 
                                    progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.document:
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


