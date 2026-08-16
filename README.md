









📦 What This Telegram Bot Can Do
Your bot acts like a personal media vault for storing and retrieving videos or photos using sharable Telegram links.

✅ Key Features
1. Store Media to a Private Channel
When the bot owner (you) sends a photo or video to the bot:

It copies the media to a storage channel (a private Telegram channel you own).

It saves the message ID and a unique ID in an SQLite database.

It creates a custom sharable link (like https://t.me/YourBot?start=abc123).

2. Generate and Share Links
After uploading media, the bot replies with:

less
Copy
Edit
🎬 Your requested video:

🎥 video abc123

🔗 LINK: https://t.me/YourBot?start=XYZ
You can share this link with anyone. When they click it, the bot will send the video/photo to them.

3. Auto-delete After 20 Minutes
When someone receives media from the bot:

The file is automatically deleted from their chat after 20 minutes.

This helps keep things temporary and private.

🔒 Private and Owner-Only Uploading
Only the owner (your Telegram user ID) can upload files to the bot.

Other users can only receive files via /start links.

🧠 How It Works Behind the Scenes
Component	Role
.env file	Stores bot token, owner ID, and channel ID (for security).
sqlite3 database	Keeps a list of uploaded media (file type, unique ID, etc.).
copy_message()	Telegram API method to duplicate media from sender to channel.
base64 encoding	Makes the links compact and safe to include in the Telegram start command.
asyncio	Used to delay and delete the message after 20 minutes.

🧪 Example Use Case
You (the owner) send a video to the bot. It replies:

less
Copy
Edit
🎬 Your requested video:

🎥 video a1b2c3d4



