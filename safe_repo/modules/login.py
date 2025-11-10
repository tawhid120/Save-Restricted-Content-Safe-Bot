#safe_repo

from pyrogram import filters, Client
from safe_repo import app, USER_CLIENTS # <--- USER_CLIENTS এখানে ইম্পোর্ট করা হয়েছে
import random
import os
import string
from safe_repo.core.mongo import db
from safe_repo.core.func import subscribe, chk_user
from config import API_ID as api_id, API_HASH as api_hash
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait
)
from asyncio.exceptions import TimeoutError # <--- TimeoutError ইম্পোর্ট করা হয়েছে

def generate_random_name(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))  # Editted ... 

async def delete_session_files(user_id):
    session_file = f"session_{user_id}.session"
    memory_file = f"session_{user_id}.session-journal"

    session_file_exists = os.path.exists(session_file)
    memory_file_exists = os.path.exists(memory_file)

    if session_file_exists:
        os.remove(session_file)
    
    if memory_file_exists:
        os.remove(memory_file)

    # Delete session from the database
    if session_file_exists or memory_file_exists:
        await db.delete_session(user_id)
        return True  # Files were deleted
    return False  # No files found

@app.on_message(filters.command("logout"))
async def clear_db(client, message):
    user_id = message.chat.id
    
    # --- সেশন ক্যাশ সমাধান ---
    # লগআউট করার সময় অ্যাক্টিভ সেশনটি বন্ধ করুন এবং ক্যাশ থেকে ডিলিট করুন
    if user_id in USER_CLIENTS:
        try:
            await USER_CLIENTS[user_id].stop()
            print(f"Stopped active session for user {user_id}")
        except Exception as e:
            print(f"Error stopping client on logout: {e}")
        del USER_CLIENTS[user_id]
    # --- সমাধান শেষ ---

    files_deleted = await delete_session_files(user_id)
    
    await db.delete_user(user_id)
    await message.reply('Successfully Logout!')


@app.on_message(filters.command("login"))
async def generate_session(client, message):
    
    lol = await chk_user(message, message.chat.id)
    if lol == 1:
        return
        
    join = await subscribe(client, message)
    if join == 1:
        return

    user_id = message.chat.id
    
    # সেশন ফাইল ডিলিট করুন (যদি থাকে)
    await delete_session_files(user_id)

    # একটি নতুন ক্লায়েন্ট তৈরি করুন (শুধু লগইন প্রসেসের জন্য)
    # Pyrogram সেশন নামটি 랜덤 হওয়া ভালো
    session_name = generate_random_name()
    try:
        client = Client(session_name, api_id=api_id, api_hash=api_hash, in_memory=True)
    except Exception as e:
        await message.reply(f"Error starting client: {e}")
        return

    try:
        await client.connect()
        phone_number_msg = await app.ask(user_id, "Please send your phone number with country code (e.g., +19876543210):", filters=filters.text, timeout=600)
        phone_number = phone_number_msg.text
        
        try:
            code = await client.send_code(phone_number)
        except FloodWait as fw:
            await message.reply(f"Flood wait: Please wait {fw.value} seconds before trying again.")
            return
        except (ApiIdInvalid, PhoneNumberInvalid) as e:
            await message.reply(f"Error: {e}. Please check your input and try again.")
            return

        try:
            otp_code = await app.ask(user_id, "We have sent an OTP to your official Telegram account. Once received, enter the OTP in the following format: \nIf the OTP is `12345`, please enter it as `1 2 3 4 5`.", filters=filters.text, timeout=600)
        except TimeoutError:
            await message.reply('⏰ Time limit of 10 minutes exceeded. Please restart the session.')
            return
        
        phone_code = otp_code.text.replace(" ", "")
        
        try:
            await client.sign_in(phone_number, code.phone_code_hash, phone_code)
                    
        except PhoneCodeInvalid:
            await message.reply('❌ Invalid OTP. Please restart the session.')
            return
        except PhoneCodeExpired:
            await message.reply('❌ Expired OTP. Please restart the session.')
            return
        except SessionPasswordNeeded:
            try:
                two_step_msg = await app.ask(user_id, 'Your account has two-step verification enabled. Please enter your password.', filters=filters.text, timeout=300)
            except TimeoutError:
                await message.reply('⏰ Time limit of 5 minutes exceeded. Please restart the session.')
                return
            try:
                password = two_step_msg.text
                await client.check_password(password=password)
            except PasswordHashInvalid:
                await two_step_msg.reply('❌ Invalid password. Please restart the session.')
                return

        # --- সেশন ক্যাশ সমাধান ---
        # সেশনটি চালু রাখুন এবং ক্যাশে সেভ করুন
        
        string_session = await client.export_session_string()
        await db.set_session(user_id, string_session)
        
        # যদি এই ইউজার আগে লগইন করে থাকে, তার পুরনো সেশন বন্ধ করুন
        if user_id in USER_CLIENTS:
            try:
                await USER_CLIENTS[user_id].stop()
            except Exception:
                pass
                
        USER_CLIENTS[user_id] = client  # নতুন অ্যাক্টিভ সেশনটি ক্যাশে সেভ করুন
        # await client.disconnect() <-- সেশন চালু রাখার জন্য এই লাইনটি ডিলিট করা হয়েছে
        
        await otp_code.reply("✅ Login successful! Your session is now active.")
        # --- সমাধান শেষ ---

    except TimeoutError:
        await message.reply('⏰ Time limit of 10 minutes exceeded. Please restart the session.')
    except Exception as e:
        await message.reply(f'An error occurred: {e}')
        # যদি কোনো এরর হয়, তাহলে ক্লায়েন্ট ডিসকানেক্ট করুন
        if client.is_connected:
            await client.disconnect()
