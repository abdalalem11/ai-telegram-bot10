import asyncio
import logging
import os
from datetime import datetime

from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

user_sessions = {}
pending_auth = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 بوت استخراج جلسات تيليثون\n\n/help - عرض المساعدة")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 الأوامر:\n"
        "/gen <api_id> <api_hash> - استخراج جلسة\n"
        "/info - عرض معلومات الجلسة\n"
        "/revoke - إلغاء الجلسة"
    )

async def generate_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        api_id = int(context.args[0])
        api_hash = context.args[1]
    except:
        await update.message.reply_text("❌ استخدم: /gen 123456 abcdef123456")
        return
    
    pending_auth[user_id] = {'api_id': api_id, 'api_hash': api_hash, 'step': 'phone'}
    await update.message.reply_text("📱 أرسل رقم هاتفك (مثال: +966501234567)")

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in pending_auth or pending_auth[user_id]['step'] != 'phone':
        return
    
    phone = update.message.text.strip()
    client = TelegramClient(StringSession(), pending_auth[user_id]['api_id'], pending_auth[user_id]['api_hash'])
    
    try:
        await client.connect()
        await client.send_code_request(phone)
        pending_auth[user_id]['client'] = client
        pending_auth[user_id]['phone'] = phone
        pending_auth[user_id]['step'] = 'code'
        await update.message.reply_text("📨 تم إرسال الرمز! أرسله الآن (مثال: 12345)")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")
        del pending_auth[user_id]

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in pending_auth or pending_auth[user_id]['step'] != 'code':
        return
    
    code = update.message.text.strip()
    client = pending_auth[user_id]['client']
    
    try:
        await client.sign_in(pending_auth[user_id]['phone'], code)
        session_string = client.session.save()
        user_sessions[user_id] = {'session': session_string, 'phone': pending_auth[user_id]['phone']}
        await update.message.reply_text(f"✅ الجلسة:\n`{session_string}`")
        await client.disconnect()
        del pending_auth[user_id]
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

async def info_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        await update.message.reply_text("❌ لا توجد جلسة!")
        return
    await update.message.reply_text(f"📱 الهاتف: {user_sessions[user_id]['phone']}")

async def revoke_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("✅ تم الإلغاء!")
    else:
        await update.message.reply_text("❌ لا توجد جلسة!")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ أمر غير معروف! استخدم /help")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN غير موجود!")
        return
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("gen", generate_session))
    app.add_handler(CommandHandler("info", info_session))
    app.add_handler(CommandHandler("revoke", revoke_session))
    app.add_handler(MessageHandler(filters.Regex(r'^\+?\d+$'), handle_phone))
    app.add_handler(MessageHandler(filters.Regex(r'^\d+$'), handle_code))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 10000)),
            url_path="/telegram",
            webhook_url=f"{webhook_url}/telegram"
        )
    else:
        asyncio.run(app.run_polling())

if __name__ == "__main__":
    main()
