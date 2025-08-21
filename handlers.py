from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update
import railway_datas
import keyboards
import asyncio
import db
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
from datetime import datetime

TASHKENT_TZ = ZoneInfo("Asia/Tashkent")
scheduler = AsyncIOScheduler(
    timezone=TASHKENT_TZ,
    job_defaults={
        "coalesce": True,          
        "max_instances": 1,        
        "misfire_grace_time": 5, 
    },
)

USER_IDS = ['6889331565', '608913545', '1383186462']

def check_user(chat_id):
    ids_obj = db.RailwayDB()

    chat_id = str(chat_id)
    ids = ids_obj.get_admin_chatIDs()
    USER_IDS.extend(ids)
    if chat_id in USER_IDS:
        return True
    return False

FROM_CITY, TO_CITY, DATE,SELECT, SIGNAL, ADD_COMMENT = range(6)
ID_START = range(1)
EDIT_COMMENT = range(1)

async def start(update: Update, context: CallbackContext):
    user = update.message.chat
    chat_id = user.id
    if check_user(chat_id):
        await update.message.reply_text(
            text=f"""Assalomu aleykum {user.full_name}. Ushbu bot yordamida joylar sonini aniqlashingiz mumkin. /railwaycount""",
        )
    else:
        await update.message.reply_text(
            text=f"""Assalomu aleykum {user.full_name}. Siz bu botdan foydalana olmaysiz 😔""",
        )

async def admin_start(update: Update, context: CallbackContext):
    await update.message.reply_text("Foydalnuvchi IDsini yuboring.")
    return ID_START

async def insert_admin(update: Update, context: CallbackContext):
    ids_obj = db.RailwayDB()

    id_text = update.message.text
    chat_id = str(update.message.chat.id)
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
    chat_id = update.message.chat.id

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

        msg = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="FROM:",
            reply_markup=keyboards.get_viloyats()
        )
    else:
        msg = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="FROM:",
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

        if query.message:
            await query.message.delete()
            msg = await context.bot.send_message(
                chat_id=query.message.chat_id, 
                text="TO:",
                reply_markup=keyboards.get_viloyats()  
            )
        else:
            msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,  
                text="TO:",
                reply_markup=keyboards.get_viloyats()  
            )
    else:
        msg = await update.message.reply_text(
            text="TO:",
            reply_markup=keyboards.get_viloyats()
        )
    context.user_data["last_message"] = msg.message_id
    return TO_CITY

async def to_city_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['to_city'] = query.data
    
    await query.message.reply_text("📅 Sanani kiriting ushbu formatda (Year-Month-Day)!")
    return DATE

async def select_class(update: Update, context: CallbackContext):
    ids_obj = db.RailwayDB()

    context.user_data['date'] = update.message.text.strip()
    date = context.user_data['date']

    if not ids_obj.is_valid_date(date):
        await update.message.reply_text("Sanani noto'g'ri formatda kiritdingiz, iltimos qayta urinib ko'ring (Year-Month-Day)!")
        return DATE
    await update.message.reply_text("Class turini tanlang:", reply_markup=keyboards.select_class_button())
    return SELECT

async def railway_count(update: Update, context: CallbackContext):
    ids_obj = db.RailwayDB()

    select_type = update.message.text.strip()
    context.user_data['class_name'] = select_type
    date = context.user_data['date']
    date = date.split('-')
    date = '-'.join([f'{int(item):02d}' for item in date])

    stationFrom = context.user_data['from_city'].split(':')[1]
    stationTo = context.user_data['to_city'].split(':')[1]

    railway_all_data = railway_datas.Railway(stationFrom=stationFrom, stationTo=stationTo, date=date)

    if ids_obj.is_valid_date(date):
        freeSeats_data, freeSeats = await railway_all_data.get_need_data(type=select_type)
        if freeSeats_data == "notclass":
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
        await update.message.reply_text("Xato kiritdingiz, ushbu formatda bo'lsin (Year-Month-Day)!")
        return SELECT

async def signal_start(update: Update, context: CallbackContext):
    """🚆 Signalni boshlash (InlineKeyboardMarkup orqali)"""

    context.user_data["signal"] = update.message.text.strip().split(':')[-1].strip()
    await update.message.reply_text("Comment qo'shing:")
    return ADD_COMMENT

async def add_comment_signal(update: Update, context: CallbackContext):
    context.user_data['comment'] = update.message.text.strip()

    chat_id = update.message.chat.id
    train_number = context.user_data["signal"]
    select_type = context.user_data['class_name']
    date = context.user_data['date']
    comment = context.user_data['comment']
    date = date.split('-')
    date = '-'.join([f'{int(item):02d}' for item in date])

    await update.message.reply_text(
        f"🚆 {train_number} kuzatuv boshlandi!\n\nHar 2 daqiqada yangilanadi.",
    )

    from_city, from_city_code = context.user_data['from_city'].split(':')
    to_city, to_city_code = context.user_data['to_city'].split(':')
    route = [
            from_city.upper(),
            to_city.upper()
        ]
    add_for_data = {
        "chat_id": chat_id,
        "signal_text": train_number,
        "date": date,
        "comment": comment,
        "class_name": select_type,
        "active": True,
        "route": route,
        "total_free_seats": 0
    }
    obj = db.RailwayDB()
    obj.data_insert(data=add_for_data)

    job_name = f"signal_{chat_id}_{train_number}_{date}"
    interval_num = random.randint(120, 150)
    route_key = ''.join([word[0] for word in ' '.join(route).split()]).lower()
    doc_id = f"{chat_id}_{train_number}_{date}_{route_key}"
    if scheduler.get_job(job_name):
        scheduler.remove_job(job_name)
    
    scheduler.add_job(
        send_signal_job,
        "interval",
        seconds=interval_num,
        id=job_name,
        kwargs={
            "bot": context.bot,
            "data": {
                'doc_id': doc_id,
                'from_city': from_city_code,
                'to_city': to_city_code
            }
        }
    )
    return ConversationHandler.END

async def send_signal_job(bot, data: dict):
    """🚆 Rejalashtirilgan signal xabari (har bir poyezd uchun alohida)"""
    obj = db.RailwayDB()
    doc_id = data['doc_id']
    db_data = obj.get_signal_data(doc_id=doc_id)
    chat_id = db_data["chat_id"]
    signal_text = db_data.get("signal_text", "Noma’lum")
    date = db_data.get("date", None)
    date = "-".join([f'{int(item):02d}' for item in date.split('-')])
    stationFrom = data.get("from_city", None)
    stationTo = data.get("to_city", None)
    signal_comment = db_data.get("comment")
    select_type = db_data.get('class_name')

    railway_all_data = railway_datas.Railway(stationFrom=stationFrom, stationTo=stationTo, date=date)
    freeSeats_data, freeSeats = await railway_all_data.get_need_data(type=select_type)
    try:
        results_signal_text = f"🚆 Poyezd {signal_text} uchun joylar tekshirilmoqda...\n"
        count_free_seats = 0
        for row in freeSeats_data:
            route = row[-1]
            total_free_seats = int(row[-2])
            poyezd_licanse = row[0]

            if poyezd_licanse == signal_text:
                route_key = ''.join([word[0] for word in route]).lower()
                results_signal_text = (
                    f"🚆 {route[0]} - {route[1]}\n📅 Sana: {date}\n"
                    f"🚂 Poyezd number: {signal_text}\nClass: {select_type}\n"
                    f"💺 Bo'sh o'rinlar soni: {total_free_seats}\n💬 Comment: {signal_comment}"
                )
                count_free_seats = total_free_seats

        obj = db.RailwayDB()
        reply_markup = keyboards.signal_keyboard(signal_text, date=date, route_key=route_key)
        if count_free_seats != 0:
            await bot.send_message(chat_id=chat_id,
                                   text=f"📡 Signal: {results_signal_text}",
                                   reply_markup=reply_markup)
    except Exception as e:
        obj = db.RailwayDB()
        if obj.check_date(sana_str=date):
            stations = {
                '2900000': 'Toshkent',
                '2900700': 'Samarqand',
                '2900800': 'Buxoro',
                '2903200': 'Xiva',
                '2900790': 'Urganch',
                '2903000': 'Nukus',
                '2900900': 'Navoiy',
                '2902300': 'Andijon',
                '2901100': 'Qarshi',
                '2900400': 'Jizzax',
                '2901500': 'Termiz',
                '2900200': 'Guliston',
                '2902000': "Qo'qon",
                '2900920': 'Margilon',
                '2901900': 'Pop',
                '2902200': 'Namangan'
            }
            obj = db.RailwayDB()
            if stationFrom and stationTo:
                route_key = f"{stations[stationFrom][0]}{stations[stationTo][0]}".lower()
                doc_id = f"{chat_id}_{signal_text}_{date}_{route_key}"
                obj.update_signal(doc_id=doc_id)
                results_signal_text = f"{stations[stationFrom].upper()} - {stations[stationTo].upper()}\nSana: {date}\nPoyezd number: {signal_text}"

                job_id = f"signal_{chat_id}_{signal_text}_{date}"
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"🚫 Kuzatuv to‘xtatildi.\nSabab: Ma'lumot topilmadi!"
                    )
                    print(e)

async def stop_signal(update: Update, context: CallbackContext):
    """🚫 Signalni to‘xtatish (InlineKeyboardMarkup orqali)"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(':')
    route_key = parts[-3]
    train_number = parts[-2]
    date = parts[-1]

    chat_id = update.effective_chat.id
    job_name = f"signal_{chat_id}_{train_number}_{date}"

    obj = db.RailwayDB()
    doc_id = f"{chat_id}_{train_number}_{date}_{route_key}"
    signal_datas = obj.get_signal_data(doc_id=doc_id)
    results_signal_text = f"🚆 {signal_datas['route'][0]} - {signal_datas['route'][1]}\n📅 Sana: {date}\n🚂 Poyezd number: {train_number}\n💺 Bo'sh o'rinlar soni: {signal_datas['total_free_seats']}\n💬 Comment: {signal_datas['comment']}"
    job = scheduler.get_job(job_name) 
    active = signal_datas['active']
    if job:
        if active:
            obj.update_signal(doc_id=doc_id)  
            scheduler.remove_job(job_name)   
            await query.message.reply_text(f"🚫 {train_number} kuzatuvi to‘xtatildi.\n{results_signal_text}")
        else:
            await query.message.reply_text(f"🚫 {train_number} kuzatuv allaqachon to'xtatilgan!")
        await asyncio.sleep(1)
    else:
        await query.message.reply_text("⚠ Hech qanday aktiv kuzatuv topilmadi.")

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Amalyot bajarilmadi!')
    return ConversationHandler.END

async def view_actives(update: Update, context: CallbackContext):
    """📋 Faol signallar ro‘yxatini chiqarish"""
    chat_id = update.message.chat.id
    if check_user(chat_id):
        railway_obj = db.RailwayDB()
        actives_data = railway_obj.get_actives(chat_id=chat_id)
        if actives_data == []:
            await update.message.reply_text("❌ No active signals found.")
            return
        for act_data in actives_data:
            train_number = act_data['signal_text']
            date = act_data['date']
            signal_comment = act_data['comment']
            results_signal_text = (
                f"🚆 {act_data['route'][0]} - {act_data['route'][1]}\n"
                f"📅 Sana: {date}\n"
                f"🚂 Poyezd number: {train_number}\n"
                f"💺 Bo'sh o'rinlar soni: {act_data['total_free_seats']}\n💬 Comment: {signal_comment}"
            )
            route_key = ''.join([word[0] for word in ' '.join(act_data['route']).split()]).lower()
            reply_markup = keyboards.signal_keyboard(train_number=train_number, date=date, route_key=route_key)
            await update.message.reply_text( 
                text=f"📌 Aktiv signal:\n{results_signal_text}", 
                reply_markup=reply_markup
            )                
            await asyncio.sleep(1)  
    else:
        await update.message.reply_text(
            text=f"""Siz bu botdan foydalana olmaysiz 😔""",
        )

async def restart_active_signals(application):
    """Bot qayta ishga tushganda eski signallarni qayta tiklash"""
    railway_obj = db.RailwayDB()
    actives_data = railway_obj.get_actives()

    if not actives_data:
        print("⏳ Hech qanday aktiv signal topilmadi.")
        return

    stations = {
        "Toshkent": "2900000",
        "Samarqand": "2900700",
        "Buxoro": "2900800",
        "Xiva": "2903200",
        "Urganch": "2900790",
        "Nukus": "2903000",
        "Navoiy": "2900900",
        "Andijon": "2902300",
        "Qarshi": "2901100",
        "Jizzax": "2900400",
        "Termiz": "2901500",
        "Guliston": "2900200",
        "Qo'qon": "2902000",
        "Margilon": "2900920",
        "Pop": "2901900",
        "Namangan": "2902200",
    }
    today = datetime.now().date() 
    for act_data in actives_data:
        job_date = datetime.strptime(act_data['date'], "%Y-%m-%d").date()
        
        chat_id = act_data['chat_id']
        train_number = act_data['signal_text']
        date = act_data['date']
        route = act_data['route']
        from_city = route[0].capitalize()
        from_city_code = stations.get(from_city, None)
        to_city = route[1].capitalize()
        to_city_code = stations.get(to_city, None)
        job_name = f"signal_{chat_id}_{train_number}_{date}"
        if scheduler.get_job(job_name) or job_date < today:
            continue

        interval_num = random.randint(120, 150)
        route_key = ''.join([word[0] for word in ' '.join(act_data['route']).split()]).lower()
        doc_id = f"{chat_id}_{train_number}_{date}_{route_key}"        
        scheduler.add_job(
            send_signal_job,
            "interval",
            seconds=interval_num,
            id=job_name,
            kwargs={
                "bot": application.bot,
                "data": {
                    'doc_id': doc_id,
                    'from_city': from_city_code,
                    'to_city': to_city_code
                }
            }
        )

async def ask_new_comment(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    context.user_data["edit_message_id"] = query.message.message_id
    context.user_data["edit_keyboard"] = query.message.reply_markup
    context.user_data['query_data'] = query.data
    prompt_message = await query.message.reply_text("✍️ Yangi comment kiriting:")
    context.user_data['prompt_message_id'] = prompt_message.message_id
    context.user_data['prompt_chat_id'] = prompt_message.chat.id

    return EDIT_COMMENT

async def save_new_comment(update: Update, context: CallbackContext):
    if "edit_message_id" not in context.user_data:
        return

    new_comment = update.message.text
    chat_id = update.message.chat_id
    message_id = context.user_data["edit_message_id"]

    message = await context.bot.forward_message(
        chat_id=chat_id,
        from_chat_id=chat_id,
        message_id=message_id
    )
    old_text = message.text
    await message.delete()

    idx = 0
    lines = old_text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("💬 Comment:"):
            idx = index
            lines[index] = f"💬 Comment: {new_comment}"
    new_text = "\n".join(lines[:idx+1])

    query_data = context.user_data['query_data']
    _, route_key, train_number, date = query_data.split(':')
    obj = db.RailwayDB()
    doc_id = f"{chat_id}_{train_number}_{date}_{route_key}"
    update_com = obj.update_comment(doc_id=doc_id, new_comment=new_comment)
    old_keyboard = context.user_data.get("edit_keyboard")

    if update_com: 
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=new_text,
            reply_markup=old_keyboard
        )
    else:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=old_text,
            reply_markup=old_keyboard
        )

    await context.bot.delete_message(
        chat_id=context.user_data['prompt_chat_id'],
        message_id=context.user_data['prompt_message_id']
    )
    await update.message.delete()
    del context.user_data['prompt_message_id']
    del context.user_data['prompt_chat_id']
    del context.user_data["edit_message_id"]
    del context.user_data["edit_keyboard"]
    del context.user_data["query_data"]

    return ConversationHandler.END