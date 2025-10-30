import os
import json
import re
from pathlib import Path
from typing import Dict
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

# --- إعدادات عامة ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ لم يتم العثور على متغير البيئة BOT_TOKEN. قم بتعيينه قبل التشغيل.")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# --- دوال مساعدة ---

def escape_md(text: str) -> str:
    """تهريب الرموز الخاصة في MarkdownV2"""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

def _user_json_path(user_id: int, kind: str) -> Path:
    """توليد مسار ملف JSON للمستخدم"""
    return DATA_DIR / f"user_{user_id}_{kind}.json"

def _load_json(path: Path) -> Dict:
    """قراءة JSON إن وجد"""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_json(path: Path, obj: Dict):
    """حفظ JSON"""
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _make_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة الأزرار"""
    buttons = [
        [InlineKeyboardButton("اسم المستخدم", callback_data="username")],
        [InlineKeyboardButton("معرف", callback_data="userid")],
    ]
    return InlineKeyboardMarkup(buttons)

# --- الأوامر الأساسية ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند إرسال /start"""
    user = update.effective_user
    if not user:
        return

    username = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip() or "مستخدم"
    user_id = user.id

    text = escape_md(
        f"أهلاً بك {username}\n\n"
        f"أيدي حسابك: `{user_id}`\n\n"
        "اضغط الأزرار أدناه لتنفيذ الإجراءات."
    )

    await update.message.reply_text(
        text,
        reply_markup=_make_keyboard(),
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
    )

# --- التعامل مع الضغط على الأزرار ---

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return

    await query.answer()  # إغلاق المؤشر لدى المستخدم
    user = query.from_user
    username = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip() or "مستخدم"
    user_id = user.id
    kind = query.data  # 'username' أو 'userid'

    try:
        if kind == "username":
            path = _user_json_path(user_id, "username")
            data = _load_json(path)
            count = data.get("count", 0) + 1
            display = username if count == 1 else f"{username} {count}"

            data = {"base": username, "count": count, "display": display, "user_id": user_id}
            _save_json(path, data)

            msg = escape_md(
                f"✅ تم تحديث ملف الاسم بنجاح!\n\n"
                f"الاسم الحالي: `{display}`\n"
                f"ملف: `{path.as_posix()}`\n\n"
                "اضغط مرة أخرى لزيادة العدد."
            )
            await _safe_edit(query, msg)

        elif kind == "userid":
            path = _user_json_path(user_id, "userid")
            data = _load_json(path)
            count = data.get("count", 0) + 1
            display_id = str(user_id) if count == 1 else f"{user_id} {count}"

            data = {"id": user_id, "count": count, "display": display_id, "user": username}
            _save_json(path, data)

            msg = escape_md(
                f"✅ تم تحديث ملف المعرف بنجاح!\n\n"
                f"المعرف الحالي: `{display_id}`\n"
                f"ملف: `{path.as_posix()}`\n\n"
                "اضغط مرة أخرى لزيادة العدد."
            )
            await _safe_edit(query, msg)

        else:
            await query.answer(text="❌ نوع الزر غير معروف.", show_alert=True)

    except Exception as e:
        error_msg = escape_md(f"⚠️ حدث خطأ أثناء تنفيذ العملية:\n`{e}`")
        await _safe_edit(query, error_msg)


async def _safe_edit(query, text: str):
    """محاولة آمنة لتعديل الرسالة أو إرسال جديدة عند الفشل"""
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=_make_keyboard(),
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
        )
    except Exception:
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=_make_keyboard(),
                parse_mode="MarkdownV2",
            )
        except Exception as inner_error:
            print("⚠️ فشل إرسال الرسالة:", inner_error)

# --- التشغيل ---

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    print("✅ البوت يعمل الآن... اضغط Ctrl+C للإيقاف.")
    app.run_polling()

if __name__ == "__main__":
    main()