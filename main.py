import os
import logging
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# إعداد سجل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
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
        await update.message.reply_text("⚠️ حدث خطأ في تحميل الكوبونات.")
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
    await update.message.reply_text("مرحباً! أرسل اسم الكوبون (مثال: نمشي) وسأبحث عنه.")

def main():
    token = os.getenv("TOKEN")
    if not token:
        logger.error("❌ لم يتم تعيين التوكن!")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ البوت يعمل...")
    app.run_polling()

if __name__ == '__main__':
    main()
