# --------------------- ایمپورت ها ------------------------------

from telegram import (Update,
                      InlineKeyboardButton,
                      InlineKeyboardMarkup,
                      InputFile)

from telegram.ext import (CommandHandler,
                          ApplicationBuilder,
                          ContextTypes,
                          CallbackQueryHandler,
                          ConversationHandler,
                          MessageHandler,
                          filters)

import json
import os

# --------------------- متغیر ها ------------------------------

ADMIN_ID = 1402912123
ADDING_TASK = 1
todo_data = {}
DATA_FILE = "todo_data.json"
user_ids = set()

# ----------------- ذخیره و بارگیری ----------------------------

def save_user_ids():
    with open('user_ids.json', 'w') as f:
        json.dump(list(user_ids), f)

def load_user_ids():
    global user_ids
    if os.path.exists('user_ids.json'):
        with open('user_ids.json', 'r') as f:
            user_ids = set(json.load(f))

def save_tasks () :
    with open(DATA_FILE, 'w', encoding = 'utf-8') as f :
        json.dump(todo_data, f, ensure_ascii=False)

def load_tasks () :
    global todo_data
    if os.path.exists(DATA_FILE) :
        with open(DATA_FILE, 'r', encoding='utf-8') as f :
            todo_data = json.load(f)
    else :
        todo_data = {}

def get_user_tasks(user_id):
    user_id = str(user_id)
    if user_id not in todo_data:
        todo_data[user_id] = []
    return todo_data[user_id]


# ----------------- دکمه ها ---------------------------

async def handle_buttom(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    query = update.callback_query
    user_id = update._effective_user.id
    user_tasks = get_user_tasks(user_id)

    await query.answer()
    data = query.data

    # ابتدا بررسی می‌کنیم که آیا حالت multi هست یا خیر
    if data == "mark_done_multi":
        await context.bot.send_message(chat_id=user_id, text="شماره‌های کارهایی که می‌خوای علامت بزنی رو با `|` جدا کن (مثلاً: 1 | 3 | 5)")
        context.user_data['action'] = 'mark_done_multi'
    
    elif data == "remove_multi":
        await context.bot.send_message(chat_id=user_id, text="شماره‌های کارهایی که می‌خوای حذف کنی رو با `|` جدا کن (مثلاً: 2 | 4)")
        context.user_data['action'] = 'remove_multi'

    elif data.startswith("done_"):
        try:
            index = int(data.split("_")[1])
            if 0 <= index < len(user_tasks):
                user_tasks[index] = f"✅ {user_tasks[index]}"
                save_tasks()
                await query.edit_message_text(f"{index+1}, {user_tasks[index]}")
        except ValueError:
            await query.edit_message_text("شماره نامعتبر بود.")

    elif data.startswith("remove_"):
        try:
            index = int(data.split("_")[1])
            if 0 <= index < len(user_tasks):
                removed = user_tasks.pop(index)
                save_tasks()
                await query.edit_message_text(f"کار '{removed}' حذف شد. ")
        except ValueError:
            await query.edit_message_text("شماره نامعتبر بود.")


# -------------------------- Back Up & Admin ----------------------------------

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'rb') as f:
            await update.message.reply_document(InputFile(f, filename='todo_data.json'))
    else:
        await update.message.reply_text("فایل دیتابیس پیدا نشد.")


async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("شما اجازه دسترسی به این بخش را ندارید.")
        return

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'rb') as f:
            await update.message.reply_document(InputFile(f, filename='todo_data.json'))
    else:
        await update.message.reply_text("فایل دیتابیس پیدا نشد.")


# --------------------------- اطلاع رسانی ---------------------------------
    
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("شما اجازه این کار را ندارید.")
        return

    if not context.args:
         await update.message.reply_text("لطفا متنی برای ارسال وارد کن.")
         return

    message = ' '.join(context.args)
    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            success += 1
        except Exception as e:
            failed += 1

    await update.message.reply_text(f"📢 پیام ارسال شد.\n✅ موفق: {success}\n❌ ناموفق: {failed}")

# -------------------------- شروع ---------------------------

async def start (update: Update, context: ContextTypes.DEFAULT_TYPE) :

    user_id = str(update.effective_user.id)
    if user_id not in todo_data:
         todo_data[user_id] = []
         save_tasks()
    
    user_ids.add(user_id)
    save_user_ids()

    await update.message.reply_text("""
                                    
                                    سلام کاربر عزیز
این یه ربات برای لیست کردن کار هاته که دیگه اونارو فراموش نکنی 😁
از دستورات زیر برای استفاده از ربات اسفاده کن : 
                                    ----------------------------------------------
برای نشون دادن لیست کار هات از دستور /show استفاده کن
برای اضافه کردن کارهات به لیسست از دستور /add استفاده کن
برای علامت زدن به عنوان انجام شده از دستور /done استفاده کن
برای حذف کردن یه کار از دستور /remove استفاده کن
برای استفاده از راهنما /help
                                    ----------------------------------------------
""")

# -------------------------- اضافه کردن (جدید) --------------------------

async def add_task_start (update:Update, context:ContextTypes.DEFAULT_TYPE) :
    await update.message.reply_text("لطفا عنوان یا عنوان های کار رو وارد کن(میتونی از | برای جداسازی استفاده کنی : )")
    return ADDING_TASK

async def receive_task(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    user_id = update.effective_user.id
    text = update.message.text
    tasks = [task.strip() for task in text.split('|') if task.strip()]

    if not tasks :
        await update.message.reply_text("هیچ کاری دریافت نشد. لطفا دوباره امتحان کن. ")
        return ADDING_TASK
    
    
    user_tasks = get_user_tasks(user_id)
    user_tasks.extend(tasks)
    
    save_tasks()
    await update.message.reply_text(f"{len(tasks)} کار با موفقیت اضافه شد. ✅")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    await update.message.reply_text("افزودن لغو شد. ")
    return ConversationHandler.END

# -------------------------- نشان دادن --------------------------------

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update._effective_user.id
    user_tasks = get_user_tasks(user_id)

    if not user_tasks:
        await update.message.reply_text("هیچ کاری برای نمایش وجود ندارد.")
        return

    # نمایش لیست در یک پیام
    task_list_text = "\n".join([f"{i + 1}. {task}" for i, task in enumerate(user_tasks)])

    # دکمه‌ها برای عملیات
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ علامت‌زدن انجام شده", callback_data="mark_done_multi")],
        [InlineKeyboardButton("🗑️ حذف کارها", callback_data="remove_multi")]
    ])

    await update.message.reply_text(
        f"📝 لیست کارهای شما:\n\n{task_list_text}",
        reply_markup=keyboard
    )

# ------------------ علامت زدن به عنوان انجام شده ------------------------

async def mark_done(update: Update, context:ContextTypes.DEFAULT_TYPE) :
    user_id = update._effective_user.id
    user_tasks = get_user_tasks(user_id)

    if len(context.args) == 0 :
        await update.message.reply_text("لطفا سماره کار رو وارد کن. ")
        return
    try :
        task_num = int(context.args[0]) - 1
    except ValueError :
        await update.message.reply_text("شماره وارد شده معتبر نیست. ")
        return


    if task_num < 0 or task_num >= len(user_tasks) :
        await update.message.reply_text("شماره کار وارد شده، معتبر نیست. ")
        return
    
    completed_task = user_tasks[task_num]
    user_tasks[task_num] = f"✅ {completed_task}"
    save_tasks()
    await update.message.reply_text(f"تسک {task_num + 1} به عنوان انجام شده علامت گذاری شد. ")

# ------------------------- پاک کردن تسک --------------------------------

async def remove_task(update:Update, context: ContextTypes.DEFAULT_TYPE) :
    user_id = update._effective_user.id
    user_tasks = get_user_tasks(user_id)

    if len(context.args) == 0 :
        await update.message.reply_text("لطفا شماره کار رو وارد کن. ")
        return
    
    try :
        task_num = int(context.args[0]) - 1
    except ValueError :
        await update.message.reply_text("شماره وارد شده معتبر نیست. ")
        return

    
    if task_num < 0 or task_num >= len(user_tasks) :
        await update.message.reply_text("شماره کار وارد شده معتبر نیست. ")
        return

    removed_task = user_tasks.pop(task_num)
    save_tasks()
    await update.message.reply_text(f"تسک {removed_task} با موفقیت حذف شد. ")    

# ------------------------- کمک ------------------------------------
async def help (update:Update, context:ContextTypes.DEFAULT_TYPE) :
    await update.message.reply_text("""
                                    برای استفاده صحیح از دستورات، اینطوری اونارو وارد کن :
                                    ----------------------------------------------
                                    /show
                                    /add <کاری که میخوای اضافه کنی>
                                    /done <شماره کاری که میخوای علامت بزنی>
                                    /remove <شماره کاری که میخوای علامت بزنی>
                                    ----------------------------------------------
""")

# -------------------------------------------------------------------------------

async def handle_multi_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_tasks = get_user_tasks(user_id)
    action = context.user_data.get('action')
    text = update.message.text
    numbers = [int(num.strip()) - 1 for num in text.split('|') if num.strip().isdigit()]

    if not numbers:
        await update.message.reply_text("شماره‌ها معتبر نیستند.")
        return

    done_count = 0
    removed_count = 0

    if action == 'mark_done_multi':
        for i in numbers:
            if 0 <= i < len(user_tasks) and not user_tasks[i].startswith("✅"):
                user_tasks[i] = f"✅ {user_tasks[i]}"
                done_count += 1
        await update.message.reply_text(f"{done_count} کار علامت زده شد.")
    
    elif action == 'remove_multi':
        for i in sorted(numbers, reverse=True):
            if 0 <= i < len(user_tasks):
                user_tasks.pop(i)
                removed_count += 1
        await update.message.reply_text(f"{removed_count} کار حذف شد.")

    save_tasks()
    context.user_data.pop('action', None)  # ✅ این خط مهمه

# -------------------------هندلر ها ----------------------------------------

conv_handler = ConversationHandler(
    entry_points= [CommandHandler('add', add_task_start)],
    states= {
        ADDING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_task)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

# app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app = ApplicationBuilder().token("7749405805:AAHX7uM8DEb69SrRFM2G2TMkjUWEya9qsXM").build()
app.add_handler(CommandHandler('backup', backup))
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('show', show_list))
app.add_handler(conv_handler)
app.add_handler(CommandHandler('done', mark_done))
app.add_handler(CommandHandler('remove', remove_task))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_multi_action))
app.add_handler(CommandHandler('help', help))
app.add_handler(CallbackQueryHandler(handle_buttom))
app.add_handler(CommandHandler('admin_backup', admin_backup))
app.add_handler(CommandHandler("broadcast", broadcast))

load_tasks()
app.run_polling()