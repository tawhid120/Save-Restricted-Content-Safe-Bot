from pyrogram import filters, Client
from safe_repo import app
import os
import string
import random
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
    FloodWait,
    TimeoutError # TimeoutError import করা হয়েছে
)

# একটি গ্লোবাল ডিকশনারি যা সক্রিয় ইউজার ক্লায়েন্টদের ধরে রাখবে।
# ধরে নেওয়া হচ্ছে এটি আপনার 'safe_repo' মডিউল বা গ্লোবাল স্কোপে সংজ্ঞায়িত।
# যদি এটি অন্য ফাইল থেকে ইমপোর্ট হয়, তবে উপরের import সেকশনে যোগ করুন।
# আপাতত, এটি এখানে সংজ্ঞায়িত করা হলো:
USER_CLIENTS = {}


async def delete_session_files(user_id):
    """সেশন ফাইল এবং জার্নাল ফাইল ডিলিট করে এবং ডাটাবেস থেকে সেশন মুছে দেয়।"""
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
        
        # সক্রিয় ক্লায়েন্টকে বন্ধ করুন এবং USER_CLIENTS থেকে মুছে ফেলুন
        if user_id in USER_CLIENTS:
            try:
                await USER_CLIENTS[user_id].stop()
            except Exception:
                pass
            del USER_CLIENTS[user_id]
            
        return True # Files were deleted
    return False # No files found

@app.on_message(filters.command("logout"))
async def clear_db(client, message):
    user_id = message.chat.id
    files_deleted = await delete_session_files(user_id)

    if files_deleted:
        await message.reply("✅ আপনার সেশন ডেটা এবং ফাইলগুলি মেমরি এবং ডিস্ক থেকে সাফ করা হয়েছে। আপনি এখন লগ আউট করেছেন।")
    else:
        await message.reply("⚠️ আপনি লগ ইন করেননি, কোনো সেশন ডেটা পাওয়া যায়নি।")
        
@app.on_message(filters.command("login"))
async def generate_session(_, message):
    user_id = message.chat.id
    client = None # ক্লায়েন্ট অবজেক্টকে আগে থেকেই ইনিশিয়ালাইজ করা হলো

    # সাবস্ক্রিপশন চেক
    joined = await subscribe(_, message)
    if joined == 1:
        return
    
    # যদি ক্লায়েন্ট ইতিমধ্যেই সক্রিয় থাকে, তার পুরনো সেশন বন্ধ করুন (আপনার নতুন কোডের লজিক)
    if user_id in USER_CLIENTS:
        try:
            await USER_CLIENTS[user_id].stop()
        except Exception:
            pass
        del USER_CLIENTS[user_id]

    try:
        # ১. ফোন নম্বর ইনপুট
        number_msg = await _.ask(user_id, 'অনুগ্রহ করে আপনার কান্ট্রি কোড সহ ফোন নম্বরটি দিন। \nউদাহরণ: +19876543210', filters=filters.text, timeout=300)
        phone_number = number_msg.text.strip()

        await message.reply("📲 OTP পাঠানো হচ্ছে...")
        
        # ক্লায়েন্ট তৈরি করা
        client = Client(f"session_{user_id}", api_id, api_hash)
        
        # ২. OTP কোড পাঠানো
        try:
            # client.send_code() স্বয়ংক্রিয়ভাবে connect() করে নেয়
            code = await client.send_code(phone_number)
        except ApiIdInvalid:
            await message.reply('❌ API ID এবং API HASH এর ভুল কম্বিনেশন। অনুগ্রহ করে সেশনটি পুনরায় শুরু করুন।')
            await client.stop()
            return
        except PhoneNumberInvalid:
            await message.reply('❌ ভুল ফোন নম্বর। অনুগ্রহ করে সেশনটি পুনরায় শুরু করুন।')
            await client.stop()
            return
        except FloodWait as e:
            await message.reply(f'⚠️ ফ্লাড অপেক্ষা: অনুগ্রহ করে {e.value} সেকেন্ড পরে আবার চেষ্টা করুন।')
            await client.stop()
            return
        
        # ৩. OTP ইনপুট
        otp_msg = await _.ask(user_id, "অনুগ্রহ করে আপনার অফিসিয়াল টেলিগ্রাম অ্যাকাউন্টে আসা OTP টি চেক করুন। OTP পেলে, এটি নিম্নলিখিত ফরম্যাটে প্রবেশ করুন: \nযদি OTP `12345` হয়, তবে `1 2 3 4 5` হিসাবে প্রবেশ করুন।", filters=filters.text, timeout=600)
        
        phone_code = otp_msg.text.replace(" ", "")

        # ৪. সাইন ইন
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
            
    except TimeoutError:
        # ask() ফাংশন টাইম আউট হলে
        await message.reply('⏰ সময়সীমা (টাইম আউট) পেরিয়ে গেছে। অনুগ্রহ করে সেশনটি পুনরায় শুরু করুন।')
        if client:
            await client.stop()
        return
    except PhoneCodeInvalid:
        await message.reply('❌ ভুল OTP। অনুগ্রহ করে সেশনটি পুনরায় শুরু করুন।')
        if client:
            await client.stop()
        return
    except PhoneCodeExpired:
        await message.reply('❌ OTP এর মেয়াদ উত্তীর্ণ হয়েছে। অনুগ্রহ করে সেশনটি পুনরায় শুরু করুন।')
        if client:
            await client.stop()
        return
    except SessionPasswordNeeded:
        # ৫. দুই-ধাপ যাচাইকরণের জন্য পাসওয়ার্ড
        try:
            two_step_msg = await _.ask(user_id, 'আপনার অ্যাকাউন্টে দুই-ধাপ যাচাইকরণ (2FA) সক্ষম করা আছে। অনুগ্রহ করে আপনার পাসওয়ার্ড দিন।', filters=filters.text, timeout=300)
        except TimeoutError:
            await message.reply('⏰ সময়সীমা (টাইম আউট) পেরিয়ে গেছে। অনুগ্রহ করে সেশনটি পুনরায় শুরু করুন।')
            if client:
                await client.stop()
            return
        
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply('❌ ভুল পাসওয়ার্ড। অনুগ্রহ করে সেশনটি পুনরায় শুরু করুন।')
            if client:
                await client.stop()
            return
        except Exception as e:
            await message.reply(f"❌ পাসওয়ার্ড চেক করতে সমস্যা হয়েছে: {e}")
            if client:
                await client.stop()
            return
    except Exception as e:
        # অন্যান্য অপ্রত্যাশিত ত্রুটি
        await message.reply(f"❌ একটি অপ্রত্যাশিত ত্রুটি ঘটেছে: {e}")
        if client:
            await client.stop()
        return

    
    # --- সাফল্যের পর কাজগুলো ---
    try:
        # সেশন স্ট্রিং এক্সপোর্ট এবং ডাটাবেসে সেভ
        string_session = await client.export_session_string()
        await db.set_session(user_id, string_session)

        # ক্লায়েন্টটি বন্ধ না করে সক্রিয় ক্লায়েন্ট ক্যাশে যোগ করুন
        USER_CLIENTS[user_id] = client

        # সফল বার্তা
        await message.reply("✅ লগইন সফল! আপনার সেশন এখন সক্রিয় আছে।")

    except Exception as e:
        await message.reply(f"❌ সেশন সংরক্ষণ বা ক্লায়েন্ট সেটআপে সমস্যা: {e}")
        if client:
            await client.stop()
