from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update
import checkrailway
import keyboards

FROM_CITY, TO_CITY, DATE, SIGNAL = range(4)

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text(
        text=f"""Assalomu aleykum {user.full_name}. Ushbu bot yordamida joylar sonini aniqlashingiz mumkin. /railwaycount""",
    )

async def railway_start(update: Update, context: CallbackContext):
    await update.message.reply_text("Poyezd tanlash boshlandi!!!")
    
    return await get_from_city(update, context)

async def get_from_city(update: Update, context: CallbackContext):
    await update.message.reply_text(
        text="Qayerdan borishingizni tanlang:",
        reply_markup=keyboards.get_viloyats()
    )
    return FROM_CITY

async def from_city_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['from_city'] = query.data
    
    return await get_to_city(update, context)

async def get_to_city(update: Update, context: CallbackContext):
    query = update.callback_query
    
    await query.message.reply_text(
        text="Qayerga borishingizni tanlang:",
        reply_markup=keyboards.get_viloyats()
    )
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
    
    stationFrom = context.user_data['from_city'].split(':')[1]
    stationTo = context.user_data['to_city'].split(':')[1]

    if checkrailway.is_valid_date(date):
        freeSeats_data, freeSeats = checkrailway.reilway_counts(stationFrom, stationTo, date=date)
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
    chat_id = update.message.chat_id
    context.user_data["signal"] = update.message.text.strip()

    reply_markup = keyboards.signal_keyboard  # Ishonch hosil qiling, bu noto‘g‘ri emas
    await update.message.reply_text(
        f"Signal yuborish boshlandi.\n\nHar 5 daqiqada xabar yuboriladi.",
        reply_markup=reply_markup
    )

    # Har 5 daqiqada signal yuborish uchun
    context.job_queue.run_repeating(
        send_signal_job, interval=300, first=0, chat_id=chat_id, name=str(chat_id)
    )

async def send_signal_job(context: CallbackContext):
    """Rejalashtirilgan signal xabari"""
    job = context.job  # context.job bo‘lmasa, bu joyda xatolik chiqadi

    if job and hasattr(job, 'chat_id'): 
        chat_id = job.chat_id
    else:
        print("Xatolik: chat_id yo‘q!")  # Log yozish
        return
    
    user_data = context.application.user_data  # Umumiy user_data
    chat_data = user_data.get(chat_id, {})  # Har bir chat uchun user_data
    signal_text = chat_data.get("signal", "Noma’lum")
    await context.bot.send_message(chat_id=chat_id, text=f"Signal: {signal_text}")


async def stop_signal(update: Update, context: CallbackContext):
    """Signal yuborishni to‘xtatish"""
    query = update.callback_query
    await query.answer()

    # Avvalgi ishlarni to‘xtatish
    current_jobs = context.job_queue.get_jobs_by_name(str(query.message.chat_id))
    for job in current_jobs:
        job.schedule_removal()

    await query.message.reply_text("🚫 Signal yuborish to‘xtatildi.")

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Amalyot bajarilmadi!')
    return ConversationHandler.END


