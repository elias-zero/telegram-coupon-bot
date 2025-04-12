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

# تحميل بيانات الكوبونات من ملف Excel
def load_coupons(file_path='coupons.xlsx'):
    try:
        df = pd.read_excel(file_path)
        # التأكد من وجود الأعمدة المطلوبة
        required_columns = ['title', 'description', 'code', 'link', 'countries', 'note']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f'ملف Excel يجب أن يحتوي على عمود "{col}"')
                return None
        return df
    except Exception as e:
        logger.error(f'خطأ في قراءة ملف Excel: {e}')
        return None

# البحث عن الكوبون باستخدام العمود title
def find_coupon(df, coupon_name: str):
    coupon = df[df['title'].str.lower() == coupon_name.lower()]
    if not coupon.empty:
        return coupon.iloc[0]
    else:
        return None

# التعامل مع الرسائل الواردة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    df = load_coupons()
    if df is None:
        await update.message.reply_text("حدث خطأ أثناء تحميل البيانات.")
        return

    coupon_row = find_coupon(df, user_input)
    if coupon_row is not None:
        message = (
            f"كوبون {coupon_row['title']}\n"
            f"{coupon_row['description']}\n"
            f"الكوبون : {coupon_row['code']}\n"
            f"صالح لـ : {coupon_row['countries']}\n"
            f"ملاحظة : {coupon_row['note']}\n"
            f"رابط الشراء : {coupon_row['link']}\n\n"
            "لمزيد من الكوبونات قم بزيارة موقعنا : https://www.discountcoupon.online"
        )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("عفواً، لم يتم العثور على كوبون بهذا الاسم.")

# أمر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل اسم الكوبون (مثلاً: نمشي) وسأقوم بالبحث عنه.")

# الدالة الرئيسية لتشغيل البوت
async def main():
    # قراءة التوكن من متغير البيئة، تأكد من أن متغير TOKEN معد في Render أو في إعدادات المشروع
    token = os.getenv("TOKEN")
    if not token:
        logger.error("التوكن غير موجود! تأكد من إعداد متغير البيئة TOKEN.")
        return

    application = ApplicationBuilder().token(token).build()

    # إضافة معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("البوت يعمل الآن...")
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
