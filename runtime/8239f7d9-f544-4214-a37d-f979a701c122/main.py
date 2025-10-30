import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import pytz
from datetime import datetime

# إعداد الـ logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب التوكن من متغير البيئة
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ لم يتم العثور على متغير البيئة BOT_TOKEN")

# منطقة زمنية اختبارية للتأكد أن pytz شغالة
damascus = pytz.timezone("Asia/Damascus")
logger.info(f"⏰ Current Damascus Time: {datetime.now(damascus).strftime('%Y-%m-%d %H:%M:%S')}")

# دالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("كيفك؟", callback_data="how_are_you")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"أهلاً {user.first_name} 👋\n"
        "أنا بوت تجريبي بسيط للتأكد من عمل المكاتب 🔥",
        reply_markup=reply_markup
    )

# رد على الزر
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "how_are_you":
        await query.edit_message_text(text="الحمد لله أنا تمام 😎")

# تشغيل البوت
def main():
    logger.info("🚀 Starting bot... checking if libraries are working.")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()