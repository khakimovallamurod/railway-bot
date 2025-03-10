from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update
import checkrailway
import keyboards
import asyncio

FROM_CITY, TO_CITY, DATE, SIGNAL = range(4)

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

async def railway_count(update: Update, context: CallbackContext):
    context.user_data['date'] = update.message.text.strip()
    date = context.user_data['date']
    date = date.split('.')
    date = '.'.join([f'{int(item):02d}' for item in date])
    stationFrom = context.user_data['from_city'].split(':')[1]
    stationTo = context.user_data['to_city'].split(':')[1]

    if checkrailway.is_valid_date(date):
        freeSeats_data, freeSeats = await asyncio.to_thread(checkrailway.reilway_counts, stationFrom, stationTo, date)
        if freeSeats_data==None:
            await update.message.reply_text(f"Ma'lumot yo'q, qaytadan urinib ko'ring. /railwaycount")
            return DATE
        
        text_seats = ''.join(''.join(row) for row in freeSeats_data)
        text_seats += f"Barcha bo'sh o'rinlar soni: {freeSeats}"
        poyezd_number = []
        for row in freeSeats_data:
            number = row[0].strip('\n')
            total_free_seats = int(row[-2].split(':')[-1].strip(' ').strip('\n'))
            if total_free_seats == 0:
                poyezd_number.append(number)

        if poyezd_number != []:
            reply_markup = keyboards.poyezd_licanse(poyezd_number)
            await update.message.reply_text(f"{text_seats}", reply_markup=reply_markup)
            return SIGNAL
        else:
            await update.message.reply_text(f"{text_seats}")
            return ConversationHandler.END
    else:
        await update.message.reply_text("Xato kiritdingiz, ushbu formatda bo'lsin (day.month.year)!")
        return DATE
    
async def signal_start(update: Update, context: CallbackContext):
    """Foydalanuvchiga signalni boshlash haqida xabar berish"""
    chat_id = update.message.chat_id
    context.user_data["signal"] = update.message.text.strip().split(':')[-1].strip()

    reply_markup = keyboards.signal_keyboard() if callable(keyboards.signal_keyboard) else keyboards.signal_keyboard

    await update.message.reply_text(
        f"Signal yuborish boshlandi.\n\nHar 2 daqiqada xabar yuboriladi.",
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
        send_signal_job, interval=120, first=0, name=str(chat_id),
        data={
            "chat_id": chat_id, "signal": context.user_data["signal"],
            "from_city":stationFrom, 
            "to_city": stationTo,      
            "date": date, 
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
    freeSeats_data, freeSeats = await asyncio.to_thread(checkrailway.reilway_counts, stationFrom, stationTo, date)

    for row in freeSeats_data:
        total_free_seats = int(row[-2].split(':')[-1].strip(' ').strip('\n'))
        poyezd_licanse = row[0].strip().split(':')[-1].strip().strip('\n')
        if poyezd_licanse == signal_text:
            results_signal_text = f"Poyezd number: {signal_text}\nBo'sh o'rinlar soni: {total_free_seats}"

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


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Amalyot bajarilmadi!')
    return ConversationHandler.END


