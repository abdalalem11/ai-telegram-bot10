import asyncio
import logging
import os
import re
from datetime import datetime

from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# متغيرات التخزين المؤقت
user_sessions = {}
pending_auth = {}

# -------------------- الأوامر --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر البدء"""
    await update.message.reply_text(
        "🔥 **بوت استخراج جلسات تيليثون**\n\n"
        "📌 الأوامر المتاحة:\n"
        "/gen <api_id> <api_hash> - استخراج جلسة جديدة\n"
        "/info - عرض معلومات الجلسة الحالية\n"
        "/revoke - إلغاء الجلسة\n"
        "/help - عرض المساعدة"
    )

async def generate_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """استخراج جلسة جديدة"""
    user_id = update.effective_user.id
    
    try:
        api_id = int(context.args[0])
        api_hash = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ استخدام خاطئ!\n"
            "الصيغة: /gen <api_id> <api_hash>\n"
            "مثال: /gen 123456 abcdef123456"
        )
        return
    
    # طلب رقم الهاتف
    pending_auth[user_id] = {
        'api_id': api_id,
        'api_hash': api_hash,
        'step': 'phone'
    }
    
    await update.message.reply_text(
        "📱 **أرسل رقم هاتفك** (مع رمز الدولة)\n"
        "مثال: +966501234567"
    )

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة رقم الهاتف"""
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    
    if user_id not in pending_auth or pending_auth[user_id]['step'] != 'phone':
        return
    
    # إنشاء عميل تيليثون
    session_name = f"session_{user_id}_{int(datetime.now().timestamp())}"
    client = TelegramClient(
        StringSession(),
        pending_auth[user_id]['api_id'],
        pending_auth[user_id]['api_hash']
    )
    
    try:
        await client.connect()
        await client.send_code_request(phone)
        
        pending_auth[user_id]['client'] = client
        pending_auth[user_id]['phone'] = phone
        pending_auth[user_id]['step'] = 'code'
        
        await update.message.reply_text(
            "📨 **تم إرسال رمز التحقق!**\n"
            "أرسل الرمز الذي وصلتك (مثال: 12345)"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")
        del pending_auth[user_id]

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة رمز التحقق"""
    user_id = update.effective_user.id
    code = update.message.text.strip()
    
    if user_id not in pending_auth or pending_auth[user_id]['step'] != 'code':
        return
    
    client = pending_auth[user_id]['client']
    phone = pending_auth[user_id]['phone']
    
    try:
        await client.sign_in(phone, code)
        session_string = client.session.save()
        
        # حفظ الجلسة
        user_sessions[user_id] = {
            'session': session_string,
            'api_id': pending_auth[user_id]['api_id'],
            'api_hash': pending_auth[user_id]['api_hash'],
            'phone': phone,
            'created_at': datetime.now().isoformat()
        }
        
        # عرض الجلسة
        await update.message.reply_text(
            f"✅ **تم استخراج الجلسة بنجاح!**\n\n"
            f"📋 **الجلسة:**\n`{session_string}`\n\n"
            f"⚠️ **احتفظ بها في مكان آمن!**\n"
            f"📱 الهاتف: {phone}\n"
            f"🆔 API ID: {pending_auth[user_id]['api_id']}"
        )
        
        # تنظيف
        await client.disconnect()
        del pending_auth[user_id]
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في التحقق: {str(e)}")

async def info_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض معلومات الجلسة"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text("❌ لا توجد جلسة نشطة!")
        return
    
    data = user_sessions[user_id]
    await update.message.reply_text(
        f"📊 **معلومات الجلسة:**\n\n"
        f"📱 الهاتف: {data['phone']}\n"
        f"🆔 API ID: {data['api_id']}\n"
        f"📅 تاريخ الإنشاء: {data['created_at']}\n"
        f"🔑 الجلسة: `{data['session'][:30]}...`"
    )

async def revoke_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إلغاء الجلسة"""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text("❌ لا توجد جلسة لإلغائها!")
        return
    
    del user_sessions[user_id]
    await update.message.reply_text("✅ تم إلغاء الجلسة بنجاح!")

# -------------------- التشغيل --------------------

def main():
    """تشغيل البوت"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("لم يتم العثور على TELEGRAM_BOT_TOKEN!")
        return
    
    app = Application.builder().token(token).build()
    
    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_session))
    app.add_handler(CommandHandler("info", info_session))
    app.add_handler(CommandHandler("revoke", revoke_session))
    
    # معالجات الرسائل
    app.add_handler(MessageHandler(filters.Regex(r'^\+?\d+$'), handle_phone))
    app.add_handler(MessageHandler(filters.Regex(r'^\d+$'), handle_code))
    
    # تشغيل البوت
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 10000)),
            url_path="/telegram",
            webhook_url=webhook_url
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()            await update.message.reply_text(reply)
        else:
            # لاگ خطا
            print("⚠️ OpenRouter Error:")
            print("Status Code:", response.status_code)
            print("Response Text:", response.text[:500])  # لاگ حداکثر 500 کاراکتر
            await update.message.reply_text("⚠️ خطا از OpenRouter:\n" + response.text[:300])
    except Exception as e:
        print("‼️ استثناء در ارسال درخواست:", str(e))
        await update.message.reply_text("⛔ خطای داخلی در ربات!")

# سرور ساختگی برای Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive.')

def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, DummyHandler)
    print(f"✅ Server is running on port {port}")
    httpd.serve_forever()

# اجرای موازی ربات و سرور
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()
