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
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# 2. إعداد Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 3. تحميل الكوبونات مع تنظيف البيانات وتتبع اللوج
def load_coupons(file_path='coupons.xlsx'):
    logger.info(f"🗂️ Attempting to load coupons from: {file_path}")
    logger.info(f"🌐 Current working directory: {os.getcwd()}")
    try:
        df = pd.read_excel(file_path)
        logger.info(f"✅ Excel file read successfully, shape: {df.shape}")

        # تنظيف القيم النصية من مسافات بيضاء
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        logger.info("✂️ Trimmed whitespace from all string cells.")

        required_columns = [
            'title', 'description', 'code',
            'link', 'countries', 'note', 'image'
        ]
        for col in required_columns:
            if col not in df.columns:
                logger.error(f'❌ Column "{col}" is missing in the Excel file!')
                return None
        logger.info(f"📋 All required columns are present: {required_columns}")
        return df
    except Exception as e:
        logger.error(f'⚠️ Error reading Excel file: {e}')
        return None

# 4. البحث عن الكوبون مع مطابقة بعد تنظيف

def find_coupon(df, coupon_name: str):
    coupon_search = coupon_name.strip().lower()
    logger.info(f"🔍 Searching for coupon with title: '{coupon_search}'")
    # مقارنة غير حساسة لحالة الأحرف بعد التنظيف
    df['title_clean'] = df['title'].astype(str).str.lower()
    match = df[df['title_clean'] == coupon_search]
    if match.empty:
        logger.info("❌ No matching coupon found.")
        return None
    logger.info("✅ Coupon found, returning the first match.")
    return match.iloc[0]

# 5. التعامل مع الرسائل الواردة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logger.info(f"📩 Received user input: {user_input}")
    df = load_coupons()
    
    if df is None:
        logger.error("⚠️ Failed to load coupons DataFrame.")
        await update.message.reply_text("⚠️ حدث خطأ في تحميل الكوبونات.")
        return

    coupon = find_coupon(df, user_input)
    if coupon is not None:
        response = (
            f"🎉 كوبون {coupon['title']}\n\n"
            f"🔥 {coupon['description']}\n\n"
            f"✅ الكوبون : {coupon['code']}\n\n"
            f"🌍 صالح لـ : {coupon['countries']}\n\n"
            f"📌 ملاحظة : {coupon['note']}\n\n"
            f"🛒 رابط الشراء : {coupon['link']}\n\n"
            "💎 لمزيد من الكوبونات والخصومات قم بزيارة موقعنا : \n\n"
            "https://www.discountcoupon.online"
        )

        image_url = coupon.get('image')
        if isinstance(image_url, str) and image_url:
            try:
                logger.info(f"📸 Sending photo for coupon: {image_url}")
                await update.message.reply_photo(photo=image_url, caption=response)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send image ({e}), sending text only.")
                await update.message.reply_text(response)
        else:
            logger.info("✉️ No image URL, sending text response.")
            await update.message.reply_text(response)
    else:
        logger.info("⚠️ Coupon not found, notifying user.")
        await update.message.reply_text("⚠️ عذراً، لم يتم العثور على الكوبون.")

# 6. أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"🔔 /start command received from user {update.effective_user.id}")
    await update.message.reply_text(
        "مرحباً! أرسل اسم الكوبون (مثال: نمشي بالعربية او Namshi بالإنجليزية) وسأبحث عنه."
    )

# 7. نقطة الدخول
def main():
    logger.info("🚀 Starting Flask health check thread...")
    Thread(target=run_flask, daemon=True).start()
    
    token = os.getenv("TOKEN")
    if not token:
        logger.error("❌ TOKEN environment variable is not set!")
        return
    logger.info("🔑 Token loaded from env, initializing bot...")

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Bot is up and running, polling for messages...")
    application.run_polling()

if __name__ == '__main__':
    main()
