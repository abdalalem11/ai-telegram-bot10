import logging
import requests
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# محیط
TELEGRAM_TOKEN = "7709824108:AAHTvv3jVQpIDYvWyug8BpIq-HdnTv6rtNA"
OPENROUTER_API_KEY = "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"

# پاسخ به /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من آماده‌ام. سوالی داری بپرس.")

# پاسخ چت
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistral/mixtral-8x7b",  # مدل سبک‌تر برای تست
        "messages": [
            {"role": "system", "content": "تو یک ربات پاسخ‌گوی فارسی هستی."},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            await update.message.reply_text(reply)
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