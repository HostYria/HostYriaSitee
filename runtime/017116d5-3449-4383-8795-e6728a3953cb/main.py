import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# دالة البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("كيفك", callback_data="كيفك")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("أهلاً بك 👋", reply_markup=reply_markup)

# دالة عند الضغط على الزر
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "كيفك":
        await query.edit_message_text("الحمدلله تمام 😄")

def main():
    # قراءة التوكن من متغير البيئة
    TOKEN = os.environ.get("TOKEN_BOT")
    if not TOKEN:
        print("Error: TOKEN_BOT is not set in environment variables!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running... ✅")
    app.run_polling()

if __name__ == "__main__":
    main()