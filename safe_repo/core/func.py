#safe_repo


import math
import time , re
from pyrogram import enums
from config import CHANNEL_ID, OWNER_ID 
from safe_repo.core import script
#from safe_repo.core.mongo.plans_db import premium_users
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import cv2
from pyrogram.errors import FloodWait, InviteHashInvalid, InviteHashExpired, UserAlreadyParticipant, UserNotParticipant
from datetime import datetime as dt
import asyncio, subprocess, re, os, time

# devgaganin থেকে যোগ করা নতুন ইম্পোর্ট
import concurrent.futures
import logging
try:
    from safe_repo.core.mongo import db
except ImportError:
    print("Warning: Could not import 'db' from 'safe_repo.core.mongo'. Rename function might fail.")
    db = None # একটি ফলব্যাক সেট করা হয়েছে

# devgaganin এর settings.py থেকে যোগ করা হয়েছে
VIDEO_EXTENSIONS = {
    'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm',
    'mpeg', 'mpg', '3gp'
}


async def chk_user(message, user_id):
    return 0
    #user = await premium_users()
    #if user_id in user or user_id in OWNER_ID:
        #return 0
    #else:
        #await message.reply_text("Purchase premium to do the tasks...")
        #return 1



async def gen_link(app,chat_id):
   link = await app.export_chat_invite_link(chat_id)
   return link

async def subscribe(app, message):
   update_channel = CHANNEL_ID
   url = await gen_link(app, update_channel)
   if update_channel:
      try:
         user = await app.get_chat_member(update_channel, message.from_user.id)
         if user.status == "kicked":
            await message.reply_text("You are Banned. Contact -- @safe_repo")
            return 1
      except UserNotParticipant:
         await message.reply_photo(photo="https://graph.org/file/d44f024a08ded19452152.jpg",caption=script.FORCE_MSG.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Now...", url=f"{url}")]]))
         return 1
      except Exception:
         await message.reply_text("Something Went Wrong. Contact us @safe_repo...")
         return 1



async def get_seconds(time_string):
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

    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0




PROGRESS_BAR = """\n
**__Completed__** : {1}/{2}
**__Bytes__** : {0}%
**__Speed__** : {3}/s
**__Time__** : {4}
"""


async def progress_bar(current, total, ud_type, message, start):

    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["🟢" for i in range(math.floor(percentage / 10))]),
            ''.join(["🔴" for i in range(10 - math.floor(percentage / 10))]))
            
        tmp = progress + PROGRESS_BAR.format( 
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n\n{}".format(ud_type, tmp),)             
                
        except:
            pass

def humanbytes(size):
    if not size:
        return ""
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


# এই ফাংশনটি safe_repo/core/func.py ফাইলে যোগ করুন
def thumbnail(sender):
    return f'{sender}.jpg' if os.path.exists(f'{sender}.jpg') else None
    
def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60      
    return "%d:%02d:%02d" % (hour, minutes, seconds)




async def userbot_join(userbot, invite_link):
    try:
        await userbot.join_chat(invite_link)
        return "Successfully joined the Channel"
    except UserAlreadyParticipant:
        return "User is already a participant."
    except (InviteHashInvalid, InviteHashExpired):
        return "Could not join. Maybe your link is expired or Invalid."
    except FloodWait:
        return "Too many requests, try again later."
    except Exception as e:
        print(e)
        return "Could not join, try joining manually."
    


def get_link(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)   
    try:
        link = [x[0] for x in url][0]
        if link:
            return link
        else:
            return False
    except Exception:
        return False

# -----------------------------------------------------------------
# নিচের ফাংশনগুলো devgaganin এর প্রজেক্ট থেকে যোগ করা বা প্রতিস্থাপন করা হয়েছে
# -----------------------------------------------------------------

def hhmmss(seconds):
    return time.strftime('%H:%M:%S',time.gmtime(seconds))

# devgaganin/utils/func.py থেকে প্রতিস্থাপিত (Replaced)
async def screenshot(video: str, duration: int, sender: str) -> str | None:
    existing_screenshot = f"{sender}.jpg"
    if os.path.exists(existing_screenshot):
        return existing_screenshot

    time_stamp = hhmmss(duration // 2)
    output_file = dt.now().isoformat("_", "seconds") + ".jpg"

    cmd = [
        "ffmpeg",
        "-ss", time_stamp,
        "-i", video,
        "-frames:v", "1",
        output_file,
        "-y"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()

    if os.path.isfile(output_file):
        return output_file
    else:
        print(f"FFmpeg Error: {stderr.decode().strip()}")
        return None

# devgaganin/utils/func.py থেকে প্রতিস্থাপিত (Replaced)
async def get_video_metadata(file_path):
    default_values = {'width': 1, 'height': 1, 'duration': 1}
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    
    try:
        def _extract_metadata():
            try:
                vcap = cv2.VideoCapture(file_path)
                if not vcap.isOpened():
                    return default_values

                width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = vcap.get(cv2.CAP_PROP_FPS)
                frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)

                if fps <= 0:
                    return default_values

                duration = round(frame_count / fps)
                if duration <= 0:
                    return default_values

                vcap.release()
                return {'width': width, 'height': height, 'duration': duration}
            except Exception as e:
                logging.error(f"Error in video_metadata: {e}")
                return default_values
        
        return await loop.run_in_executor(executor, _extract_metadata)
        
    except Exception as e:
        logging.error(f"Error in get_video_metadata: {e}")
        return default_values

# devgaganin/utils/func.py থেকে যোগ করা হয়েছে (Added)
def E(L):   
    private_match = re.match(r'https://t\.me/c/(\d+)/(?:\d+/)?(\d+)', L)
    public_match = re.match(r'https://t\.me/([^/]+)/(?:\d+/)?(\d+)', L)
    
    if private_match:
        return f'-100{private_match.group(1)}', int(private_match.group(2)), 'private'
    elif public_match:
        return public_match.group(1), int(public_match.group(2)), 'public'
    
    return None, None, None

# devgaganin/plugins/settings.py থেকে যোগ করা হয়েছে এবং আপনার ডেটাবেস অনুযায়ী পরিবর্তন করা হয়েছে (Added and Modified)
async def rename_file(file, sender, edit): # 'sender' হলো user_id
    try:
        # আপনার প্রজেক্টের (tawhid120) ডেটাবেস লজিক ব্যবহার করা হয়েছে
        if db:
            user_data = await db.get_data(sender)
        else:
            user_data = None
            
        if user_data:
            delete_words = user_data.get('delete_words', [])
            custom_rename_tag = user_data.get('rename_tag', '')
            replacements = user_data.get('replacement_words', {})
        else:
            delete_words = []
            custom_rename_tag = ''
            replacements = {}
        
        last_dot_index = str(file).rfind('.')
        if last_dot_index != -1 and last_dot_index != 0:
            ggn_ext = str(file)[last_dot_index + 1:]
            if ggn_ext.isalpha() and len(ggn_ext) <= 9:
                if ggn_ext.lower() in VIDEO_EXTENSIONS:
                    original_file_name = str(file)[:last_dot_index]
                    file_extension = 'mp4' # devgaganin ডিফল্ট mp4 ব্যবহার করে
                else:
                    original_file_name = str(file)[:last_dot_index]
                    file_extension = ggn_ext
            else:
                original_file_name = str(file)[:last_dot_index]
                file_extension = 'mp4' # devgaganin ডিফল্ট mp4 ব্যবহার করে
        else:
            original_file_name = str(file)
            file_extension = 'mp4' # devgaganin ডিফল্ট mp4 ব্যবহার করে
        
        for word in delete_words:
            original_file_name = original_file_name.replace(word, '')
        
        for word, replace_word in replacements.items():
            original_file_name = original_file_name.replace(word, replace_word)
        
        # ফাইল নামের খালি স্থান ঠিক করা
        original_file_name = ' '.join(original_file_name.split())
        
        new_file_name = f'{original_file_name} {custom_rename_tag}.{file_extension}'
        
        os.rename(file, new_file_name)
        return new_file_name
    except Exception as e:
        print(f"Rename error: {e}")
        return file

