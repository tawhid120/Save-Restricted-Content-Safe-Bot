# safe_repo/core/get_func.py

import os
import re
import time
import asyncio
from typing import Optional
from pyrogram import Client
from pyrogram.errors import UserNotParticipant
from config import LOG_GROUP, API_ID, API_HASH
from safe_repo.core.mongo import db

# Import helper functions from func.py
from safe_repo.core.func import (
    rename_file,
    get_video_metadata as video_metadata,
    screenshot,
    hhmmss,
    humanbytes,
    TimeFormatter,
    process_text_with_rules,
    get_thumbnail_for_video
)

# Global variables
P = {}
emp = {}

def sanitize(filename: str) -> str:
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*\']', '_', filename).strip(" .")[:255]


async def upd_dlg(c) -> bool:
    """Update userbot's dialog list"""
    try:
        async for _ in c.get_dialogs(limit=100):
            pass
        return True
    except Exception as e:
        print(f'Failed to update dialogs: {e}')
        return False


async def get_msg(c, u, i: str, d: int, lt: str):
    """
    Fetch message from Telegram.
    c = bot client
    u = userbot client
    i = chat_id or username
    d = message_id
    lt = link_type ('public' or 'private')
    """
    try:
        if lt == 'public':
            # For public channels/groups
            try:
                # Check if it's a bot
                if str(i).lower().endswith('bot'):
                    emp[i] = False
                    xm = await u.get_messages(i, d)
                    emp[i] = getattr(xm, "empty", False)
                    if not emp[i]:
                        emp[i] = True
                        print(f"Bot chat found successfully...")
                        return xm
                
                # Try with bot first
                if emp.get(i, True):
                    xm = await c.get_messages(i, d)
                    print(f"Fetched by {c.me.username}")
                    emp[i] = getattr(xm, "empty", False)
                    if emp[i]:
                        print(f"Not fetched by {c.me.username}, trying userbot...")
                        try:
                            await u.join_chat(i)
                        except:
                            pass
                        xm = await u.get_messages((await u.get_chat(f"@{i}")).id, d)
                    
                    return xm
            except Exception as e:
                print(f'Error fetching public message: {e}')
                return None
                
        else:  # private
            if not u:
                return None
                
            try:
                async for _ in u.get_dialogs(limit=50):
                    pass
                
                # Handle different ID formats
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
                
                # Try - format
                try:
                    result = await u.get_messages(chat_id_dash, d)
                    if result and not getattr(result, "empty", False):
                        return result
                except Exception:
                    pass
                
                # Final fallback
                try:
                    async for _ in u.get_dialogs(limit=200):
                        pass
                    result = await u.get_messages(int(i), d)
                    if result and not getattr(result, "empty", False):
                        return result
                except Exception:
                    pass
                
                return None
                        
            except Exception as e:
                print(f'Private channel error: {e}')
                return None
                
    except Exception as e:
        print(f'Error fetching message: {e}')
        return None


async def prog(c, t, C, h, m, st):
    """Progress bar for download/upload"""
    global P
    if t == 0:
        return 
    
    p = c / t * 100
    interval = 10 if t >= 100 * 1024 * 1024 else 20 if t >= 50 * 1024 * 1024 else 30 if t >= 10 * 1024 * 1024 else 50
    step = int(p // interval) * interval
    
    if m not in P or P[m] != step or p >= 100:
        P[m] = step
        c_mb = c / (1024 * 1024)
        t_mb = t / (1024 * 1024)
        bar = '🟢' * int(p / 10) + '🔴' * (10 - int(p / 10))
        
        diff = time.time() - st
        if diff == 0:
            diff = 0.001 
            
        speed = c / diff / (1024 * 1024)
        eta = time.strftime('%M:%S', time.gmtime((t - c) / (speed * 1024 * 1024))) if speed > 0 else '00:00'
        
        try:
            await C.edit_message_text(h, m, f"__**Processing...**__\n\n{bar}\n\n⚡**Completed**: {c_mb:.2f} MB / {t_mb:.2f} MB\n📊 **Done**: {p:.2f}%\n🚀 **Speed**: {speed:.2f} MB/s\n⏳ **ETA**: {eta}\n\n**__Powered by @tawhid120__**")
        except:
            pass
            
        if p >= 100:
            P.pop(m, None)


async def send_direct(c, m, tcid, ft=None, rtmid=None):
    """Send media directly by file_id"""
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


async def process_msg(c, u, m, d, lt, uid, i):
    """
    Main message processing function.
    c = bot client
    u = userbot client
    m = message object
    d = destination user_id (as string)
    lt = link_type
    uid = user_id (as int)
    i = source chat_id
    """
    try:
        # Get user settings from database
        user_data = await db.get_data(int(d))
        if not user_data:
            user_data = {}
        
        # Determine target chat
        cfg_chat = user_data.get('chat_id', None)
        tcid = int(d)
        rtmid = None
        
        if cfg_chat:
            if '/' in cfg_chat:
                parts = cfg_chat.split('/', 1)
                tcid = int(parts[0])
                rtmid = int(parts[1]) if len(parts) > 1 else None
            else:
                tcid = int(cfg_chat)
        
        # Process media messages
        if m.media:
            # Process caption
            orig_text = m.caption.markdown if m.caption else ''
            proc_text = await process_text_with_rules(user_data, orig_text)
            user_cap = user_data.get('caption', '')
            ft = f'{proc_text}\n\n{user_cap}' if proc_text and user_cap else user_cap if user_cap else proc_text
            
            # Try direct send for public messages
            if lt == 'public' and not emp.get(i, False):
                if await send_direct(c, m, tcid, ft, rtmid):
                    return 'Sent directly.'
            
            # Download and upload
            st = time.time()
            p = await c.send_message(d, 'Downloading...')

            # Generate filename
            c_name = f"{time.time()}"
            file_name = None

            if m.video:
                file_name = m.video.file_name
            elif m.audio:
                file_name = m.audio.file_name
            elif m.document:
                file_name = m.document.file_name
            
            if file_name:
                c_name = sanitize(file_name)
            else:
                ext = ".mp4" if m.video else ".mp3" if m.audio else ".jpg" if m.photo else ""
                c_name = sanitize(f"{time.time()}{ext}")

            # Download file
            f = await u.download_media(m, file_name=c_name, progress=prog, progress_args=(c, int(d), p.id, st))
            
            if not f:
                await c.edit_message_text(d, p.id, 'Failed to download.')
                return 'Failed.'
            
            # Rename file
            await c.edit_message_text(d, p.id, 'Renaming...')
            if file_name:
                f = await rename_file(f, int(d), p)
            
            # Check file size
            fsize_bytes = os.path.getsize(f)
            fsize_gb = fsize_bytes / (1024 * 1024 * 1024)
            
            # Handle large files (>2GB) - placeholder, needs userbot Y
            if fsize_gb > 2:
                await c.edit_message_text(d, p.id, 'File larger than 2GB. This feature needs premium userbot setup.')
                if os.path.exists(f):
                    os.remove(f)
                return 'Failed (File too large).'
            
            # Upload file
            await c.edit_message_text(d, p.id, 'Uploading...')
            st = time.time()
            th = None

            try:
                video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ogv']
                audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.aiff', '.ac3']
                file_ext = os.path.splitext(f)[1].lower() if f else ""

                if m.video or (m.document and file_ext in video_extensions):
                    mtd = await video_metadata(f)
                    dur, h, w = mtd['duration'], mtd['height'], mtd['width']
                    th = await get_thumbnail_for_video(user_data, f, dur, int(d))
                    await c.send_video(tcid, video=f, caption=ft, 
                                    thumb=th, width=w, height=h, duration=dur, 
                                    progress=prog, progress_args=(c, int(d), p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.video_note:
                    await c.send_video_note(tcid, video_note=f, progress=prog, 
                                        progress_args=(c, int(d), p.id, st), reply_to_message_id=rtmid)
                elif m.voice:
                    await c.send_voice(tcid, f, progress=prog, progress_args=(c, int(d), p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.sticker:
                    await c.send_sticker(tcid, m.sticker.file_id, reply_to_message_id=rtmid)
                elif m.audio or (m.document and file_ext in audio_extensions):
                    th = user_data.get('thumb') if user_data.get('thumb') and os.path.exists(user_data.get('thumb')) else None
                    await c.send_audio(tcid, audio=f, caption=ft, 
                                    thumb=th, progress=prog, progress_args=(c, int(d), p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.photo:
                    await c.send_photo(tcid, photo=f, caption=ft, 
                                    progress=prog, progress_args=(c, int(d), p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.document:
                    th = user_data.get('thumb') if user_data.get('thumb') and os.path.exists(user_data.get('thumb')) else None
                    await c.send_document(tcid, document=f, caption=ft, thumb=th,
                                        progress=prog, progress_args=(c, int(d), p.id, st), 
                                        reply_to_message_id=rtmid)
                else:
                    await c.send_document(tcid, document=f, caption=ft,
                                        progress=prog, progress_args=(c, int(d), p.id, st), 
                                        reply_to_message_id=rtmid)
            except Exception as e:
                await c.edit_message_text(d, p.id, f'Upload failed: {str(e)[:30]}')
                if os.path.exists(f):
                    os.remove(f)
                if th and os.path.exists(th) and th != user_data.get('thumb'):
                    os.remove(th)
                return 'Failed.'
            
            # Cleanup
            if os.path.exists(f):
                os.remove(f)
            if th and os.path.exists(th) and th != user_data.get('thumb'):
                os.remove(th)
            await c.delete_messages(d, p.id)
            
            return 'Done.'
            
        elif m.text:
            # Send text messages
            await c.send_message(tcid, text=m.text.markdown, reply_to_message_id=rtmid)
            return 'Sent.'
            
    except Exception as e:
        print(f"Process_msg Error: {e}")
        return f'Error: {str(e)[:50]}'
