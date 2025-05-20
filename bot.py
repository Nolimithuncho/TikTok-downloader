import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import requests

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Rate limiting storage
user_requests = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a TikTok link and I'll fetch it without the watermark!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📺 TikTok Downloader Bot Help:

1. Send any TikTok video link
2. I'll return it without watermark

Example links:
https://tiktok.com/@user/video/123456789
https://www.tiktok.com/t/abcdefghijk/
"""
    await update.message.reply_text(help_text)

def fetch_tiktok_video(url):
    try:
        api_url = "https://tikwm.com/api/?url=" + url
        response = requests.get(api_url).json()
        if response.get("code") == 0:
            return response["data"]["play"]
        return None
    except Exception as e:
        print(f"Error fetching TikTok: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    
    # Rate limiting
    if user_id in user_requests:
        if len([t for t in user_requests[user_id] if now - t < timedelta(minutes=1)]) >= 5:
            await update.message.reply_text("🚫 Too many requests! Please wait a minute.")
            return
    
    user_requests.setdefault(user_id, []).append(now)
    user_requests[user_id] = [t for t in user_requests[user_id] if now - t < timedelta(hours=1)]
    
    url = update.message.text.strip()
    if not url.startswith(("https://www.tiktok.com", "https://tiktok.com", "https://vt.tiktok.com")):
        await update.message.reply_text("⚠️ Please send a valid TikTok URL starting with https://tiktok.com")
        return

    try:
        await update.message.reply_text("⏳ Downloading your video...")
        video_url = fetch_tiktok_video(url)
        
        if video_url:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_url,
                caption="✅ Here's your TikTok without watermark!"
            )
        else:
            await update.message.reply_text("❌ Failed to download video. The link may be invalid or private.")
            
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
app.run_polling()
