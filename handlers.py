from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update
import railway_datas
import keyboards
import asyncio

FROM_CITY, TO_CITY, DATE,SELECT, SIGNAL = range(5)

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    msg = await update.message.reply_text(
        text=f"""Assalomu aleykum {user.full_name}. Ushbu bot yordamida joylar sonini aniqlashingiz mumkin. /railwaycount""",
    )

async def railway_start(update: Update, context: CallbackContext):
    
    msg = await update.message.reply_text("Poyezd tanlash boshlandi!!!")
    context.user_data["last_message"] = msg.message_id
    
    return await get_from_city(update, context)

async def safe_delete_message(bot, chat_id, message_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"[Xatolik] Xabarni o‘chirishda muammo: {e}")

async def get_from_city(update: Update, context: CallbackContext):
    if "last_message" in context.user_data:
        await safe_delete_message(context.bot, update.message.chat_id, context.user_data["last_message"])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Xatolik (delete_message): {e}") 

        msg = await query.message.reply_text(
            text="Qayerdan borishingizni tanlang:",
            reply_markup=keyboards.get_viloyats()
        )

    else:
        msg = await update.message.reply_text(
            text="Qayerdan borishingizni tanlang:",
            reply_markup=keyboards.get_viloyats()
        )

    context.user_data["last_message"] = msg.message_id
    return FROM_CITY


async def from_city_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['from_city'] = query.data
    
    return await get_to_city(update, context)


async def get_to_city(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Xatolik: {e}")

        msg = await query.message.reply_text(
            text="Qayerga borishingizni tanlang:",
            reply_markup=keyboards.get_viloyats()
        )

    else:
        msg = await update.message.reply_text(
            text="Qayerga borishingizni tanlang:",
            reply_markup=keyboards.get_viloyats()
        )

    context.user_data["last_message"] = msg.message_id
    return TO_CITY



async def to_city_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['to_city'] = query.data
    
    await query.message.reply_text("Sanani kiriting ushbu formatda (day.month.year)!")
    return DATE

async def select_class(update: Update, context: CallbackContext):
    context.user_data['date'] = update.message.text.strip()
    
    await update.message.reply_text("Class turini tanlang:", reply_markup=keyboards.select_class_button())
    return SELECT

async def railway_count(update: Update, context: CallbackContext):
    
    select_type = update.message.text.strip()
    context.user_data['class_name'] = select_type

    date = context.user_data['date']
    date = date.split('.')
    date = '.'.join([f'{int(item):02d}' for item in date])
    stationFrom = context.user_data['from_city'].split(':')[1]
    stationTo = context.user_data['to_city'].split(':')[1]

    railway_all_data = railway_datas.Railway(stationFrom=stationFrom, stationTo=stationTo, date=date)
    
    if railway_all_data.is_valid_date():
        freeSeats_data, freeSeats = railway_all_data.get_need_data(type=select_type)
        
        if freeSeats_data == "notclass":
            await update.message.reply_text(f"Bu class nomida ma'lumot yo'q, qayta kiriting.")

        text_seats = f"Class names: {select_type}\n"
        for row in freeSeats_data:
            text_seats += f"Poezd number: {row[0]}\n  Poyezd brand: {row[1]}\n  Ketish vaqti: {row[2]}\n  Kelish vaqti: {row[3]}\n  FreeSeats: {row[4]}\n"+"-"*40+'\n'

        text_seats += f"Barcha bo'sh o'rinlar soni: {freeSeats}"
        poyezd_number = []
        for row in freeSeats_data:
            number = "Poyezd number: " + row[0]
            total_free_seats = int(row[-2])
            if total_free_seats == 0:
                poyezd_number.append(number)

        if poyezd_number != []:
            reply_markup = keyboards.poyezd_licanse(poyezd_number)
            await update.message.reply_text(f"{text_seats}", reply_markup=reply_markup)
            return SIGNAL
        else:
            await update.message.reply_text(f"{text_seats}")
            return SELECT
    else:
        await update.message.reply_text("Xato kiritdingiz, ushbu formatda bo'lsin (day.month.year)!")
        return SELECT
    
async def signal_start(update: Update, context: CallbackContext):
    """Foydalanuvchiga signalni boshlash haqida xabar berish"""
    chat_id = update.message.chat_id
    context.user_data["signal"] = update.message.text.strip().split(':')[-1].strip()
    select_type = context.user_data['class_name']
    reply_markup = keyboards.signal_keyboard() if callable(keyboards.signal_keyboard) else keyboards.signal_keyboard

    await update.message.reply_text(
        f"Signal yuborish boshlandi.\n\nHar 1 daqiqada xabar yuboriladi.",
        reply_markup=reply_markup
    )

    if context.application is None or context.application.job_queue is None:
        print("Xatolik: `context.application` yoki `job_queue` mavjud emas!")
        return

    job_queue = context.application.job_queue
    stationFrom = context.user_data['from_city'].split(':')[1]
    stationTo = context.user_data['to_city'].split(':')[1]
    date = context.user_data['date']
    job_queue.run_repeating(
        send_signal_job, interval=60, first=0, name=str(chat_id),
        data={
            "chat_id": chat_id, "signal": context.user_data["signal"],
            "from_city":stationFrom, 
            "to_city": stationTo,      
            "date": date, 
            "class_name": select_type
            }  
    )

async def send_signal_job(context: CallbackContext):
    """Rejalashtirilgan signal xabari"""
    job = context.job  
    if job is None or "chat_id" not in job.data:
        return
    
    chat_id = job.data["chat_id"]
    signal_text = job.data.get("signal", "Noma’lum") 
    date = job.data.get("date", None)
    date = date.split('.')
    date = '.'.join([f'{int(item):02d}' for item in date])

    stationFrom = job.data.get("from_city", None)
    stationTo = job.data.get("to_city", None)

    select_type = job.data.get('class_name')
    railway_all_data = railway_datas.Railway(stationFrom=stationFrom, stationTo=stationTo, date=date)
    freeSeats_data, freeSeats = railway_all_data.get_need_data(type=select_type)

    for row in freeSeats_data:
        route = row[-1]
        total_free_seats = int(row[-2])
        poyezd_licanse = row[0]
        if poyezd_licanse == signal_text:
            results_signal_text = f"{route[0]} - {route[1]}\nSana: {date}\nPoyezd number: {signal_text}\nBo'sh o'rinlar soni: {total_free_seats}"

    await context.bot.send_message(chat_id=chat_id, text=f"Signal: {results_signal_text}")

async def stop_signal(update: Update, context: CallbackContext):
    """Signal yuborishni to‘xtatish"""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id if query.message else None
    if chat_id is None:
        await query.message.reply_text("⚠ Xatolik: chat ID aniqlanmadi.")
        return

    if not context.application or not context.application.job_queue:
        await query.message.reply_text("⚠ Xatolik: Job Queue topilmadi.")
        return

    current_jobs = context.application.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    await query.message.reply_text("🚫 Signal yuborish to‘xtatildi.")
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Amalyot bajarilmadi!')
    return ConversationHandler.END


