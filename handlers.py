from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update
import railway_datas
import keyboards
import asyncio
import db
import time

USER_IDS = ['6889331565', '608913545', '1383186462']
ids_obj = db.RailwayDB()

def check_user(chat_id):
    chat_id = str(chat_id)
    ids = ids_obj.get_admin_chatIDs()
    USER_IDS.extend(ids)
    if chat_id in USER_IDS:
        return True
    return False

FROM_CITY, TO_CITY, DATE,SELECT, SIGNAL, ADD_COMMENT = range(6)
ID_START = range(1)

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = user.id
    if check_user(chat_id):
        msg = await update.message.reply_text(
            text=f"""Assalomu aleykum {user.full_name}. Ushbu bot yordamida joylar sonini aniqlashingiz mumkin. /railwaycount""",
        )
    else:
        msg = await update.message.reply_text(
            text=f"""Assalomu aleykum {user.full_name}. Siz bu botdan foydalana olmaysiz 😔""",
        )

async def admin_start(update: Update, context: CallbackContext):
    await update.message.reply_text("Foydalnuvchi IDsini yuboring.")
    return ID_START

async def insert_admin(update: Update, context: CallbackContext):
    id_text = update.message.text
    chat_id = str(update.message.from_user.id)
    if chat_id in USER_IDS :
        if ids_obj.add_admin(id_text):
            await update.message.reply_text("Foydalanuvchi qo'shildi ✅")
            return ConversationHandler.END
        else:
            await update.message.reply_text("ID xato yoki User allaqachon mavjud ❌")
    else:
        await update.message.reply_text("Siz foydalanuvchi qo'sholmaysiz ❌")

    return ConversationHandler.END

async def railway_start(update: Update, context: CallbackContext):
    chat_id = update.message.from_user.id

    if check_user(chat_id):
        msg = await update.message.reply_text("Poyezd tanlash boshlandi!!!")
        context.user_data["last_message"] = msg.message_id
        
        return await get_from_city(update, context)
    else:
        await update.message.reply_text(
            text=f"""Siz bu botdan foydalana olmaysiz 😔""",
        )
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
            text="FROM WHERE:",
            reply_markup=keyboards.get_viloyats()
        )

    else:
        msg = await update.message.reply_text(
            text="FROM WHERE:",
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
            text="TO WHERE:",
            reply_markup=keyboards.get_viloyats()
        )

    else:
        msg = await update.message.reply_text(
            text="TO WHERE:",
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

    context.user_data["signal"] = update.message.text.strip().split(':')[-1].strip()
    await update.message.reply_text("Comment qo'shing:")
    return ADD_COMMENT

async def add_comment_signal(update: Update, context: CallbackContext):
    context.user_data['comment'] = update.message.text.strip()

    chat_id = update.message.chat_id
    train_number = context.user_data["signal"]
    select_type = context.user_data['class_name']
    date = context.user_data['date']
    comment = context.user_data['comment']
    date = date.split('.')
    date = '.'.join([f'{int(item):02d}' for item in date])
    await update.message.reply_text(
        f"🚆 {train_number} kuzatuv boshlandi!\n\nHar 2 daqiqada yangilanadi.",
    )

    if context.application is None or context.application.job_queue is None:
        await update.message.reply_text("⚠ Xatolik: Job Queue ishlamayapti!")
        return

    job_queue = context.application.job_queue
    job_name = f"signal_{chat_id}_{train_number}_{date}"

    job_queue.run_repeating(
        send_signal_job, interval=120, first=0, name=job_name,
        data={
            "chat_id": chat_id,
            "signal": train_number,
            "from_city": context.user_data['from_city'].split(':')[1],
            "to_city": context.user_data['to_city'].split(':')[1],
            "date": context.user_data['date'],
            "class_name": select_type,
            "comment": comment
        }
    )
    return ConversationHandler.END

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
    signal_comment = job.data.get("comment")
    select_type = job.data.get('class_name')
    railway_all_data = railway_datas.Railway(stationFrom=stationFrom, stationTo=stationTo, date=date)
    freeSeats_data, freeSeats = railway_all_data.get_need_data(type=select_type)

    try:
        results_signal_text = f"🚆 Poyezd {signal_text} uchun joylar tekshirilmoqda...\n"
        add_for_data = {
                    'chat_id': chat_id,
                    'signal_text': signal_text,
                    'date': date,
                    'comment': signal_comment,
                    'class_name': select_type,
                    'active': True
                }
        count_free_seats = 0
        for row in freeSeats_data:
            route = row[-1]
            total_free_seats = int(row[-2])
            poyezd_licanse = row[0]
            if poyezd_licanse == signal_text:
                route_key = ''.join([word[0] for word in route]).lower()
                add_for_data['route'] = route
                add_for_data['total_free_seats'] = total_free_seats
                results_signal_text = f"{route[0]} - {route[1]}\nSana: {date}\nPoyezd number: {signal_text}\nClass: {select_type}\nBo'sh o'rinlar soni: {total_free_seats}\nComment: {signal_comment}"
                count_free_seats = total_free_seats
        obj = db.RailwayDB()
        obj.data_insert(data=add_for_data)
        # Har bir poyezd uchun alohida "To‘xtatish" tugmasi
        reply_markup = keyboards.signal_keyboard(signal_text, date=date, route_key=route_key)
        if count_free_seats != 0:
            await context.bot.send_message(chat_id=chat_id, 
                                        text=f"Signal: {results_signal_text}", 
                                        reply_markup=reply_markup)
    except:
        job_name = context.job.name  
        obj = db.RailwayDB()
        if stationFrom and stationTo:
            route_key = f"{stationFrom[0]}{stationTo[0]}".lower()
            doc_id = f"{chat_id}_{signal_text}_{date}_{route_key}"
            obj.update_signal(doc_id=doc_id)
            results_signal_text = f"{stationFrom} - {stationTo}\nSana: {date}\nPoyezd number: {signal_text}"

            current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
            if current_jobs:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚫 {results_signal_text} kuzatuvi avtomatik to‘xtatildi.\nSabab: Ma'lumot topilmadi!"
                )
                await asyncio.sleep(3)
    
async def stop_signal(update: Update, context: CallbackContext):
    """🚫 Signalni to‘xtatish (InlineKeyboardMarkup orqali)"""
    query = update.callback_query
    await query.answer()
    query_data = query.data.split(':')  # ⛔ "stop_signal:778Ф" → "778Ф"
    train_number = query_data[-2]
    date = query_data[-1]
    route_key = query_data[-3]
    obj = db.RailwayDB()
    chat_id = query.message.chat_id if query.message else update.effective_chat.id 
    doc_id = f"{chat_id}_{train_number}_{date}_{route_key}"
    signal_datas = obj.get_signal_data(doc_id=doc_id)
    results_signal_text = f"{signal_datas['route'][0]} - {signal_datas['route'][1]}\nSana: {date}\nPoyezd number: {train_number}\nBo'sh o'rinlar soni: {signal_datas['total_free_seats']}\nComment: {signal_datas['comment']}"
    active = signal_datas['active']
    if not context.application or not context.application.job_queue:
        await query.message.reply_text("⚠ Xatolik: Job Queue topilmadi.")
        return

    job_name = f"signal_{chat_id}_{train_number}_{date}"
    current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
    if current_jobs:
        # for job in current_jobs:
        #     job.schedule_removal()
        if active:
            obj.update_signal(doc_id=doc_id)
            await query.message.reply_text(f"🚫 {train_number} kuzatuvi to‘xtatildi.\n{results_signal_text}")
        else:
            await query.message.reply_text(f"🚫 {train_number} kuzatuv allaqachon to'xtatilgan!")
        time.sleep(3)
    else:
        await query.message.reply_text("⚠ Hech qanday aktiv kuzatuv topilmadi.")


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Amalyot bajarilmadi!')
    return ConversationHandler.END

async def view_actives(update: Update, context: CallbackContext):
    """📋 Faol signallar ro‘yxatini chiqarish"""
    chat_id = update.message.chat_id 
    if check_user(chat_id):
        railway_obj = db.RailwayDB()
        actives_data = railway_obj.get_actives()
        

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
            signal_comment = act_data['comment']
            if job_name in active_jobs:
                found_active = True 
                results_signal_text = (
                    f"{act_data['route'][0]} - {act_data['route'][1]}\n"
                    f"Sana: {date}\n"
                    f"Poyezd number: {train_number}\n"
                    f"Bo'sh o'rinlar soni: {act_data['total_free_seats']}\nComment: {signal_comment}"
                )
                route_key = ''.join([word[0] for word in ' '.join(act_data['route']).split()]).lower()
                reply_markup = keyboards.signal_keyboard(train_number=train_number, date=date, route_key=route_key)
                await update.message.reply_text( 
                    text=f"📌 Aktiv signal:\n{results_signal_text}", 
                    reply_markup=reply_markup
                )                
                await asyncio.sleep(1)  

        if not found_active:
            await update.message.reply_text("❌ Hech qanday aktiv signal topilmadi.")
    else:
        await update.message.reply_text(
            text=f"""Siz bu botdan foydalana olmaysiz 😔""",
        )

async def restart_active_signals(application):
    """Bot qayta ishga tushganda eski signallarni qayta tiklash"""
    railway_obj = db.RailwayDB()
    actives_data = railway_obj.get_actives()

    job_queue = application.job_queue
    if not actives_data:
        print("⏳ Hech qanday aktiv signal topilmadi.")
        return
    stations = {
        "Toshkent": "2900000",
        "Samarqand": "2900700",
        "Buxoro": "2900800",
        "Xiva": "2903200",
        "Urganch": "2900790",#
        "Nukus": "2903000",
        "Navoiy": "2900900",
        "Andijon": "2902300",
        "Qarshi": "2901100",
        "Jizzax": "2900400",
        "Termiz": "2901500",
        "Guliston": "2900200",
        "Qo'qon": "2902000",
        "Margilon": "2900920",#
        "Pop": "2901900",
        "Namangan": "2902200",
    }
    for act_data in actives_data:
        chat_id = act_data['chat_id']
        train_number = act_data['signal_text']
        date = act_data['date']
        route = act_data['route']
        from_city = route[0].capitalize()
        to_city = route[1].capitalize()
        select_type = act_data.get('class_name', 'Noma’lum')
        comment = act_data.get('comment', '')

        job_name = f"signal_{chat_id}_{train_number}_{date}"

        job_queue.run_repeating(
            send_signal_job, interval=120, first=0, name=job_name,
            data={
                "chat_id": chat_id,
                "signal": train_number,
                "from_city": stations[from_city],
                "to_city": stations[to_city],
                "date": date,
                "class_name": select_type,
                "comment": comment
            }
        )

