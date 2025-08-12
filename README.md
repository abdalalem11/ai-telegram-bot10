# 🤖 AI Telegram Bot with OpenRouter

یک ربات تلگرام هوش مصنوعی ساده با استفاده از:
- OpenRouter.ai (مدل‌های GPT)
- python-telegram-bot
- قابل دیپلوی در Render.com

## 📦 نصب محلی (برای تست)
```bash
pip install -r requirements.txt
```

## 🛠 اجرا
```bash
export TELEGRAM_TOKEN=توکن_ربات
export OPENROUTER_API_KEY=کلید_API
python main.py
```

## ☁️ دیپلوی در Render
1. این ریپو را روی GitHub بفرستید
2. وارد حساب خود در [Render](https://render.com) شوید
3. گزینه "New Web Service" را بزنید
4. ریپو را انتخاب کرده و مراحل را طی کنید
5. Environment Variables را تنظیم کنید:
   - `TELEGRAM_TOKEN`
   - `OPENROUTER_API_KEY`

## 📌 نکات
- از Polling استفاده می‌کند (نیازی به webhook نیست)
- فارسی‌زبان و مودب