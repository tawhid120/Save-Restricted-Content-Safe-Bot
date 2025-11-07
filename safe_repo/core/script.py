#safe_repo

# ------------------------------------------------------------ #

START_TXT = """
👋 **Welcome to Advanced Content Saver Bot v3.0!**

🤖 **Your Ultimate Message Saver**

I'm designed to help you save and download content from:
• Public & Private Channels
• Private Groups
• Bot Messages

📋 **Quick Start Guide:**
1️⃣ Login using `/login` command
2️⃣ Send any Telegram message link
3️⃣ Get your content saved instantly!

⚡ **Key Features:**
• Save single messages
• Batch download (up to 100 posts)
• Custom captions & thumbnails
• Session management
• Premium features available

💡 **Tip:** Use `/help` to explore all commands

✨ **Ready to start saving content?**
"""

FORCE_MSG = """
👋 **Hey {}!**

⚠️ **Access Restricted**

According to my database, you haven't joined our updates channel yet.

📢 **To use this bot, you need to:**
1️⃣ Join the updates channel
2️⃣ Click on "Try Again" or restart the bot

🔗 **Why join?**
• Get latest updates & features
• Stay informed about maintenance
• Access exclusive content

**Thank you for your cooperation!** ✨
"""

HELP_TXT = """
📚 **Help & Commands Guide**

🔐 **Authentication:**
• `/login` - Login with your account session
• `/logout` - Remove your active session

⚙️ **Configuration:**
• `/settings` - Configure bot preferences
  ├─ Custom captions
  ├─ Custom thumbnails
  ├─ Session management
  └─ Channel settings

📥 **Download Commands:**
• Send message link - Save single message
• `/batch` - Bulk download guide
• `/cancel` - Stop ongoing batch process

👤 **Account:**
• `/myplan` - Check premium status
• `/stats` - View your usage statistics

❓ **Need More Help?**
Use `/help2` for detailed examples and FAQ

💬 **Support:** @safe_repo
"""

HELP2_TXT = """
🕵️ **Detailed Help & Examples**

📌 **FOR PUBLIC/PRIVATE CHANNELS:**

**Step-by-step:**
1️⃣ Login using `/login`
2️⃣ Join the target channel in your logged account
3️⃣ Send the message link to this bot

**Format:** `https://t.me/channel_username/message_id`
**Example:** `https://t.me/example/12345`

---

🤖 **FOR BOT MESSAGES:**

**Format:** `https://t.me/b/bot_username/message_id`

**Note:** Use **Plus Messenger** to get the correct message_id

---

💬 **FOR GROUP TOPICS:**

**Private Groups:**
• Original: `https://t.me/c/xxxxxxxxx/first_id/second_id`
• Send as: `https://t.me/c/xxxxxxxxx/second_id`
• ⚠️ Remove the first ID and one `/`

**Public Groups:**
• Remove `/c` from the link
• Format: `https://t.me/username/second_id`

---

📦 **BATCH DOWNLOAD:**

**Format:** `https://t.me/channel/START_ID-END_ID`
**Examples:**
• `https://t.me/example/100-110` (11 messages)
• `https://t.me/example/1-100` (100 messages)

**Limits:**
• Maximum: 100 messages per batch
• Spaces allowed: `100 - 110`

---

❓ **FAQ - Troubleshooting:**

**Q:** Bot says "Have you joined the channel?"
**A:** Re-login using `/login` and try again

**Q:** Batch download is stuck?
**A:** Use `/cancel` command to stop

**Q:** Getting "No session" error?
**A:** Login first using `/login`

**Q:** Can't access private channel?
**A:** Make sure you've joined that channel in your logged account

---

💡 **Pro Tips:**
• Login before downloading for faster speeds
• Use batch for multiple messages
• Set custom caption in `/settings`

🆘 **Still need help?** Contact @safe_repo
"""

ADMIN_TXT = """
🛠️ **Admin Control Panel**

👥 **User Management:**
• `/add <user_id>` - Grant premium access
• `/rem <user_id>` - Revoke premium access
• `/check <user_id>` - Verify premium status

📢 **Broadcast:**
• `/broadcast <message>` - Send without forward tag
• `/announce <message>` - Send with forward tag

📊 **Statistics:**
• `/stats` - View complete bot statistics
  ├─ Total users
  ├─ Premium users
  ├─ Active sessions
  └─ Usage metrics

🔧 **Maintenance:**
• `/maintenance on/off` - Toggle maintenance mode
• `/logs` - View recent error logs

⚡ **Quick Actions:**
• `/ban <user_id>` - Ban a user
• `/unban <user_id>` - Unban a user

**Admin rights required for all commands** 🔐
"""

SETTINGS_TXT = """
⚙️ **Settings & Customization**

Welcome to your personalization hub! Configure the bot according to your preferences.

🎯 **Available Options:**

📝 **Caption Settings**
• Set custom caption format
• Add watermarks
• Configure file naming

🖼️ **Thumbnail Settings**
• Upload custom thumbnail
• Set default thumbnail
• Remove thumbnail

🔐 **Session Management**
• Active session status
• Login/Logout
• Session security

📢 **Channel Settings**
• Configure source channels
• Set destination preferences

---

💡 **How to use:**
Simply click on the buttons below to configure each setting

⚠️ **Note:** Some features are available for premium users only

🌟 **Upgrade to Premium** for unlimited access!
"""

CAPTIONS_TXT = """
📝 **Caption Customization**

Personalize how your saved content appears!

🎨 **Caption Options:**

**1️⃣ Set Custom Caption:**
• Add your own text to every file
• Use variables: `{filename}`, `{size}`, `{duration}`

**2️⃣ Caption Template:**
"""
