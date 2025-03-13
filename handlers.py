from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update
import railway_datas
import keyboards
import asyncio
import db
import time

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
        
        if freeSeats_data == "notclass" :
            await update.message.reply_text(f"{select_type} bunda ma'lumot yo'q, qayta kiriting.")
            return SELECT
        elif freeSeats_data == None:
            await update.message.reply_text(f"{date} bu vaqtda ma'lumot yo'q, qayta kiriting.")
            return DATE

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
    """🚆 Signalni boshlash (InlineKeyboardMarkup orqali)"""
    

    chat_id = update.message.chat_id
    context.user_data["signal"] = update.message.text.strip().split(':')[-1].strip()
    train_number = context.user_data["signal"]
    select_type = context.user_data['class_name']
    date = context.user_data['date']
    date = date.split('.')
    date = '.'.join([f'{int(item):02d}' for item in date])
    await update.message.reply_text(
        f"🚆 {train_number} kuzatuv boshlandi!\n\nHar 1 daqiqada yangilanadi.",
    )

    if context.application is None or context.application.job_queue is None:
        await update.message.reply_text("⚠ Xatolik: Job Queue ishlamayapti!")
        return

    job_queue = context.application.job_queue
    job_name = f"signal_{chat_id}_{train_number}_{date}"

    job_queue.run_repeating(
        send_signal_job, interval=60, first=0, name=job_name,
        data={
            "chat_id": chat_id,
            "signal": train_number,
            "from_city": context.user_data['from_city'].split(':')[1],
            "to_city": context.user_data['to_city'].split(':')[1],
            "date": context.user_data['date'],
            "class_name": select_type
        }
    )


async def send_signal_job(context: CallbackContext):
    """🚆 Rejalashtirilgan signal xabari (har bir poyezd uchun alohida)"""
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

    results_signal_text = f"🚆 Poyezd {signal_text} uchun joylar tekshirilmoqda...\n"
    add_for_data = {
                'chat_id': chat_id,
                'signal_text': signal_text,
                'date': date,
                'active': True
            }
    count_free_seats = 0
    for row in freeSeats_data:
        route = row[-1]
        total_free_seats = int(row[-2])
        poyezd_licanse = row[0]
        if poyezd_licanse == signal_text:
            add_for_data['route'] = route
            add_for_data['total_free_seats'] = total_free_seats
            results_signal_text = f"{route[0]} - {route[1]}\nSana: {date}\nPoyezd number: {signal_text}\nBo'sh o'rinlar soni: {total_free_seats}"
            count_free_seats = total_free_seats
    obj = db.RailwayDB()
    obj.data_insert(data=add_for_data)
    # Har bir poyezd uchun alohida "To‘xtatish" tugmasi
    reply_markup = keyboards.signal_keyboard(signal_text, date=date)
    if count_free_seats != 0:
        await context.bot.send_message(chat_id=chat_id, 
                                    text=f"Signal: {results_signal_text}", 
                                    reply_markup=reply_markup)

async def stop_signal(update: Update, context: CallbackContext):
    """🚫 Signalni to‘xtatish (InlineKeyboardMarkup orqali)"""
    query = update.callback_query
    await query.answer()

    query_data = query.data.split(':')  # ⛔ "stop_signal:778Ф" → "778Ф"
    train_number = query_data[-2]
    date = query_data[-1]

    obj = db.RailwayDB()
    chat_id = query.message.chat_id if query.message else update.effective_chat.id 
    doc_id = f"{chat_id}_{train_number}_{date}"
    signal_datas = obj.get_signal_data(doc_id=doc_id)
    results_signal_text = f"{signal_datas['route'][0]} - {signal_datas['route'][1]}\nSana: {date}\nPoyezd number: {train_number}\nBo'sh o'rinlar soni: {signal_datas['total_free_seats']}"
    
    if chat_id is None:
        await query.message.reply_text("⚠ Xatolik: chat ID aniqlanmadi.")
        return

    if not context.application or not context.application.job_queue:
        await query.message.reply_text("⚠ Xatolik: Job Queue topilmadi.")
        return

    job_name = f"signal_{chat_id}_{train_number}_{date}"
    current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
        obj.update_signal(doc_id=doc_id)
        await query.message.reply_text(f"🚫 {train_number} kuzatuvi to‘xtatildi.\n{results_signal_text}")
        time.sleep(5)
    else:
        await query.message.reply_text("⚠ Hech qanday aktiv kuzatuv topilmadi.")


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Amalyot bajarilmadi!')
    return ConversationHandler.END

async def view_actives(update: Update, context: CallbackContext):
    """📋 Faol signallar ro‘yxatini chiqarish"""
    railway_obj = db.RailwayDB()
    actives_data = railway_obj.get_actives()
    chat_id = update.message.chat_id  

    job_queue = context.application.job_queue
    active_jobs = {job.name for job in job_queue.jobs()}  
    if not actives_data:
        await update.message.reply_text("❌ Hech qanday aktiv kuzatuv topilmadi.")
        return

    found_active = False  

    for act_data in actives_data:
        train_number = act_data['signal_text']
        date = act_data['date']
        job_name = f"signal_{chat_id}_{train_number}_{date}"  

        if job_name in active_jobs:
            found_active = True 
            results_signal_text = (
                f"{act_data['route'][0]} - {act_data['route'][1]}\n"
                f"Sana: {date}\n"
                f"Poyezd number: {train_number}\n"
                f"Bo'sh o'rinlar soni: {act_data['total_free_seats']}"
            )

            callback_data = f"stop_signal:{train_number}:{date}"  

            reply_markup = keyboards.signal_keyboard(train_number=train_number, date=date)
            await update.message.reply_text( 
                text=f"📌 Aktiv signal:\n{results_signal_text}", 
                reply_markup=reply_markup
            )                
            await asyncio.sleep(1)  

    if not found_active:
        await update.message.reply_text("❌ JobQueue dagi hech qanday aktiv signal topilmadi.")
