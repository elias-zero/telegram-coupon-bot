import os
import logging
import pandas as pd
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# 1. إعداد خادم Flask للـ Health Check
app = Flask(__name__)

@app.route('/health')
def health_check():
    """يرد بـ 'OK' عند طلب الرابط من خدمات المراقبة"""
    return "OK", 200

# 2. تشغيل الخادم في خيط منفصل
def run_flask():
    """تشغيل خادم Flask على منفذ 8080"""
    app.run(host='0.0.0.0', port=8080)

# 3. الجزء الخاص ببوت التليجرام
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_coupons(file_path='coupons.xlsx'):
    try:
        df = pd.read_excel(file_path)
        required_columns = ['title', 'description', 'code', 'link', 'countries', 'note']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f'العمود "{col}" غير موجود!')
                return None
        return df
    except Exception as e:
        logger.error(f'خطأ في قراءة الملف: {e}')
        return None

def find_coupon(df, coupon_name: str):
    coupon = df[df['title'].str.lower() == coupon_name.lower()]
    return coupon.iloc[0] if not coupon.empty else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    df = load_coupons()
    
    if df is None:
        await update.message.reply_text("⚠️  حدث خطأ في تحميل الكوبونات.")
        return

    coupon = find_coupon(df, user_input)
    if coupon is not None:
        response = (
            f"🎉 كوبون {coupon['title']}\n"
            f"{coupon['description']}\n\n"
            f"✅ الكوبون: {coupon['code']}\n"
            f"🌍 صالح لـ: {coupon['countries']}\n"
            f"📌 ملاحظة: {coupon['note']}\n"
            f"🛒 رابط الشراء: {coupon['link']}\n\n"
            "لمزيد من العروض: https://www.discountcoupon.online"
        )
    else:
        response = "⚠️ عذراً، لم يتم العثور على الكوبون."
    
    await update.message.reply_text(response)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل اسم الكوبون (مثال: نمشي بالعربية او Namshi بالإنجليزية) وسأبحث عنه.")

def main():
    # بدء تشغيل خادم Flask في خيط منفصل
    Thread(target=run_flask).start()
    
    # بدء تشغيل البوت
    token = os.getenv("TOKEN")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ البوت يعمل...")
    application.run_polling()
    application.run_polling(allowed_updates=Update.ALL_TYPES)  # <-- التعديل هنا

if __name__ == '__main__':
    main()
