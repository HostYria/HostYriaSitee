import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# محاولة استيراد pytz
try:
    import pytz
    from datetime import datetime
    pytz_available = True
except ImportError:
    pytz_available = False


# دالة البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("كيفك؟", callback_data="how_are_you")],
        [InlineKeyboardButton("⏰ شقد الساعة؟", callback_data="time_now")],
        [InlineKeyboardButton("📅 شقد نحنا بالشهر؟", callback_data="date_now")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"أهلاً {user.first_name}! 💬\nاختر من الأزرار بالأسفل 👇",
        reply_markup=reply_markup
    )


# التعامل مع الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "how_are_you":
        await query.edit_message_text("الحمد لله أنا تمام 😎")

    elif query.data == "time_now":
        if pytz_available:
            tz = pytz.timezone("Asia/Damascus")  # غيرها حسب منطقتك
            now = datetime.now(tz).strftime("%H:%M:%S")
            await query.edit_message_text(f"⏰ الوقت الحالي: {now}")
        else:
            await query.edit_message_text("⚠️ مكتبة pytz غير موجودة 😔")

    elif query.data == "date_now":
        if pytz_available:
            tz = pytz.timezone("Asia/Damascus")
            today = datetime.now(tz).strftime("%Y-%m-%d")
            await query.edit_message_text(f"📅 التاريخ اليوم: {today}")
        else:
            await query.edit_message_text("⚠️ مكتبة pytz غير موجودة 😔")


# تشغيل البوت
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ لم يتم تعيين متغير BOT_TOKEN في بيئة التشغيل!")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("✅ البوت شغال واستنى أوامر المستخدم...")
    app.run_polling()


if __name__ == "__main__":
    main()