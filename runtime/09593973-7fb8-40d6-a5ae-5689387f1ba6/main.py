import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest
import random
import string

# Replace with your bot token
TOKEN = "7775647810:AAEsvvD8cJlxxZGZUJlBs01vrSTxHmrqZy8"
CHANNEL_ID = "@hossamo_peterson"  # استبدل هذا بمعرف قناتك

ACCOUNTS_FILE = "user_accounts.json"
GIFT_CODES_FILE = "gift_codes.json"

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=update.effective_user.id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest:
        return False

async def force_subscribe_markup():
    keyboard = [
        [InlineKeyboardButton("الموافقة والمتابعة الى القناة ✅", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
        [InlineKeyboardButton("تشغيل البوت 🤖", callback_data='start_bot')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referred_by = None
    
    # Handle referral
    if context.args and context.args[0].startswith('ref_'):
        referred_by = int(context.args[0].split('_')[1])
        # Store referral info in context
        context.user_data['referred_by'] = referred_by

    # التحقق من الاشتراك
    if not await check_subscription(update, context):
        terms_message = """
شروط واحكام استخدام البوت:

🟥 أنت المسؤول الوحيد عن أموالك، دورنا يقتصر على الوساطة بينك وبين الموقع، مع ضمان إيداع وسحب أموالك بكفاءة وموثوقية.

🟥 لا يجوز للاعب إيداع وسحب الأرصدة بهدف التبديل بين وسائل الدفع. تحتفظ إدارة البوت بالحق في سحب أي رصيد والاحتفاظ به إذا تم اكتشاف عملية تبديل أو أي انتهاك لقوانين البوت.

🟥 إنشاء أكثر من حساب يؤدي إلى حظر جميع الحسابات وتجميد الأرصدة الموجودة فيها، وذلك وفقاً لشروط وأحكام الموقع للحد من الأنشطة الاحتيالية، وامتثالاً لسياسة اللعب النظيف.

🟥 أي محاولات للغش أو إنشاء حسابات متعددة بغرض الاستفادة من رصيد الإحالة ستؤدي إلى تجميد حسابك فوراً وإزالة جميع الإحالات الخاصة بك.

**يُعدّ انضمامك للقناة والاستمرار في استخدام البوت بمثابة الموافقة على هذه الشروط، وتحمل المسؤولية الكاملة عن أي انتهاك لها.**
"""
        await update.message.reply_text(
            terms_message,
            reply_markup=await force_subscribe_markup(),
            parse_mode='Markdown'
        )
        return

    # التحقق ما إذا كان المستخدم مسجل
    is_registered = False
    for account in user_accounts.values():
        if account.get('user_id') == user_id:
            is_registered = True
            break

    if is_registered:
        # إذا كان مسجل، اعرض القائمة الرئيسية
        main_menu_keyboard = [
            [InlineKeyboardButton("Ichancy ⚡", callback_data='ichancy')],
            [InlineKeyboardButton("شحن رصيد في البوت 📥", callback_data='deposit'),
             InlineKeyboardButton("سحب رصيد من البوت 📤", callback_data='withdraw')],
            [InlineKeyboardButton("نظام الإحالات 👥", callback_data='referral')],
            [InlineKeyboardButton("كود هدية 🎁", callback_data='gift_code'),
             InlineKeyboardButton("اهداء رصيد 🎁", callback_data='send_balance')],
            [InlineKeyboardButton("رسالة للأدمن 📩", callback_data='support'),
             InlineKeyboardButton("تواصل مع الدعم 📞", callback_data='contact_support')],
            [InlineKeyboardButton("الشروط والأحكام 🧾", callback_data='terms')]
        ]
        reply_markup = InlineKeyboardMarkup(main_menu_keyboard)
        balance = 0
        for account in user_accounts.values():
            if account['user_id'] == user_id:
                balance = account.get('balance', 0)
                break
        await update.message.reply_text(
            f"معرف حسابك: `{user_id}`\nرصيدك في البوت: {balance} ليرة سورية",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # إذا لم يكن مسجل، اعرض قائمة إنشاء الحساب
        keyboard = [
            [InlineKeyboardButton("إنشاء حساب", callback_data='create_account')],
            [InlineKeyboardButton("رسالة للأدمن 📩", callback_data='support')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # تأكد من عدم وجود حساب للمستخدم قبل عرض صفحة التسجيل
        user_exists = False
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                user_exists = True
                break

        if not user_exists:
            welcome_text = f"""
معرف حسابك: `{user_id}`
عليك انشاء حساب أولاً للاستمرار
"""
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # إذا كان المستخدم موجود ولكن تم حذف حسابه
            welcome_text = f"""
معرف حسابك: `{user_id}`
يمكنك إنشاء حساب جديد للاستمرار
"""
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 5029011355:
        return

    command = update.message.text.split()
    if len(command) == 0:
        return

    if command[0] == '/listpredefined':
        try:
            with open('predefined_accounts.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                accounts = data.get('accounts', [])
                if not accounts:
                    await update.message.reply_text("لا توجد حسابات معدة مسبقاً")
                    return
                accounts_text = "الحسابات المعدة مسبقاً:\n\n"
                for account in accounts:
                    accounts_text += f"اسم المستخدم:\n`{account['username']}`\n"
                    accounts_text += f"كلمة المرور:\n`{account['password']}`\n"
                    accounts_text += "—————————————\n"
                await update.message.reply_text(accounts_text, parse_mode='Markdown')
        except (FileNotFoundError, json.JSONDecodeError):
            await update.message.reply_text("حدث خطأ في قراءة ملف الحسابات")
        return

    if command[0] == '/addpredefined' and len(command) == 3:
        username, password = command[1], command[2]
        try:
            with open('predefined_accounts.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            # التحقق من عدم وجود الحساب مسبقاً
            accounts = data.get('accounts', [])
            for account in accounts:
                if account['username'] == username:
                    await update.message.reply_text("هذا الحساب موجود بالفعل")
                    return

            # إضافة الحساب الجديد
            accounts.append({'username': username, 'password': password})
            data['accounts'] = accounts

            with open('predefined_accounts.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            await update.message.reply_text("تم إضافة الحساب بنجاح")
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ: {str(e)}")
        return

    if command[0] == '/delpredefined' and len(command) == 2:
        username = command[1]
        try:
            with open('predefined_accounts.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            accounts = data.get('accounts', [])
            data['accounts'] = [acc for acc in accounts if acc['username'] != username]

            with open('predefined_accounts.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            await update.message.reply_text("تم حذف الحساب بنجاح")
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ: {str(e)}")
        return

    if command[0] == '/users':
        if not user_accounts:
            await update.message.reply_text("لا يوجد مستخدمين مسجلين حالياً")
            return

        users_text = "المستخدمين المسجلين:\n\n"
        for username, data in user_accounts.items():
            users_text += f"معرف المستخدم:\n`{data['user_id']}`\n"
            users_text += f"اسم المستخدم:\n`{username}`\n"
            users_text += f"كلمة المرور:\n`{data['password']}`\n"
            users_text += f"رصيد البوت: {data.get('balance', 0)} NSP\n"
            users_text += f"رصيد ايشانسي: {data.get('ichancy_balance', 0)} NSP\n"
            users_text += f"تاريخ التسجيل:\n`{data['created_at']}`\n"
            users_text += "—————————————\n"
        await update.message.reply_text(users_text, parse_mode='Markdown')
        return

    command = update.message.text.split()
    if len(command) < 2:
        help_text = """
الأوامر المتاحة:
/broadcast [الرسالة] - إرسال إذاعة عامة
/send [معرف المستخدم] [الرسالة] - إرسال رسالة لمستخدم محدد
/adduser [اسم المستخدم] [كلمة المرور] - إضافة حساب جديد
/deluser [اسم المستخدم] - حذف حساب
/addbalance [معرف المستخدم] [المبلغ] - إضافة رصيد
/deductbalance [معرف المستخدم] [المبلغ] - سحب رصيد
/setcontactaddr [العنوان] - تعيين عنوان التواصل مع الدعم
"""
        await update.message.reply_text(help_text)
        return

    if command[0] == '/broadcast':
        message = ' '.join(command[1:])
        success_count = 0
        for account in user_accounts.values():
            try:
                await context.bot.send_message(chat_id=account['user_id'], text=message)
                success_count += 1
            except:
                continue
        await update.message.reply_text(f"تم إرسال الإذاعة إلى {success_count} مستخدم")

    elif command[0] == '/send' and len(command) >= 3:
        user_id = command[1]
        message = ' '.join(command[2:])
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            await update.message.reply_text("تم إرسال الرسالة بنجاح")
        except:
            await update.message.reply_text("فشل إرسال الرسالة")

    elif command[0] == '/adduser' and len(command) == 3:
        user_id, password = command[1], command[2]
        # التحقق مما إذا كان المستخدم موجود بالفعل
        for account in user_accounts.values():
            if str(account.get('user_id')) == user_id:
                await update.message.reply_text("المستخدم موجود بالفعل")
                return

        # إنشاء حساب جديد باستخدام معرف المستخدم كمفتاح
        user_accounts[user_id] = {
            'password': password,
            'user_id': int(user_id),
            'created_at': str(update.message.date),
            'balance': 0
        }
        save_accounts()
        await update.message.reply_text("تم إنشاء الحساب بنجاح")

    elif command[0] == '/deluser' and len(command) == 2:
        target_user_id = command[1]
        # البحث عن الحساب باستخدام معرف المستخدم
        for username, account in list(user_accounts.items()):
            if str(account['user_id']) == target_user_id:
                del user_accounts[username]
                save_accounts()
                await update.message.reply_text("تم حذف الحساب بنجاح")
                return
        await update.message.reply_text("الحساب غير موجود")

    elif command[0] == '/addbalance' and len(command) >= 6:
        user_id = command[1]
        amount = int(command[2])
        bonus_percentage = float(command[3])
        transaction_id = command[4]
        payment_method = command[5]
        note = ' '.join(command[6:]) if len(command) > 6 else ''

        # حساب البونص
        bonus = int(amount * (bonus_percentage / 100))
        total_amount = amount + bonus

        for account in user_accounts.values():
            if str(account['user_id']) == user_id:
                account['balance'] = account.get('balance', 0) + total_amount
                
                # التحقق من وجود محيل وإضافة عمولة الإحالة
                if account.get('referred_by') and account.get('referred_by') != "null":
                    referral_bonus = int(amount * 0.05)  # 5% من المبلغ الأساسي
                    
                    # البحث عن حساب المحيل وإضافة العمولة
                    for referrer_account in user_accounts.values():
                        if str(referrer_account.get('user_id')) == str(account['referred_by']):
                            referrer_account['balance'] = referrer_account.get('balance', 0) + referral_bonus
                            # إرسال إشعار للمحيل
                            await context.bot.send_message(
                                chat_id=account['referred_by'],
                                text=f"🎁 لقد حصلت على {referral_bonus} قادمة من إحالاتك!"
                            )
                            break
                
                # حفظ تفاصيل العملية
                if 'transactions' not in account:
                    account['transactions'] = []
                
                transaction_details = {
                    'type': 'deposit',
                    'amount': amount,
                    'bonus': bonus,
                    'bonus_percentage': bonus_percentage,
                    'transaction_id': transaction_id,
                    'payment_method': payment_method,
                    'date': str(update.message.date),
                    'note': note
                }
                
                account['transactions'].append(transaction_details)
                save_accounts()

                # إرسال تأكيد للأدمن
                admin_msg = f"""
✅ تم إضافة رصيد:
👤 المستخدم: {user_id}
💰 المبلغ: {amount}
🎁 البونص: {bonus} ({bonus_percentage}%)
💵 المجموع: {total_amount}
🔢 رقم العملية: {transaction_id}
💳 طريقة الدفع: {payment_method}
📝 ملاحظات: {note}
"""
                await update.message.reply_text(admin_msg)

                # إرسال إشعار للمستخدم
                user_msg = f"""
تم شحن حسابك بنجاح ✅
المبلغ: {amount}
وسيلة الشحن: {payment_method}
رقم العملية: {transaction_id}
"""
                await context.bot.send_message(
                    chat_id=user_id,
                    text=user_msg
                )

                # إرسال رسالة البونص بشكل منفصل
                if bonus > 0:
                    bonus_msg = f"🎁 مبروك! لقد حصلت على زيادة {bonus} ليرة بسبب بونص {bonus_percentage}% اهلا وسهلا"
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=bonus_msg
                    )
                return
        await update.message.reply_text("المستخدم غير موجود")

    elif command[0] == '/deductbalance' and len(command) == 3:
        user_id = command[1]
        amount = int(command[2])
        for account in user_accounts.values():
            if str(account['user_id']) == user_id:
                if account.get('balance', 0) >= amount:
                    account['balance'] = account.get('balance', 0) - amount
                    save_accounts()
                    await update.message.reply_text(f"تم خصم {amount} من الرصيد")
                else:
                    await update.message.reply_text("الرصيد غير كافي")
                return
        await update.message.reply_text("المستخدم غير موجود")

    elif command[0] == '/giftcode' and len(command) == 3:
        try:
            amount = int(command[1])
            num_codes = int(command[2])

            if amount <= 0 or num_codes <= 0:
                await update.message.reply_text("يجب أن تكون القيم موجبة")
                return

            generated_codes = []

            # قراءة الأكواد الحالية
            try:
                with open(GIFT_CODES_FILE, 'r') as f:
                    gift_codes = json.load(f)
            except:
                gift_codes = {'codes': {}}

            # توليد الأكواد الجديدة
            for _ in range(num_codes):
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                generated_codes.append({'code': code, 'amount': amount})

            # تحديث الأكواد
            admin_id = str(update.effective_user.id)
            if admin_id not in gift_codes['codes']:
                gift_codes['codes'][admin_id] = []
            gift_codes['codes'][admin_id].extend(generated_codes)

            # حفظ في الملف
            with open(GIFT_CODES_FILE, 'w') as f:
                json.dump(gift_codes, f, indent=4)

            # إرسال الأكواد للأدمن
            codes_text = "\n\n".join([f"كود الهدية: `{code['code']}`\nقيمة الهدية: {code['amount']} NSP" for code in generated_codes])
            await update.message.reply_text(
                f"تم توليد الأكواد بنجاح:\n\n{codes_text}",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("تأكد من إدخال أرقام صحيحة")
            return

    elif command[0] == '/setpayaddr' and len(command) == 2:
        new_address = command[1]
        try:
            if new_address == "000":
                with open('payment_messages.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['syriatel_address'] = new_address
                with open('payment_messages.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                await update.message.reply_text("✅ تم تحديث عنوان الدفع. سيظهر للمستخدمين أن الشحن متوقف حالياً")
            else:
                with open('payment_messages.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['syriatel_address'] = new_address
                with open('payment_messages.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                await update.message.reply_text(f"✅ تم تحديث عنوان الدفع بنجاح إلى: {new_address}")
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء تحديث عنوان الدفع: {str(e)}")
    elif command[0] == '/setcontactaddr' and len(command) == 2:
        new_address = command[1]
        try:
            with open('payment_messages.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            data['contact_address'] = new_address
            with open('payment_messages.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            await update.message.reply_text(f"✅ تم تحديث عنوان التواصل مع الدعم بنجاح إلى: {new_address}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"يمكنك التجربة الآن من خلال الضغط على زر التواصل مع الدعم في القائمة الرئيسية"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء تحديث عنوان التواصل مع الدعم: {str(e)}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # التحقق من الأدمن
    if update.effective_user.id == 5029011355:
        if query.data.startswith('set_credentials_'):
            user_id = query.data.split('_')[2]
            context.user_data['setting_credentials_for'] = user_id
            context.user_data['credentials_step'] = 'username'
            await query.message.reply_text("الرجاء إدخال اسم المستخدم الذي تريد تعيينه:")
            return

        if query.data.startswith('reply_'):
            user_id = query.data.split('_')[1]
            context.user_data['replying_to'] = user_id
            await query.message.reply_text(f"أرسل ردك للمستخدم {user_id}:")
            return
        elif query.data.startswith('approve_'):
            username = query.data.split('_')[1]
            if username in user_accounts:
                user_accounts[username]['status'] = 'approved'
                user_id = user_accounts[username]['user_id']
                # إخبار المستخدم بالموافقة
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ تمت الموافقة على حسابك! يمكنك الآن استخدام البوت"
                )
                await query.message.edit_text(f"تم الموافقة على حساب {username} ✅")
            return
        elif query.data.startswith('reject_'):
            username = query.data.split('_')[1]
            if username in user_accounts:
                user_id = user_accounts[username]['user_id']
                del user_accounts[username]
                save_accounts() # Save after deletion
                # إخبار المستخدم بالرفض
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ عذراً، تم رفض طلب إنشاء حسابك. يمكنك المحاولة مرة أخرى"
                )
                await query.message.edit_text(f"تم رفض حساب {username} ❌")
            return

    if query.data == 'start_bot':
        if await check_subscription(update, context):
            keyboard = [
                [InlineKeyboardButton("إنشاء حساب", callback_data='create_account')],
                [InlineKeyboardButton("رسالة للأدمن 📩", callback_data='support'),
                 InlineKeyboardButton("تواصل مع الدعم 📞", callback_data='contact_support')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_text = f"""
معرف حسابك: `{update.effective_user.id}`
عليك انشاء حساب أولاً للاستمرار
"""
            await query.message.edit_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.answer("عليك الاشتراك بالقناة اولاً", show_alert=True)
    elif query.data == 'check_subscription':
        if await check_subscription(update, context):
            await query.message.reply_text(
                "اضغط على كلمة /start للبدء في استخدام البوت."
            )
            await query.message.delete()
        else:
            await query.answer("عذراً، يجب عليك الاشتراك في القناة أولاً ❗️", show_alert=True)
    elif query.data == 'create_account':
        if await check_subscription(update, context):
            # التحقق من أن المستخدم ليس لديه حساب مسبقاً
            has_account = False
            for account in user_accounts.values():
                if account.get('user_id') == update.effective_user.id:
                    has_account = True
                    break

            if has_account:
                await query.message.edit_text("عذراً، لديك حساب مسجل بالفعل ❌")
                return

            context.user_data['referred_by'] = context.user_data.get('referred_by') #added
            available_account = get_available_account()
            if available_account:
                username = available_account['username']
                password = available_account['password']

                # رسالة التسجيل الأولية
                register_message = await query.message.edit_text(
                    "🚀 جاري تجهيز حسابك الجديد...\nيرجى الانتظار قليلاً..."
                )

                # إضافة تأخير قصير
                await asyncio.sleep(2)

                # إظهار رسالة التقدم
                progress_message = await query.message.edit_text("جاري إنشاء الحساب... ⏳\n[          ] 0%")

                # تحديث شريط التقدم
                for i in range(1, 11):
                    progress_bar = "█" * i + " " * (10 - i)
                    percentage = i * 10
                    await progress_message.edit_text(f"جاري إنشاء الحساب... ⏳\n[{progress_bar}] {percentage}%")
                    await asyncio.sleep(0.5)

                # حفظ بيانات المستخدم
                # إضافة معلومات الإحالة عند إنشاء الحساب
                user_accounts[username] = {
                    'password': password,
                    'user_id': update.effective_user.id,
                    'created_at': str(query.message.date),
                    'balance': 0,
                    'referred_by': context.user_data.get('referred_by'),
                    'has_deposited': False
                }

                # حذف الحساب من القائمة المعدة مسبقاً
                try:
                    with open('predefined_accounts.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data['accounts'] = [acc for acc in data['accounts'] if acc['username'] != username]
                    with open('predefined_accounts.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    print(f"Error removing account from predefined list: {e}")

                # حفظ حسابات المستخدمين
                save_accounts()




                # ثم عرض رسالة النجاح
                success_message = f"""
✅ تم إنشاء حسابك بنجاح

معلومات حسابك:
👤 اسم المستخدم: {username}
🔑 كلمة المرور: {password}

⚠️ يرجى الاحتفاظ بمعلومات حسابك في مكان آمن
📌 يمكنك الآن استخدام البوت بكامل مميزاته
"""
                keyboard = [
                    [InlineKeyboardButton("القائمة الرئيسية ✅", callback_data='show_main_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                success_msg = await query.message.edit_text(
                    success_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

                # إرسال إشعار للأدمن
                admin_notification = f"""
✅ تم تسجيل حساب جديد:
الاسم: {update.effective_user.first_name}
المعرف: {update.effective_user.id}
اسم المستخدم: `{username}`
كلمة المرور: `{password}`
الوقت: {query.message.date}
"""
                await context.bot.send_message(
                    chat_id="5029011355",
                    text=admin_notification,
                    parse_mode='Markdown'
                )
                # إرسال إشعار للمحيل إذا وجد
                if context.user_data.get('referred_by'):
                    await context.bot.send_message(
                        chat_id=context.user_data['referred_by'],
                        text=f"✅ تم تسجيل مستخدم جديد من خلال رابط الإحالة الخاص بك!"
                    )

            else:
                # إظهار رسالة التحميل أولاً
                loading_message = await query.message.edit_text("جاري الاتصال بالخادم ⏳\n[          ] 0%")

                # تحديث شريط التقدم
                for i in range(1, 6):
                    progress_bar = "█" * i + " " * (10 - i)
                    percentage = i * 20
                    await loading_message.edit_text(f"جاري الاتصال بالخادم ⏳\n[{progress_bar}] {percentage}%")
                    await asyncio.sleep(0.5)

                # انتظار إضافي قبل إظهار رسالة الخطأ
                await asyncio.sleep(3)

                # إظهار رسالة الخطأ النهائية
                await query.message.edit_text("❌ خطأ في مخدم ايشانسي\n⏰ حاول بعد 5 دقائق")
        else:
            await query.message.edit_text(
                "عذراً، يجب عليك الاشتراك في القناة أولاً ❗️",
                reply_markup=await force_subscribe_markup()
            )
    elif query.data == 'ichancy_deposit':
        # التحقق من وجود حساب للمستخدم
        user_id = update.effective_user.id
        user_account = None
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                user_account = account
                break

        if user_account:
            context.user_data['waiting_for_deposit'] = True
            await query.message.edit_text(
                "أدخل المبلغ المراد شحنه في حسابك Ichancy 👇"
            )
        else:
            await query.message.edit_text(
                "عذراً، لم يتم العثور على حسابك ❌"
            )

    elif query.data == 'ichancy':
        # التحقق من وجود حساب للمستخدم
        user_id = update.effective_user.id
        user_account = None
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                user_account = account
                break

        if not user_account:
            await query.message.edit_text(
                "عذراً، يجب إنشاء حساب أولاً ❌"
            )
            return

        balance = user_account.get('balance', 0)
        user_balance = user_account.get('balance', 0)
        ichancy_balance = user_account.get('ichancy_balance', 0)

        ichancy_keyboard = [
            [InlineKeyboardButton("شحن في الحساب ⬆️", callback_data='ichancy_deposit'),
             InlineKeyboardButton("سحب من الحساب ⬇️", callback_data='ichancy_withdraw')],
            [InlineKeyboardButton("معلومات الحساب 💲", callback_data='ichancy_info')],
            [InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(ichancy_keyboard)
        try:
            message_text = """
ايشانسي
https://www.ichancy.com/
"""
            await query.message.edit_text(
                message_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Error in ichancy button: {e}")
            # محاولة إرسال رسالة جديدة إذا فشل التعديل
            await query.message.reply_text(
                "ايشانسي\nhttps://www.ichancy.com/",
                reply_markup=reply_markup
            )

    elif query.data == 'ichancy_info':
        try:
            user_id = update.effective_user.id
            user_info = None
            username = None

            # البحث عن معلومات الحساب
            for username_key, account_data in user_accounts.items():
                if account_data.get('user_id') == user_id:
                    user_info = account_data
                    username = username_key
                    break

            if user_info:
                from datetime import datetime
                from dateutil import parser
                import pytz

                created_date = parser.parse(user_info['created_at'])
                gmt3 = pytz.timezone('Asia/Baghdad')
                created_date_gmt3 = created_date.astimezone(gmt3)
                formatted_date = created_date_gmt3.strftime('%Y-%m-%d %H:%M')

                info_message = f"""
🌐 اسمك على الموقع: `{username}`
🌐 رصيدك على الموقع: {user_info.get('ichancy_balance', 0)} NSP

👤 اسمك في البوت: ({update.effective_user.first_name})
🤖 رصيدك في البوت: {user_info.get('balance', 0)} NSP

⚽️ معرف اللاعب: `{user_id}`
📅 تاريخ التسجيل: {formatted_date}
"""
                keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='ichancy')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(info_message, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.message.edit_text("لم يتم العثور على معلومات الحساب", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع 🔙", callback_data='ichancy')]]))
        except Exception as e:
            print(f"Error in ichancy_info: {e}")
            error_keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='ichancy')]]
            error_markup = InlineKeyboardMarkup(error_keyboard)
            await query.message.edit_text("عذراً، حدث خطأ أثناء عرض المعلومات. الرجاء المحاولة مرة أخرى.", reply_markup=error_markup)

    elif query.data == 'show_main_menu':
        main_menu_keyboard = [
            [InlineKeyboardButton("Ichancy ⚡", callback_data='ichancy')],
            [InlineKeyboardButton("شحن رصيد في البوت 📥", callback_data='deposit'),
             InlineKeyboardButton("سحب رصيد من البوت 📤", callback_data='withdraw')],
            [InlineKeyboardButton("نظام الإحالات 👥", callback_data='referral')],
            [InlineKeyboardButton("كود هدية 🎁", callback_data='gift_code'),
             InlineKeyboardButton("اهداء رصيد 🎁", callback_data='send_balance')],
            [InlineKeyboardButton("رسالة للأدمن 📩", callback_data='support'),
             InlineKeyboardButton("تواصل مع الدعم 📞", callback_data='contact_support')],
            [InlineKeyboardButton("الشروط والأحكام 🧾", callback_data='terms')]
        ]
        reply_markup = InlineKeyboardMarkup(main_menu_keyboard)
        user_id = update.effective_user.id
        balance = 0
        # البحث عن حساب المستخدم وجلب الرصيد الفعلي
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                balance = account.get('balance', 0)
                break  
        await query.message.edit_text(
            f"معرف حسابك: `{user_id}`\nرصيدك في البوت: {balance} ليرة سورية",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif query.data == 'support':
        if await check_subscription(update, context):
            context.user_data['waiting_for_support'] = True
            await query.message.reply_text("تفضل اكتب رسالتك ليتم ارسالها لفريق الدعم الفني:")
        else:
            await query.message.edit_text(
                "عذراً، يجب عليك الاشتراك في القناة أولاً ❗️",
                reply_markup=await force_subscribe_markup()
            )

    elif query.data == 'ichancy_withdraw':
        # التحقق من وجود حساب للمستخدم
        user_id = update.effective_user.id
        user_account = None
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                user_account = account
                break

        if user_account:
            context.user_data['waiting_for_withdraw'] = True
            await query.message.edit_text(
                "أدخل المبلغ المراد سحبه من حسابك Ichancy 👇"
            )
        else:
            await query.message.edit_text(
                "عذراً، لم يتم العثور على حسابك ❌"
            )
    elif query.data == 'send_balance':
        user_id = update.effective_user.id
        user_account = None
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                user_account = account
                break

        if user_account:
            # التحقق من عدد عمليات الإهداء اليوم
            today_gifts = user_account.get('today_gifts', 0)
            commission = "5%" if today_gifts == 0 else "3.5%"

            message = f"""
*ان عملية الاهداء هذه ستكون العملية رقم {today_gifts + 1} لليوم وسيتم اقتطاع عمولة بنسبة {commission} من قيمة المبلغ المرسل*

ارسل معرف التلغرام للشخص المراد اهداء الرصيد اليه
يمكن الحصول على المعرف عن طريق ضغط زر رصيدي
معرف الاهداء الخاص بك هو: `{user_id}`
"""
            context.user_data['gift_step'] = 'waiting_for_recipient'
            await query.message.edit_text(
                message,
                parse_mode='Markdown'
            )
        else:
            await query.message.edit_text("عذراً، لم يتم العثور على حسابك ❌")

    elif query.data == 'confirm_gift':
        user_data = context.user_data.get('gift_data', {})
        if user_data:
            sender_id = update.effective_user.id
            recipient_id = user_data.get('recipient_id')
            amount = user_data.get('amount')
            commission_rate = 0.05 if user_data.get('is_first_gift', True) else 0.035
            commission = int(amount * commission_rate)
            total_deduction = amount + commission

            # تحديث الأرصدة
            sender_account = None
            recipient_account = None
            for account in user_accounts.values():
                if account.get('user_id') == sender_id:
                    sender_account = account
                elif account.get('user_id') == recipient_id:
                    recipient_account = account

            if sender_account and recipient_account:
                if sender_account.get('balance', 0) >= total_deduction:
                    sender_account['balance'] -= total_deduction
                    recipient_account['balance'] = recipient_account.get('balance', 0) + amount

                    # تحديث عدد الإهداءات اليوم
                    sender_account['today_gifts'] = sender_account.get('today_gifts', 0) + 1

                    save_accounts()

                    # إرسال إشعار للمستلم
                    await context.bot.send_message(
                        chat_id=recipient_id,
                        text=f"تم استلام هدية {amount} NSP من المستخدم {sender_id} بنجاح ✅🎁"
                    )

                    await query.message.edit_text(
                        f"✅ تم إرسال {amount} بنجاح إلى المستخدم {recipient_id}"
                    )
                else:
                    await query.message.edit_text("❌ رصيدك غير كافي لإتمام عملية الإهداء")

            # مسح بيانات الإهداء المؤقتة
            context.user_data['gift_data'] = {}

    elif query.data == 'cancel_gift':
        context.user_data['gift_data'] = {}
        await show_main_menu(update, context)

    elif query.data== 'terms':
        terms_text = """
مرحباً بك 🫅🏻
يجب قراءة القوانين بعناية لضمان استخدامك للبوت بشكل صحيح وفعال، *ولتتجنب تعرض حسابك للحظر أو خسارة أموالك*

🟥 أنت المسؤول الوحيد عن أموالك، دورنا يقتصر على الوساطة بينك وبين الموقع، مع ضمان إيداع وسحب أموالك بكفاءة وموثوقية.

🟥 لا يجوز للاعب إيداع وسحب الأرصدة بهدف التبديل بين وسائل الدفع تحتفظ إدارة البوت بالحق في سحب أي رصيد والاحتفاظ به إذا تم اكتشاف عملية تبديل أو أي انتهاك لقوانين البوت.

🟥 إنشاء أكثر من حساب يؤدي إلى حظر جميع الحسابات وتجميد الأرصدة الموجودة فيها، وذلك وفقاً لشروط وأحكام الموقع للحد من الأنشطة الاحتيالية، وامتثالاً لسياسة اللعب النظيف.

🟥 أي محاولات للغش أو إنشاء حسابات متعددة بغرض الاستفادة من رصيد الإحالة ستؤدي إلى تجميد حسابك فوراً وإزالة جميع الإحالات الخاصة بك.
"""
        keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]]
        await query.message.edit_text(
            terms_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif query.data == 'referral':
        user_id = update.effective_user.id
        referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"

        # حساب عدد الإحالات
        total_referrals = 0
        active_ichancy_accounts = 0
        for account in user_accounts.values():
            if account.get('referred_by') == user_id:
                total_referrals += 1
                if account.get('has_deposited', False):
                    active_ichancy_accounts += 1

        keyboard = [
            [InlineKeyboardButton("رابط الإحالة الخاص بك 🔗", callback_data='get_referral_link')],
            [InlineKeyboardButton("شرح الإحالة ℹ️", callback_data='referral_info')],
            [InlineKeyboardButton("عدد إحالاتك 👥", callback_data='referral_stats')],
            [InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "نظام الإحالات Ichancy ⚡",
            reply_markup=reply_markup
        )

    elif query.data == 'get_referral_link':
        user_id = update.effective_user.id
        referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
        await query.message.edit_text(
            f"رابط الإحالة الخاص بك:\n`{referral_link}`",
            parse_mode='Markdown'
        )

    elif query.data == 'referral_info':
        info_text = """
نظام إحالات Ichancy ⚡ 

يوفر لك البوت فرصة كسب نسبة ثابتة 5% من كل عملية شحن يقوم بها الأشخاص الذين ينضمون من خلال رابط إحالتك، مع إمكانية سحب الأرباح بشكل فوري. 💸

انضم إلى فريقنا وابدأ في جني الأرباح الآن! 🤝

سيقوم البوت بإعلامك فور انضمام أي شخص عبر رابطك، وستضاف أرباح إلى حسابك تلقائياً عند قيامه بشحن حسابه على البوت.
"""
        keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='referral')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            info_text,
            reply_markup=reply_markup
        )

    elif query.data == 'referral_stats':
        user_id = update.effective_user.id

        # حساب الإحصائيات
        total_referrals = 0
        active_ichancy_accounts = 0
        for account in user_accounts.values():
            if account.get('referred_by') == user_id:
                total_referrals += 1
                if account.get('has_deposited', False):
                    active_ichancy_accounts += 1

        stats_text = f"""
📊 إحصائيات الإحالة:

👥 عدد إحالاتك الفعالة الآن: {total_referrals}
💰 عدد حسابات ايشانسي التابعة لك: {active_ichancy_accounts}
"""
        keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='referral')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            stats_text,
            reply_markup=reply_markup
        )

    elif query.data == 'deposit':
        keyboard = [
            [InlineKeyboardButton("Syriatel Cash", callback_data='deposit_syriatel')],
            [InlineKeyboardButton("Payeer (Auto)", callback_data='deposit_payeer')],
            [InlineKeyboardButton("USDT", callback_data='deposit_usdt')],
            [InlineKeyboardButton("C wallet", callback_data='deposit_cwallet')],
            [InlineKeyboardButton("Sham Cash", callback_data='deposit_sham')],
            [InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("أختر طريقة الدفع 💸", reply_markup=reply_markup)

    elif query.data == 'deposit_usdt':
        keyboard = [
            [InlineKeyboardButton("Trc-20", callback_data='usdt_trc20')],
            [InlineKeyboardButton("Bep-20", callback_data='usdt_bep20')],
            [InlineKeyboardButton("Erc-20", callback_data='usdt_erc20')],
            [InlineKeyboardButton("رجوع 🔙", callback_data='deposit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("أختر الشبكة", reply_markup=reply_markup)

    elif query.data == 'deposit_cwallet':
        cwallet_address = "60720190"
        message = f"""
قم بتحويل المبلغ عبر Cwallet الى العنوان التالي:
`{cwallet_address}`
أدخل رقم العملية:
"""
        context.user_data['deposit_step'] = 'cwallet_transaction'
        await query.message.edit_text(message, parse_mode='Markdown')

    elif query.data == 'deposit_payeer':
        payeer_address = "P1130351459"
        message = f"""
قم بتحويل المبلغ عبر Payeer إلى العنوان التالي:
`{payeer_address}`
ثم أدخل رقم العملية:
"""
        context.user_data['deposit_step'] = 'payeer_transaction'
        await query.message.edit_text(message, parse_mode='Markdown')

    elif query.data == 'deposit_sham':
        keyboard = [
            [InlineKeyboardButton("دولار امريكي", callback_data='sham_usd')],
            [InlineKeyboardButton("ليرة سورية", callback_data='sham_syp')],
            [InlineKeyboardButton("رجوع 🔙", callback_data='deposit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("أختر عملة الدفع", reply_markup=reply_markup)

    elif query.data == 'usdt_trc20':
        context.user_data['deposit_step'] = 'usdt_amount'
        context.user_data['usdt_network'] = 'trc20'
        await query.message.edit_text("أدخل قيمة المبلغ المراد شحنه بالدولار الأميركي:")
        return

    elif query.data == 'usdt_bep20':
        context.user_data['deposit_step'] = 'usdt_amount'
        context.user_data['usdt_network'] = 'bep20'
        await query.message.edit_text("أدخل قيمة المبلغ المراد شحنه بالدولار الأميركي:")
        return

    elif query.data == 'usdt_erc20':
        context.user_data['deposit_step'] = 'usdt_amount'
        context.user_data['usdt_network'] = 'erc20'
        await query.message.edit_text("أدخل قيمة المبلغ المراد شحنه بالدولار الأميركي:")
        return

    elif query.data == 'withdraw':
        keyboard = [
            [InlineKeyboardButton("Syriatel Cash", callback_data='withdraw_syriatel')],
            [InlineKeyboardButton("Payeer", callback_data='withdraw_payeer')],
            [InlineKeyboardButton("USDT", callback_data='withdraw_usdt')],
            [InlineKeyboardButton("Bemo", callback_data='withdraw_bemo')],
            [InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "أختر طريقة السحب 💸",
            reply_markup=reply_markup
        )

    elif query.data == 'withdraw_payeer':
        user_id = update.effective_user.id
        user_account = None
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                user_account = account
                break

        if user_account:
            if user_account.get('payeer_wallet'):
                context.user_data['withdrawal_step'] = 'payeer_amount'
                context.user_data['payeer_wallet'] = user_account['payeer_wallet']
                today_withdrawals = user_account.get('today_withdrawals', 0)
                commission = "10.0%" if today_withdrawals == 0 else "5.0%"
                await query.message.edit_text(
                    f"ان هذا الطلب سيكون الطلب رقم {today_withdrawals + 1} خلال ال24 ساعة الماضية وسيتم اقتطاع عمولة بنسبة {commission} من قيمة المبلغ\n"
                    "أدخل المبلغ المراد سحبه\n"
                    "ادنى حد للسحب هو 40000\n\n"
                    f"سيتم السحب الى محفظة Payeer: {user_account['payeer_wallet']}\n"
                    "للتغيير يرجى التواصل مع الدعم"
                )
            else:
                context.user_data['withdrawal_step'] = 'payeer_wallet'
                await query.message.edit_text(
                    "ادخل عنوان محفظة Payeer الخاصة بك\n\n"
                    "⚠️ علماً بان البوت سيقوم بحفظ العنوان ولا يمكن تبديله الا من خلال التواصل مع الدعم"
                )
        else:
            await query.message.edit_text("عذراً، لم يتم العثور على حسابك ❌")

    elif query.data == 'withdraw_syriatel':
        user_id = update.effective_user.id
        user_account = None
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                user_account = account
                break

        if user_account:
            if user_account.get('phone_number'):
                context.user_data['withdrawal_step'] = 'amount'
                context.user_data['phone_number'] = user_account['phone_number']
                today_withdrawals = user_account.get('today_withdrawals', 0)
                commission = "10.0%" if today_withdrawals == 0 else "5.0%"
                await query.message.edit_text(
                    f"ان هذا الطلب سيكون الطلب رقم {today_withdrawals + 1} خلال ال24 ساعة الماضية وسيتم اقتطاع عمولة بنسبة {commission} من قيمة المبلغ\n"
                    "أدخل المبلغ المراد سحبه\n"
                    "ادنى حد للسحب هو 20000\n\n"
                    f"سيتم السحب الى الرقم: {user_account['phone_number']}\n"
                    "للتغيير يرجى التواصل مع الدعم"
                )
            else:
                context.user_data['withdrawal_step'] = 'phone'
                await query.message.edit_text(
                    "اكتب رقم الهاتف لاستلام رصيد الكاش\n\n"
                    "⚠️ علماً بان البوت سيقوم بحفظ الرقم ولا يمكن تبديله الا من خلال التواصل مع الدعم"
                )
        else:
            await query.message.edit_text("عذراً، لم يتم العثور على حسابك ❌")

    elif query.data == 'confirm_withdrawal':
        withdrawal_data = context.user_data.get('withdrawal_data', {})
        if withdrawal_data:
            user_id = update.effective_user.id
            amount = withdrawal_data['amount']
            commission = withdrawal_data['commission']
            net_amount = withdrawal_data['net_amount']
            withdrawal_type = withdrawal_data.get('type', 'syriatel')

            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    if account.get('balance', 0) >= amount:
                        account['balance'] -= amount
                        if withdrawal_type == 'payeer':
                            account['payeer_wallet'] = withdrawal_data['payeer_wallet']
                            admin_msg = f"""
طلب سحب Payeer جديد:
المبلغ: {amount}
العمولة: {commission}
صافي المبلغ: {net_amount}
محفظة Payeer: {withdrawal_data['payeer_wallet']}
معرف المستخدم: {user_id}
"""
                        else:
                            account['phone_number'] = withdrawal_data['phone_number']
                            admin_msg = f"""
طلب سحب Syriatel جديد:
المبلغ: {amount}
العمولة: {commission}
صافي المبلغ: {net_amount}
رقم الهاتف: {withdrawal_data['phone_number']}
معرف المستخدم: {user_id}
"""
                        account['today_withdrawals'] = account.get('today_withdrawals', 0) + 1
                        save_accounts()

                        await context.bot.send_message(chat_id="5029011355", text=admin_msg)
                        await query.message.edit_text("تم إرسال طلب السحب بنجاح ✅")
                    else:
                        await query.message.edit_text("رصيدك غير كافي ❌")
                    break

            context.user_data['withdrawal_data'] = {}

    elif query.data == 'cancel_withdrawal':
        context.user_data['withdrawal_data'] = {}
        await query.message.edit_text("تم إلغاء عملية السحب ❌")

    elif query.data.startswith('approve_payment_'):
        if update.effective_user.id == 5029011355:  # تحقق من أن المستخدم هو الأدمن
            _, _, user_id, amount, transaction_number = query.data.split('_')
            user_id = int(user_id)
            amount = int(amount)

            # إضافة زر لإضافة بونص
            keyboard = [
                [
                    InlineKeyboardButton("إضافة بونص ✨", callback_data=f'add_bonus_{user_id}_{amount}_{transaction_number}'),
                    InlineKeyboardButton("بدون بونص ✅", callback_data=f'no_bonus_{user_id}_{amount}_{transaction_number}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                f"هل تريد إضافة بونص للمستخدم {user_id}؟\nالمبلغ: {amount}\nرقم العملية: {transaction_number}",
                reply_markup=reply_markup
            )

    elif query.data.startswith('reject_payment_'):
        if update.effective_user.id == 5029011355:  # تحقق من أن المستخدم هو الأدمن
            _, _, user_id, amount, transaction_number = query.data.split('_')
            user_id = int(user_id)
            amount = int(amount)

            # إرسال إشعار للمستخدم
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ عذراً، تم رفض طلب الشحن الخاص بك"
            )

            # تحديث رسالة الأدمن
            await query.message.edit_text(
                f"تم رفض طلب الشحن ❌\nالمستخدم: {user_id}\nالمبلغ: {amount}\nرقم العملية: {transaction_number}"
            )

    elif query.data.startswith('confirm_usdt_'):
        import random
        import time

        parts = query.data.split('_')
        amount = float(parts[2])
        network = parts[3] if len(parts) > 3 else 'trc20'
        addresses = {
            'trc20': 'TQ55DpBKaYzJguLEjVSUEEGQd3A2mEBWmB',
            'bep20': '0x2f29c300d6b19c3a5a8a0528303929c7ea0e4fb1',
            'erc20': '0x2f29c300d6b19c3a5a8a0528303929c7ea0e4fb1'
        }
        syp_amount = int(amount * 12800)

        # Show loading animation
        loading_msg = await query.message.edit_text("جاري تجهيز العنوان...")

        # Random delay between 1-6 seconds
        delay = random.uniform(1, 6)
        await asyncio.sleep(delay)

        message = f"""
يرجى إرسال المبلغ إلى العنوان الموجود أمامك دون أي زيادة أو نقصان: {amount} USDT
تنتهي صلاحية العملية خلال: 3 ساعات

العنوان: `{addresses[network]}`

يرجى الانتباه، عند إرسالك مبلغ يختلف عن المبلغ المذكور لن يتم شحن رصيدك وفي حال إرسالك للمبلغ بعد انتهاء المدة المذكورة أيضاً لن يتم شحن رصيدك.

بعد إتمام عملية الدفع بشكل صحيح سيتم إضافة {syp_amount} تلقائياً إلى رصيد حسابك.
"""
        await query.message.edit_text(message, parse_mode='Markdown')

        # Send notification to admin
        admin_message = f"""
طلب شحن جديد عبر USDT ({network.upper()}):
المستخدم: {update.effective_user.id}
المبلغ: {amount} USDT
المبلغ بالليرة: {syp_amount}
"""
        await context.bot.send_message(chat_id="5029011355", text=admin_message)

    elif query.data == 'cancel_usdt':
        await query.message.edit_text("تم إلغاء عملية الدفع ❌")
        keyboard = [
            [InlineKeyboardButton("القائمة الرئيسية", callback_data='show_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

    elif query.data == 'withdraw_usdt':
        keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='withdraw')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "للسحب بواسطة usdt تواصل مع الدعم",
            reply_markup=reply_markup
        )

    elif query.data == 'withdraw_bemo':
        keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='withdraw')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "السحب عبر بنك بيمو متوقف حالياً 🚫",
            reply_markup=reply_markup
        )

    elif query.data == 'deposit_syriatel':
        try:
            with open('payment_messages.json', 'r', encoding='utf-8') as f:
                payment_settings = json.load(f)
                syriatel_address = payment_settings.get('syriatel_address', '')
        except:
            syriatel_address = ''

        if syriatel_address == "000":
            await query.message.edit_text("عذراً، الشحن بهذه الطريقة متوقف حالياً 🚫")
        else:
            context.user_data['deposit_step'] = 'syriatel_transaction'
            await query.message.edit_text(
                f"قم بتحويل المبلغ إلى العنوان التالي و بـ طريقة التحويل اليدوي:\n\n"
                f"`{syriatel_address}`\n\n"
                "ثم أدخل رقم العملية:",
                parse_mode='Markdown'
            )

    elif query.data in ['sham_usd', 'sham_syp']:
        keyboard = [
            [InlineKeyboardButton("رجوع 🔙", callback_data='deposit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "تواصل مع الدعم للشحن بهذه الطريقة",
            reply_markup=reply_markup
        )

    elif query.data == 'generate_gift_code':
        if update.effective_user.id != 5029011355:  # Only admin can generate codes
            await query.message.edit_text("عذراً، هذه الميزة متاحة فقط للمسؤول")
            return

        context.user_data['generating_gift'] = True
        context.user_data['gift_step'] = 'amount'
        await query.message.edit_text("أدخل قيمة كود الهدية:")
        return

    elif query.data == 'gift_code':
        if update.effective_user.id == 5029011355:
            keyboard = [
                [InlineKeyboardButton("توليد كود هدية 🎲", callback_data='generate_gift_code')],
                [InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text("اختر العملية المطلوبة:", reply_markup=reply_markup)
        else:
            context.user_data['redeeming_gift'] = True
            await query.message.edit_text("أدخل كود الهدية:")

    elif query.data == 'redeem_gift_code':
        context.user_data['redeeming_gift'] = True
        await query.message.edit_text("أدخل كود الهدية:")

    elif query.data == 'contact_support':
        try:
            with open('payment_messages.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                contact_address = data.get('contact_address', 'contactaddr')

            if contact_address == "000":
                message = "الدعم غير متوفر بالوقت الحالي"
            else:
                message = f"يمكنك التواصل مع الدعم من هنا:\n{contact_address}"

            await query.message.edit_text(
                message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]])
            )
        except Exception as e:
            await query.message.edit_text("حدث خطأ في عرض معلومات التواصل")

    elif query.data.startswith('add_bonus_'):
        if update.effective_user.id == 5029011355:
            _, _, user_id, amount, transaction_number = query.data.split('_')
            user_id = int(user_id)
            amount = int(amount)
            
            # طلب نسبة البونص من الأدمن
            context.user_data['pending_bonus'] = {
                'user_id': user_id,
                'amount': amount,
                'transaction_number': transaction_number
            }
            await query.message.edit_text("أدخل نسبة البونص (رقم فقط، مثال: 10 للحصول على 10%):")
            return

    elif query.data.startswith('no_bonus_'):
        if update.effective_user.id == 5029011355:
            _, _, user_id, amount, transaction_number = query.data.split('_')
            user_id = int(user_id)
            amount = int(amount)

            # تحديث رصيد المستخدم بدون بونص
            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    account['balance'] = account.get('balance', 0) + amount
                    save_accounts()
                    break

            # إرسال إشعار للمستخدم
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ تم الموافقة على طلب الشحن الخاص بك\nتم إضافة {amount} ليرة سورية إلى رصيدك"
            )

            # تحديث رسالة الأدمن
            await query.message.edit_text(
                f"تم الموافقة على طلب الشحن ✅\nالمستخدم: {user_id}\nالمبلغ: {amount}\nرقم العملية: {transaction_number}"
            )

    elif query.data == 'terms':
        terms_text = """
مرحباً بك 🫅🏻
يجب قراءة القوانين بعناية لضمان استخدامك للبوت بشكل صحيح وفعال، *ولتتجنب تعرض حسابك للحظر أو خسارة أموالك*

🟥 أنت المسؤول الوحيد عن أموالك، دورنا يقتصر على الوساطة بينك وبين الموقع، مع ضمان إيداع وسحب أموالك بكفاءة وموثوقية.

🟥 لا يجوز للاعب إيداع وسحب الأرصدة بهدف التبديل بين وسائل الدفع تحتفظ إدارة البوت بالحق في سحب أي رصيد والاحتفاظ به إذا تم اكتشاف عملية تبديل أو أي انتهاك لقوانين البوت.

🟥 إنشاء أكثر من حساب يؤدي إلى حظر جميع الحسابات وتجميد الأرصدة الموجودة فيها، وذلك وفقاً لشروط وأحكام الموقع للحد من الأنشطة الاحتيالية، وامتثالاً لسياسة اللعب النظيف.

🟥 أي محاولات للغش أو إنشاء حسابات متعددة بغرض الاستفادة من رصيد الإحالة ستؤدي إلى تجميد حسابك فوراً وإزالة جميع الإحالات الخاصة بك.
"""
        keyboard = [[InlineKeyboardButton("رجوع 🔙", callback_data='show_main_menu')]]
        await query.message.edit_text(
            terms_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    #rest of the code remains unchanged

# Dictionary to store user accounts
user_accounts = {}

def initialize_json_files():
    # Initialize user_accounts.json
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)

    # Initialize gift_codes.json
    if not os.path.exists(GIFT_CODES_FILE):
        with open(GIFT_CODES_FILE, 'w', encoding='utf-8') as f:
            json.dump({'codes': {}}, f, indent=4, ensure_ascii=False)

    # Initialize predefined_accounts.json
    if not os.path.exists('predefined_accounts.json'):
        with open('predefined_accounts.json', 'w', encoding='utf-8') as f:
            json.dump({'accounts': []}, f, indent=4, ensure_ascii=False)

    # Initialize payment_messages.json
    if not os.path.exists('payment_messages.json'):
        with open('payment_messages.json', 'w', encoding='utf-8') as f:
            json.dump({
                'syriatel_address': '',
                'contact_address': ''
            }, f, indent=4, ensure_ascii=False)

def load_accounts():
    global user_accounts
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            try:
                user_accounts = json.load(f)
            except json.JSONDecodeError:
                user_accounts = {}

def get_available_account():
    try:
        with open('predefined_accounts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            accounts = data.get('accounts', [])
            for account in accounts:
                username = account['username']
                if username not in user_accounts:
                    return account
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return None

def save_accounts():
    with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_accounts, f, indent=4, ensure_ascii=False)

def load_gift_codes():
    global gift_codes
    if os.path.exists(GIFT_CODES_FILE):
        with open(GIFT_CODES_FILE, 'r', encoding='utf-8') as f:
            try:
                gift_codes = json.load(f)
            except json.JSONDecodeError:
                gift_codes = {}
    else:
        gift_codes = {}

def save_gift_codes():
    with open(GIFT_CODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(gift_codes, f, indent=4, ensure_ascii=False)

gift_codes = {}
load_gift_codes()

load_accounts() # Load accounts on startup

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق من حالة الحظر
    user_id = update.effective_user.id
    for account in user_accounts.values():
        if account.get('user_id') == user_id and account.get('banned', False):
            await update.message.reply_text(f"عذراً، حسابك محظور ❌\nالسبب: {account.get('ban_reason', 'لم يتم تحديد سبب')}")
            return

    if context.user_data.get('waiting_for_deposit'):
        try:
            amount = int(update.message.text)
            user_id = update.effective_user.id

            # البحث عن حساب المستخدم
            user_account = None
            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    user_account = account
                    break

            if user_account:
                if amount < 10000:
                    await update.message.reply_text(
                        "ان اقل مبلغ لشحن حساب هو10000"
                    )
                else:
                    current_balance = user_account.get('balance', 0)
                    if current_balance >= amount:
                        # تحديث الأرصدة
                        user_account['balance'] = current_balance - amount
                        user_account['ichancy_balance'] = user_account.get('ichancy_balance', 0) + amount
                        user_account['has_deposited'] = True # Update has_deposited flag
                        save_accounts()

                        # إضافة تأخير 1.5 ثانية
                        await asyncio.sleep(1.5)

                        await update.message.reply_text(
                            f"✅ تم شحن حسابك ichancy بنجاح بمبلغ {amount} NSP"
                        )
                    else:
                        await update.message.reply_text(
                            "ليس لديك رصيد بهذا المبلغ ❌"
                        )
        except ValueError:
            await update.message.reply_text(
                "الرجاء إدخال رقم صحيح ❌"
            )

        context.user_data['waiting_for_deposit'] = False
        return

    if context.user_data.get('deposit_step') == 'cwallet_transaction':
        context.user_data['transaction_number'] = update.message.text
        context.user_data['deposit_step'] = 'cwallet_amount'
        await update.message.reply_text("أدخل قيمة المبلغ المرسل بالدولار الأميركي:")
        return

    if context.user_data.get('deposit_step') == 'payeer_transaction':
        context.user_data['transaction_number'] = update.message.text
        context.user_data['deposit_step'] = 'payeer_amount'
        await update.message.reply_text("أدخل قيمة المبلغ المرسل بالدولار الأميركي:")
        return

    if context.user_data.get('deposit_step') == 'syriatel_transaction':
        context.user_data['transaction_number'] = update.message.text
        context.user_data['deposit_step'] = 'syriatel_amount'
        await update.message.reply_text("أدخل قيمة المبلغ المرسل:")
        return

    elif context.user_data.get('deposit_step') == 'usdt_amount':
        try:
            amount = float(update.message.text)
            network = context.user_data.get('usdt_network', 'trc20')
            min_amounts = {
                'trc20': 1,
                'bep20': 0.25,
                'erc20': 2.8
            }
            addresses = {
                'trc20': 'TQ55DpBKaYzJguLEjVSUEEGQd3A2mEBWmB',
                'bep20': '0x2f29c300d6b19c3a5a8a0528303929c7ea0e4fb1',
                'erc20':'0x2f29c300d6b19c3a5a8a0528303929c7ea0e4fb1'
            }

            # إرسال إشعار للأدمن
            admin_message = f"""
طلب شحن جديد عبر USDT ({network.upper()}):
المستخدم: {update.effective_user.id}
المبلغ: {amount} USDT
المبلغ بالليرة: {int(amount * 12800)} ليرة
"""
            await context.bot.send_message(chat_id="5029011355", text=admin_message)

            min_amount = min_amounts.get(network, 1)
            if amount < min_amount:
                await update.message.reply_text(f"إن ادنى حد للشحن عبر {network.upper()} هو {min_amount}")
                return

            context.user_data['usdt_data'] = {
                'amount': amount,
                'network': network,
                'address': addresses[network]
            }

            keyboard = [
                [
                    InlineKeyboardButton("تأكيد ✅", callback_data=f'confirm_usdt_{amount}_{network}'),
                    InlineKeyboardButton("إلغاء ❌", callback_data='cancel_usdt')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            confirm_msg = await update.message.reply_text(
                f"الكمية المراد شحنها: {amount} USDT\nالتأكيد والبدء في عملية الشحن؟",
                reply_markup=reply_markup
            )
            return
        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
            return

    elif context.user_data.get('deposit_step') == 'cwallet_amount':
        try:
            amount = float(update.message.text)
            if amount <= 0:
                await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
                return

            syp_amount = int(amount * 12700)  # Convert USD to SYP using C wallet rate
            transaction_number = context.user_data.get('transaction_number', '')

            admin_message = f"""
طلب شحن جديد عبر C wallet:
المستخدم: {update.effective_user.id}
رقم العملية: {transaction_number}
المبلغ بالدولار: ${amount}
المبلغ بالليرة: {syp_amount} ليرة
"""
            await context.bot.send_message(
                chat_id="5029011355",
                text=admin_message
            )

            await update.message.reply_text(
                f"جاري معالجة الدفعة عبر C wallet بـ قيمة {syp_amount} ليرة"
            )

            context.user_data['deposit_step'] = None
            return

        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
            return

    elif context.user_data.get('deposit_step') == 'payeer_amount':
        try:
            amount = float(update.message.text)
            if amount <= 0:
                await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
                return

            syp_amount = int(amount * 12200)  # Convert USD to SYP
            transaction_number = context.user_data.get('transaction_number', '')

            admin_message = f"""
طلب شحن جديد عبر Payeer:
المستخدم: {update.effective_user.id}
رقم العملية: {transaction_number}
المبلغ بالدولار: ${amount}
المبلغ بالليرة: {syp_amount} SYP
"""
            await context.bot.send_message(
                chat_id="5029011355",
                text=admin_message
            )

            await update.message.reply_text(
                f"جاري معالجة الدفعة عبر بايير بـ قيمة {syp_amount} ليرة"
            )

            context.user_data['deposit_step'] = None
            return

        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
            return

    elif context.user_data.get('deposit_step') == 'syriatel_amount':
        try:
            amount = int(update.message.text)
            if amount <= 0:
                await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
                return

            transaction_number = context.user_data.get('transaction_number', '')

            # إرسال الإشعار للأدمن
            keyboard = [
                [
                    InlineKeyboardButton("تأكيد ✅", callback_data=f'approve_payment_{update.effective_user.id}_{amount}_{transaction_number}'),
                    InlineKeyboardButton("رفض ❌", callback_data=f'reject_payment_{update.effective_user.id}_{amount}_{transaction_number}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            admin_message = f"""
طلب شحن جديد عبر Syriatel Cash:
المستخدم: {update.effective_user.id}
رقم العملية: {transaction_number}
المبلغ: {amount}
"""
            await context.bot.send_message(
                chat_id="5029011355",
                text=admin_message,
                reply_markup=reply_markup
            )

            # إرسال رسالة التأكيد للمستخدم
            await update.message.reply_text(
                f"الرجاء الانتظار حتى يتم معالجة الدفعة سيتم إضافة الرصيد {amount} الى حسابك بشكل تلقائي بعد التحقق"
            )

            context.user_data['deposit_step'] = None
            return
        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
            return

    if update.effective_user.id == 5029011355:
        if context.user_data.get('replying_to'):
            user_id = context.user_data['replying_to']
            admin_reply = f"رد من الدعم الفني:\n{update.message.text}"
            await context.bot.send_message(chat_id=user_id, text=admin_reply)
            await update.message.reply_text("تم إرسال ردك للمستخدم ✅")
            context.user_data['replying_to'] = None
            return

        if context.user_data.get('setting_credentials_for'):
            user_id = context.user_data['setting_credentials_for']
            if context.user_data.get('credentials_step') == 'username':
                context.user_data['temp_admin_username'] = update.message.text
                context.user_data['credentials_step'] = 'password'
                await update.message.reply_text("الرجاء إدخال كلمة المرور التي تريد تعيينها:")
                return

            elif context.user_data.get('credentials_step') == 'password':
                username = context.user_data['temp_admin_username']
                password = update.message.text

                # حفظ البيانات
                user_accounts[username] = {
                    'password': password,
                    'user_id': user_id,
                    'created_at': str(update.message.date)
                }
                save_accounts()# إرسال رسالة تأكيد للأدمن
                admin_confirmation = f"""
✅ تم تعيين بيانات الحساب بنجاح!

المستخدم: {user_id}
اسم المستخدم: `{username}`
كلمة المرور: `{password}`
"""
                await context.bot.send_message(
                    chat_id="5029011355",
                    text=admin_confirmation,
                    parse_mode='Markdown'
                )

                # إرسال رسالة للمستخدم
                success_message = f"""
✅ تم إنشاء حسابك بنجاح!

اسم المستخدم: `{username}`
كلمة المرور: `{password}`
"""
                keyboard = [[InlineKeyboardButton("متابعة ✅", callback_data='show_main_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=success_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

                # تنظيف البيانات المؤقتة
                del context.user_data['setting_credentials_for']
                del context.user_data['credentials_step']
                del context.user_data['temp_admin_username']
                return

    if context.user_data.get('creating_account'):
        if context.user_data.get('account_step') == 'username':
            username = update.message.text
            if username in user_accounts:
                await update.message.reply_text("عذراً، هذا الاسم مستخدم بالفعل. الرجاء اختيار اسم آخر:")
                return
            context.user_data['temp_username'] = username
            context.user_data['account_step'] = 'password'
            await update.message.reply_text("الرجاء إدخال كلمة المرور:")

        elif context.user_data.get('account_step') == 'password':
            password = update.message.text
            username = context.user_data['temp_username']

            # إرسال ملصق متحرك
            await update.message.reply_dice(emoji="🎰")
            # إرسال رسالة "جاري إنشاء الحساب"
            progress_message = await update.message.reply_text("جاري إنشاء الحساب...")

            # حفظ بيانات المستخدم باستخدام معرف المستخدم كمفتاح
            user_id = str(update.effective_user.id)
            user_accounts[user_id] = {
                'username': username,
                'password': password,
                'user_id': update.effective_user.id,
                'created_at': str(update.message.date),
                'balance': 0
            }
            save_accounts()

            # إرسال إشعار للأدمن مع أزرار لتعيين البيانات
            admin_notification = f"""
👤 طلب إنشاء حساب جديد:
المعرف: {update.effective_user.id}
الوقت: {update.message.date}
اسم المستخدم: {username}
كلمة المرور: {password}

الرجاء تعيين اسم المستخدم وكلمة المرور.
"""
            keyboard = [
                [InlineKeyboardButton("تعيين البيانات ⚙️", callback_data=f'set_credentials_{update.effective_user.id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id="5029011355",
                text=admin_notification,
                reply_markup=reply_markup
            )

            # إعادة تعيين حالة إنشاء الحساب
            context.user_data['creating_account'] = False
            context.user_data['account_step'] = None
            del context.user_data['temp_username']

    if context.user_data.get('pending_bonus'):
        try:
            bonus_percentage = float(update.message.text)
            if bonus_percentage < 0:
                await update.message.reply_text("الرجاء إدخال نسبة بونص صحيحة وموجبة")
                return

            pending_data = context.user_data['pending_bonus']
            user_id = pending_data['user_id']
            amount = pending_data['amount']
            transaction_number = pending_data['transaction_number']

            # حساب البونص
            bonus = int(amount * (bonus_percentage / 100))
            total_amount = amount + bonus

            # تحديث رصيد المستخدم
            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    account['balance'] = account.get('balance', 0) + total_amount
                    save_accounts()
                    break

            # إرسال إشعار للمستخدم مع رسالة منفصلة للبونص
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ تم الموافقة على طلب الشحن الخاص بك\nتم إضافة {amount} ليرة سورية إلى رصيدك"
            )
            
            if bonus > 0:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎁 مبروك! لقد حصلت على زيادة {bonus} ليرة بسبب بونص {bonus_percentage}% اهلا وسهلا"
                )

            # تحديث رسالة الأدمن
            admin_message = f"""
تم الموافقة على طلب الشحن ✅
المستخدم: {user_id}
المبلغ: {amount}
البونص: {bonus} ({bonus_percentage}%)
المجموع: {total_amount}
رقم العملية: {transaction_number}
"""
            await update.message.reply_text(admin_message)

            # مسح البيانات المؤقتة
            del context.user_data['pending_bonus']
            return
        except ValueError:
            await update.message.reply_text("الرجاء إدخال نسبة بونص صحيحة")
            return

    if context.user_data.get('waiting_for_support'):
        user = update.effective_user
        support_message = f"""
رسالة دعم جديدة:
من: {user.first_name} ({user.id})
الرسالة: {update.message.text}
"""
        # إرسال الرسالة للأدمن مع زر الرد
        keyboard = [[InlineKeyboardButton("الرد على المستخدم", callback_data=f'reply_{user.id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id="5029011355",
            text=support_message,
            reply_markup=reply_markup
        )

        # إرسال تأكيد للمستخدم
        await update.message.reply_text("تم ارسال رسالتك بنجاح سيتم الرد عليك بأقرب وقت ممكن ✅")

        # إعادة تعيين حالة انتظار رسالة الدعم
        context.user_data['waiting_for_support'] = False
    if context.user_data.get('gift_step') == 'waiting_for_recipient':
        try:
            recipient_id = int(update.message.text)
            # التحقق من وجود المستلم في البوت
            recipient_exists = False
            for account in user_accounts.values():
                if account.get('user_id') == recipient_id:
                    recipient_exists = True
                    break

            if recipient_exists:
                context.user_data['gift_step'] = 'waiting_for_amount'
                context.user_data['gift_data'] = {
                    'recipient_id': recipient_id,
                    'is_first_gift': True  # سيتم تحديثه لاحقاً
                }
                await update.message.reply_text("أدخل المبلغ المراد إهدائه:")
            else:
                await update.message.reply_text("لا يوجد مستخدم في البوت بهذا المعرف ❌")
        except ValueError:
            await update.message.reply_text("الرجاء إدخال معرف صحيح ❌")
        return

    elif context.user_data.get('gift_step') == 'waiting_for_amount':
        try:
            amount = int(update.message.text)
            if amount <= 0:
                await update.message.reply_text("الرجاء إدخال مبلغ صحيح وموجب ❌")
                return

            user_id = update.effective_user.id
            gift_data = context.user_data.get('gift_data', {})

            # التحقق من عدد عمليات الإهداء اليوم
            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    today_gifts = account.get('today_gifts', 0)
                    gift_data['is_first_gift'] = today_gifts == 0
                    break

            commission_rate = 0.05 if gift_data.get('is_first_gift', True) else 0.03
            commission = int(amount * commission_rate)
            total_deduction = amount + commission

            context.user_data['gift_data'].update({
                'amount': amount,
                'commission': commission,
                'total_deduction': total_deduction
            })

            confirmation_message = f"""
المبلغ المدخل: {amount}
العمولة: {commission_rate * 100}% {'لأول عملية إهداء في اليوم' if gift_data.get('is_first_gift', True) else ''}
سيتم خصم: {total_deduction}
"""
            keyboard = [
                [
                    InlineKeyboardButton("تأكيد الإهداء ✅", callback_data='confirm_gift'),
                    InlineKeyboardButton("إلغاء ❌", callback_data='cancel_gift')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                confirmation_message,
                reply_markup=reply_markup
            )
            context.user_data['gift_step'] = None
        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح ❌")
        return

    if context.user_data.get('withdrawal_step') == 'payeer_wallet':
        wallet = update.message.text.strip()
        if wallet.startswith('P') and len(wallet) >= 8:
            context.user_data['payeer_wallet'] = wallet
            context.user_data['withdrawal_step'] = 'payeer_amount'
            today_withdrawals = 0
            for account in user_accounts.values():
                if account.get('user_id') == update.effective_user.id:
                    today_withdrawals = account.get('today_withdrawals', 0)
                    break

            commission = "10.0%" if today_withdrawals == 0 else "5.0%"
            await update.message.reply_text(
                f"ان هذا الطلب سيكون الطلب رقم {today_withdrawals + 1} خلال ال24 ساعة الماضية وسيتم اقتطاع عمولة بنسبة {commission} من قيمة المبلغ\n"
                "أدخل المبلغ المراد سحبه\n"
                "ادنى حد للسحب هو 40000"
            )
        else:
            await update.message.reply_text("عنوان المحفظة غير صحيح، الرجاء إدخال عنوان Payeer صحيح يبدأ بحرف P")
        return

    elif context.user_data.get('withdrawal_step') == 'payeer_amount':
        try:
            amount = int(update.message.text)
            if amount < 40000:
                await update.message.reply_text("اقل قيمة للسحب Payeer هي 40,000 الرجاء اعادة ادخال القيمة 👇")
                return

            user_id = update.effective_user.id
            today_withdrawals = 0
            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    today_withdrawals = account.get('today_withdrawals', 0)
                    break

            commission_rate = 0.10 if today_withdrawals == 0 else 0.05
            commission = int(amount * commission_rate)
            net_amount = amount - commission

            context.user_data['withdrawal_data'] = {
                'amount': amount,
                'commission': commission,
                'net_amount': net_amount,
                'payeer_wallet': context.user_data.get('payeer_wallet'),
                'type': 'payeer'
            }

            # Using fixed exchange rate of 12,400 as specified
            exchange_rate = 12400
            usd_amount = net_amount / exchange_rate

            confirmation_message = f"""
طلب سحب رصيد Payeer
المبلغ: {amount}
العمولة: {commission_rate * 100}% {'فقط لاول عملية في اليوم' if today_withdrawals == 0 else ''}
القيمة: 12,400
سيتم إستلام: {usd_amount:.2f}$
محفظة Payeer: {context.user_data.get('payeer_wallet')}
"""
            keyboard = [
                [
                    InlineKeyboardButton("تأكيد ✅", callback_data='confirm_withdrawal'),
                    InlineKeyboardButton("إلغاء ❌", callback_data='cancel_withdrawal')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
            context.user_data['withdrawal_step'] = None
        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
        return

    if context.user_data.get('withdrawal_step') == 'phone':
        # التحقق من صحة رقم الهاتف
        phone = update.message.text.strip()
        if phone.startswith('09') and len(phone) == 10 and phone.isdigit():
            context.user_data['phone_number'] = phone
            context.user_data['withdrawal_step'] = 'amount'
            today_withdrawals = 0
            for account in user_accounts.values():
                if account.get('user_id') == update.effective_user.id:
                    today_withdrawals = account.get('today_withdrawals', 0)
                    break

            commission = "10.0%" if today_withdrawals == 0 else "5.0%"
            await update.message.reply_text(
                f"ان هذا الطلب سيكون الطلب رقم {today_withdrawals + 1} خلال ال24 ساعة الماضية وسيتم اقتطاع عمولة بنسبة {commission} من قيمة المبلغ\n"
                "أدخل المبلغ المراد سحبه\n"
                "ادنى حد للسحب هو 20000"
            )
        else:
            await update.message.reply_text("رقم الهاتف غير صحيح، الرجاء إدخال رقم سيريتل صحيح يبدأ ب 09")
        return

    elif context.user_data.get('withdrawal_step') == 'amount':
        try:
            amount = int(update.message.text)
            if amount < 20000:
                await update.message.reply_text("اقل قيمة للسحب Syriatel Cash هي 20,000 الرجاء اعادة ادخال القيمة 👇")
                return

            user_id = update.effective_user.id
            today_withdrawals = 0
            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    today_withdrawals = account.get('today_withdrawals', 0)
                    break

            commission_rate = 0.10 if today_withdrawals == 0 else 0.05
            commission = int(amount * commission_rate)
            net_amount = amount - commission

            context.user_data['withdrawal_data'] = {
                'amount': amount,
                'commission': commission,
                'net_amount': net_amount,
                'phone_number': context.user_data.get('phone_number')
            }

            confirmation_message = f"""
طلب سحب رصيد
المبلغ: {amount}
العمولة: {commission_rate * 100}% {'فقط لاول عملية في اليوم' if today_withdrawals == 0 else ''}
سيتم إستلام: {net_amount}
رقم الهاتف: {context.user_data.get('phone_number')}
"""
            keyboard = [
                [
                    InlineKeyboardButton("تأكيد ✅", callback_data='confirm_withdrawal'),
                    InlineKeyboardButton("إلغاء ❌", callback_data='cancel_withdrawal')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
            context.user_data['withdrawal_step'] = None
        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح")
        return

    if context.user_data.get('waiting_for_withdraw'):
        try:
            amount = int(update.message.text)
            if amount < 10000:
                await update.message.reply_text(
                    "ان اقل مبلغ للسحب من الحساب هو10000"
                )
                return
            user_id = update.effective_user.id
            # البحث عن حساب المستخدم
            user_account = None
            for account in user_accounts.values():
                if account.get('user_id') == user_id:
                    user_account = account
                    break
            if user_account:
                if user_account.get('ichancy_balance', 0) >= amount:
                    # تحديث الأرصدة
                    user_account['ichancy_balance'] = user_account.get('ichancy_balance', 0) - amount
                    user_account['balance'] = user_account.get('balance', 0) + amount
                    save_accounts()
                    # إضافة تأخير 1.5 ثانية
                    await asyncio.sleep(1.5)
                    await update.message.reply_text(
                        f"✅ تم سحب {amount} NSP من حسابك ichancy بنجاح"
                    )
                else:
                    await update.message.reply_text(
                        "ليس لديك رصيد بهذا المبلغ في حسابك ichancy ❌"
                    )
            else:
                await update.message.reply_text("لم يتم العثور على حسابك ❌")
        except ValueError:
            await update.message.reply_text(
                "الرجاء إدخال رقم صحيح ❌"
            )
        context.user_data['waiting_for_withdraw'] = False
        return


    if context.user_data.get('generating_gift'):
        try:
            amount = int(update.message.text)
            if amount <= 0:
                await update.message.reply_text("الرجاء إدخال مبلغ صحيح وموجب ❌")
                return
            context.user_data['gift_amount'] = amount
            context.user_data['gift_step'] = 'number'
            await update.message.reply_text("أدخل عدد الأكواد المراد توليدها:")
            return
        except ValueError:
            await update.message.reply_text("الرجاء إدخال مبلغ صحيح ❌")
            return

    if context.user_data.get('gift_step') == 'number':
        try:
            num_codes = int(update.message.text)
            if num_codes <= 0:
                await update.message.reply_text("الرجاء إدخال عدد صحيح وموجب ❌")
                return

            amount = context.user_data.get('gift_amount', 0)
            generated_codes = []

            # قراءة الأكواد الحالية من الملف
            try:
                with open(GIFT_CODES_FILE, 'r') as f:
                    gift_codes = json.load(f)
            except:
                gift_codes = {'codes': {}}

            # توليد الأكواد الجديدة
            for _ in range(num_codes):
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                generated_codes.append({'code': code, 'amount': amount})

            # تحديث الأكواد
            admin_id = str(update.effective_user.id)
            if admin_id not in gift_codes['codes']:
                gift_codes['codes'][admin_id] = []
            gift_codes['codes'][admin_id].extend(generated_codes)

            # حفظ في الملف
            with open(GIFT_CODES_FILE, 'w') as f:
                json.dump(gift_codes, f, indent=4)

            # إرسال الأكواد المولدة للأدمن
            codes_text = "\n\n".join([f"كود الهدية: `{code['code']}`\nقيمة الهدية: {code['amount']} NSP" for code in generated_codes])
            await update.message.reply_text(
                f"تم توليد الأكواد بنجاح:\n\n{codes_text}",
                parse_mode='Markdown'
            )

            context.user_data['generating_gift'] = False
            context.user_data['gift_step'] = None
            return
        except ValueError:
            await update.message.reply_text("الرجاء إدخال عدد صحيح ❌")
            return

    if context.user_data.get('redeeming_gift'):
        code = update.message.text
        user_id = update.effective_user.id

        # قراءة الأكواد من الملف
        try:
            with open(GIFT_CODES_FILE, 'r') as f:
                gift_codes = json.load(f)
        except:
            gift_codes = {'codes': {}}

        code_found = False
        code_used = False

        # البحث عن الكود في جميع الأكواد المتاحة
        for admin_id, codes_list in gift_codes['codes'].items():
            for code_data in codes_list:
                if code_data['code'] == code:
                    code_found = True
                    if code_data.get('used', False):
                        code_used = True
                        break

                    # البحث عن حساب المستخدم
                    user_account = None
                    for account in user_accounts.values():
                        if account.get('user_id') == user_id:
                            user_account = account
                            break

                    if user_account:
                        # تحديث رصيد المستخدم
                        user_account['balance'] = user_account.get('balance', 0) + code_data['amount']
                        save_accounts()

                        # تحديث حالة الكود
                        code_data['used'] = True
                        code_data['used_by'] = user_id
                        code_data['used_at'] = str(update.message.date)

                        # حفظ التغييرات
                        with open(GIFT_CODES_FILE, 'w') as f:
                            json.dump(gift_codes, f, indent=4)

                        await update.message.reply_text(
                            f"تم استبدال الكود بنجاح وإضافة {code_data['amount']} إلى رصيدك في البوت 🎁✅"
                        )
                        
                        # إرسال إشعار للأدمن
                        admin_notification = f"""
🎁 تم استبدال كود هدية:
👤 المستخدم: {user_id}
💰 قيمة الكود: {code_data['amount']}
🔑 الكود: {code}
⏰ وقت الاستبدال: {update.message.date}
"""
                        await context.bot.send_message(
                            chat_id="5029011355",
                            text=admin_notification
                        )
                        return

        if code_used:
            await update.message.reply_text("تم استبدال هذا الكود سابقاً حظ أوفر في المرة القادمة 🥲")
        elif not code_found:
            await update.message.reply_text("الكود المدخل غير صحيح ❌")

        context.user_data['redeeming_gift'] = False
        return

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == 5029011355:
        command = update.message.text.split()
        if len(command) > 1:
            # عرض تفاصيل أمر محدد
            cmd = command[1].lower()
            command_details = {
                'broadcast': """
📢 الأمر: /broadcast
الوصف: إرسال رسالة إلى جميع المستخدمين
الاستخدام: /broadcast [نص الرسالة]
مثال: /broadcast مرحباً بكم في البوت!
""",
                'send': """
📨 الأمر: /send
الوصف: إرسال رسالة لمستخدم محدد
الاستخدام: /send [معرف المستخدم] [نص الرسالة]
مثال: /send 123456789 مرحباً بك!
""",
                'adduser': """
➕ الأمر: /adduser
الوصف: إضافة حساب جديد
الاستخدام: /adduser [اسم المستخدم] [كلمة المرور]
مثال: /adduser user123 pass123
""",
                'deluser': """
➖ الأمر: /deluser
الوصف: حذف حساب مستخدم
الاستخدام: /deluser [اسم المستخدم]
مثال: /deluser user123
""",
                'addbalance': """
💰 الأمر: /addbalance
الوصف: إضافة رصيد لمستخدم
الاستخدام: /addbalance [معرف المستخدم] [المبلغ] [نسبة البونص] [رقم العملية] [طريقة الدفع] [ملاحظات]
مثال: /addbalance 123456789 100000 10 TR123 syriatel شحن اول مرة
""",
                'deductbalance': """
💸 الأمر: /deductbalance
الوصف: خصم رصيد من مستخدم
الاستخدام: /deductbalance [معرف المستخدم] [المبلغ]
مثال: /deductbalance 123456789 50000
""",
                'users': """
👥 الأمر: /users
الوصف: عرض قائمة المستخدمين المسجلين
الاستخدام: /users
""",
                'listpredefined': """
📋 الأمر: /listpredefined
الوصف: عرض الحسابات المعدة مسبقاً
الاستخدام: /listpredefined
""",
                'addpredefined': """
➕ الأمر: /addpredefined
الوصف: إضافة حساب معد مسبقاً
الاستخدام: /addpredefined [اسم المستخدم] [كلمة المرور]
مثال: /addpredefined user123 pass123
""",
                'delpredefined': """
➖ الأمر: /delpredefined
الوصف: حذف حساب معد مسبقاً
الاستخدام: /delpredefined [اسم المستخدم]
مثال: /delpredefined user123
""",
                'setpayaddr': """
💳 الأمر: /setpayaddr
الوصف: تعيين عنوان الدفع
الاستخدام: /setpayaddr [العنوان]
مثال: /setpayaddr 0912345678
""",
                'setcontactaddr': """
📞 الأمر: /setcontactaddr
الوصف: تعيين عنوان التواصل مع الدعم
الاستخدام: /setcontactaddr [العنوان]
مثال: /setcontactaddr @support
""",
                'giftcode': """
🎁 الأمر: /giftcode
الوصف: إنشاء أكواد هدية
الاستخدام: /giftcode [المبلغ] [عدد الأكواد]
مثال: /giftcode 1000 5
"""
            }
            
            if cmd in command_details:
                await update.message.reply_text(command_details[cmd])
            else:
                await update.message.reply_text("❌ الأمر غير موجود. استخدم /help لعرض قائمة الأوامر المتاحة.")
        else:
            # عرض قائمة الأوامر الرئيسية
            admin_help = """
📋 قائمة أوامر الأدمن:

/broadcast [الرسالة] - إرسال إذاعة لجميع المستخدمين
/send [معرف المستخدم] [الرسالة] - إرسال رسالة لمستخدم محدد
/adduser [اسم المستخدم] [كلمة المرور] - إضافة حساب جديد
/deluser [اسم المستخدم] - حذف حساب
/addbalance [معرف المستخدم] [المبلغ] - إضافة رصيد
/deductbalance [معرف المستخدم] [المبلغ] - خصم رصيد
/users - عرض قائمة المستخدمين
/listpredefined - عرض الحسابات المعدة مسبقاً
/addpredefined [اسم المستخدم] [كلمة المرور] - إضافة حساب معد مسبقاً
/delpredefined [اسم المستخدم] - حذف حساب معد مسبقاً
/setpayaddr [العنوان] - تعيين عنوان الدفع
/setcontactaddr [العنوان] - تعيين عنوان التواصل مع الدعم
/giftcode [المبلغ] [عدد الأكواد] - إنشاء أكواد هدية

للحصول على تفاصيل استخدام أي أمر، اكتب:
/help [اسم الأمر]
مثال: /help broadcast
"""
            await update.message.reply_text(admin_help)
    else:
        # رسالة المساعدة للمستخدمين العاديين
        user_help = """
📋 قائمة الأوامر المتاحة:

/start - بدء استخدام البوت
/help - عرض قائمة الأوامر المتاحة

🔹 الخدمات المتاحة عبر القائمة:
• إنشاء حساب جديد
• شحن وسحب الرصيد
• نظام الإحالات
• كود هدية
• إهداء رصيد
• التواصل مع الدعم
• عرض الشروط والأحكام

للمزيد من المساعدة، يمكنك التواصل مع الدعم الفني عبر القائمة الرئيسية.
"""
        await update.message.reply_text(user_help)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 5029011355:  # التحقق من أن المستخدم هو الأدمن
        return
    
    try:
        if len(context.args) < 1:
            await update.message.reply_text("الاستخدام: /ban [معرف المستخدم] [السبب؟]")
            return
            
        user_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "لم يتم تحديد سبب"
        
        # البحث عن حساب المستخدم
        user_found = False
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                account['banned'] = True
                account['ban_reason'] = reason
                user_found = True
                save_accounts()
                break
                
        if user_found:
            # إرسال إشعار للمستخدم المحظور
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"تم حظر حسابك ❌\nالسبب: {reason}"
                )
            except:
                pass
                
            await update.message.reply_text(f"✅ تم حظر المستخدم {user_id}\nالسبب: {reason}")
        else:
            await update.message.reply_text("❌ لم يتم العثور على المستخدم")
            
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم غير صحيح")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 5029011355:  # التحقق من أن المستخدم هو الأدمن
        return
    
    try:
        if len(context.args) < 1:
            await update.message.reply_text("الاستخدام: /unban [معرف المستخدم]")
            return
            
        user_id = int(context.args[0])
        
        # البحث عن حساب المستخدم
        user_found = False
        for account in user_accounts.values():
            if account.get('user_id') == user_id:
                if account.get('banned', False):
                    account['banned'] = False
                    account.pop('ban_reason', None)
                    user_found = True
                    save_accounts()
                    break
                
        if user_found:
            # إرسال إشعار للمستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="تم إلغاء حظر حسابك ✅"
                )
            except:
                pass
                
            await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم {user_id}")
        else:
            await update.message.reply_text("❌ لم يتم العثور على المستخدم")
            
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم غير صحيح")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # إضافة أوامر الأدمن
    admin_commands = ['broadcast', 'send', 'adduser', 'deluser', 'addbalance', 'deductbalance', 'users', 'listpredefined', 'addpredefined', 'delpredefined', 'setpayaddr', 'giftcode', 'setcontactaddr', 'ban', 'unban']
    for cmd in admin_commands:
        application.add_handler(CommandHandler(cmd, admin_command))

    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    initialize_json_files()
    main()