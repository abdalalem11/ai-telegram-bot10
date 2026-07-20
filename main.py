import asyncio
import logging
import os
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("مرحباً! البوت يعمل 🚀")

async def healthcheck(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ البوت يعمل بشكل طبيعي!")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("لم يتم العثور على BOT_TOKEN!")
        return
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", healthcheck))
    
    webhook_url = os.getenv("RENDER_EXTERNAL_URL")
    if webhook_url:
        logger.info(f"تشغيل مع Webhook: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 10000)),
            url_path="/telegram",
            webhook_url=f"{webhook_url}/telegram"
        )
    else:
        logger.info("تشغيل مع Polling")
        asyncio.run(app.run_polling())

if __name__ == "__main__":
    main()
