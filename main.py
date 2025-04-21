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

# 3. تحميل الكوبونات
def load_coupons(file_path='coupons.xlsx'):
    try:
        df = pd.read_excel(file_path)
        required_columns = [
            'title', 'description', 'code',
            'link', 'countries', 'note', 'image'
        ]
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

# 4. التعامل مع الرسائل الواردة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    df = load_coupons()
    
    if df is None:
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
        # إذا كان هناك رابط صورة صالح، نرسلها مع التسمية
        if isinstance(image_url, str) and image_url.strip():
            try:
                await update.message.reply_photo(photo=image_url, caption=response)
            except Exception as e:
                logger.warning(f"فشل إرسال الصورة ({e}), سنرسل النص فقط.")
                await update.message.reply_text(response)
        else:
            # لا توجد صورة، نرسل النص فقط
            await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ عذراً، لم يتم العثور على الكوبون.")

# 5. أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل اسم الكوبون (مثال: نمشي) وسأبحث عنه."
    )

# 6. نقطة الدخول
def main():
    Thread(target=run_flask, daemon=True).start()
    
    token = os.getenv("TOKEN")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ البوت يعمل...")
    application.run_polling()

if __name__ == '__main__':
    main()
