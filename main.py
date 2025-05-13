import os
import logging
import pandas as pd
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from difflib import get_close_matches

# إعداد خادم Flask للـ Health Check
app = Flask(__name__)
@app.route('/health')
def health_check():
    return "OK", 200
def run_flask():
    app.run(host='0.0.0.0', port=8080)

# إعداد Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تحميل الكوبونات وتنظيف البيانات
def load_coupons(file_path='coupons.xlsx'):
    logger.info(f"🗂️ Attempting to load coupons from: {file_path}")
    logger.info(f"🌐 Current working directory: {os.getcwd()}")
    try:
        df = pd.read_excel(file_path)
        logger.info(f"✅ Excel file read successfully, shape: {df.shape}")
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
        return df
    except Exception as e:
        logger.error(f'⚠️ Error reading Excel file: {e}')
        return None

# البحث المتقدم مع التصحيح الإملائي
def find_coupons(df, user_input):
    user_input_clean = user_input.strip().lower()
    df['title_clean'] = df['title'].astype(str).str.lower()

    matches = df[df['title_clean'].str.contains(user_input_clean)]

    if not matches.empty:
        return matches, None
    else:
        possible_titles = df['title_clean'].unique().tolist()
        suggestions = get_close_matches(user_input_clean, possible_titles, n=1, cutoff=0.6)
        return None, suggestions[0] if suggestions else None

# التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logger.info(f"📩 Received user input: {user_input}")
    df = load_coupons()

    if df is None:
        logger.error("⚠️ Failed to load coupons DataFrame.")
        await update.message.reply_text("⚠️ حدث خطأ في تحميل الكوبونات.")
        return

    results, suggestion = find_coupons(df, user_input)

    if results is not None:
        for idx, coupon in results.iterrows():
            response = (
                f"🎉 كوبون {coupon['title']}\n\n"
                f"🔥 {coupon['description']}\n\n"
                f"✅ الكوبون : {coupon['code']}\n\n"
                f"🌍 صالح لـ : {coupon['countries']}\n\n"
                f"📌 ملاحظة : {coupon['note']}\n\n"
                f"🛒 رابط الشراء : {coupon['link']}\n\n"
                "💎 لمزيد من الكوبونات والخصومات قم بزيارة موقعنا :\n\n"
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
        if suggestion:
            await update.message.reply_text(
                f"❓ لم يتم العثور على الكوبون المطلوب.\nهل كنت تقصد: "{suggestion}"؟"
            )
        else:
            await update.message.reply_text(
                "⚠️ عذراً، لم يتم العثور على الكوبون. تأكد من كتابة اسم المتجر بشكل صحيح."
            )

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"🔔 /start command received from user {update.effective_user.id}")
    await update.message.reply_text(
        "مرحباً! أرسل اسم الكوبون (مثال: نمشي أو نون) وسأبحث لك عن أفضل العروض 🔍"
    )

# نقطة الدخول
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
