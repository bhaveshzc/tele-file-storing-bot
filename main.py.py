import os
import logging
import sqlite3
import uuid
import base64
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID"))

if not BOT_TOKEN or not OWNER_ID or not STORAGE_CHANNEL_ID:
    raise ValueError("❌ BOT_TOKEN, OWNER_ID or STORAGE_CHANNEL_ID is missing in the .env file!")

# Database setup
conn = sqlite3.connect("mediadatabase.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        file_type TEXT,
        unique_id TEXT UNIQUE,
        message_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Telegram bot setup
telegram_app = Application.builder().token(BOT_TOKEN).build()

def encode_payload(payload: str) -> str:
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

def decode_payload(encoded: str) -> str:
    padding = len(encoded) % 4
    if padding:
        encoded += "=" * (4 - padding)
    return base64.urlsafe_b64decode(encoded).decode()

async def delete_media_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    await asyncio.sleep(1200)  # 20 minutes
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.error(f"❌ Failed to delete message: {e}")

async def send_media(update: Update, context: ContextTypes.DEFAULT_TYPE, unique_id: str):
    cursor.execute("SELECT file_type, message_id FROM media WHERE unique_id = ?", (unique_id,))
    media_entry = cursor.fetchone()

    if media_entry:
        file_type, message_id = media_entry

        try:
            sent_message = await context.bot.copy_message(
                chat_id=update.message.chat_id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=message_id,
                protect_content=True
            )

            await update.message.reply_text("⚠️ This file will be deleted in 20 minutes!")
            asyncio.create_task(delete_media_after_delay(context, update.message.chat_id, sent_message.message_id))

        except Exception as e:
            logging.error(f"❌ Failed to copy media: {e}")
            await update.message.reply_text("❌ This media has been deleted!")
            cursor.execute("DELETE FROM media WHERE unique_id = ?", (unique_id,))
            conn.commit()

    else:
        await update.message.reply_text("❌ Media not found!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text.strip()
    if message_text.startswith("/start ") and len(message_text) > 7:
        encoded_payload = message_text.split(" ", 1)[1]
        try:
            decoded_payload = decode_payload(encoded_payload)
            if decoded_payload.startswith("get-media-"):
                unique_id = decoded_payload.replace("get-media-", "")
                await send_media(update, context, unique_id)
        except Exception:
            await update.message.reply_text("❌ Invalid link format!")
    else:
        welcome_message = """🚀 Welcome to the Bot!


this bot provides the link to your media files which you can share to ur channel easily.

📌 Join now: [Click Here]"""
        await update.message.reply_text(welcome_message, parse_mode="Markdown", disable_web_page_preview=True)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != OWNER_ID:
        return

    file_type = None
    if update.message.photo:
        file_type = "photo"
    elif update.message.video:
        file_type = "video"

    if not file_type:
        await update.message.reply_text("❌ No valid media detected!")
        return

    try:
        copied_message = await context.bot.copy_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        message_id = copied_message.message_id
        unique_id = str(uuid.uuid4())[:8]

        cursor.execute(
            "INSERT OR IGNORE INTO media (file_id, file_type, unique_id, message_id) VALUES (?, ?, ?, ?)",
            (None, file_type, unique_id, message_id)
        )
        conn.commit()

        bot_user = await context.bot.get_me()
        encoded_link = encode_payload(f"get-media-{unique_id}")
        link = f"https://t.me/{bot_user.username}?start={encoded_link}"

        media_indicator = f"📸 pic {unique_id}" if file_type == "photo" else f"🎥 video {ideunique_id}"
        cooked_message = f"video:\n\n{media_indicator}\n\n🔗 LINK: {link}"

        await update.message.reply_text(cooked_message, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"❌ Error copying media: {e}")
        await update.message.reply_text("❌ Failed to process media!")

if __name__ == "__main__":
    telegram_app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/start"), start))
    telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

    logging.info("🤖 Bot is running...")
    telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)
