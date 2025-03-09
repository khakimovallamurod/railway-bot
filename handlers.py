from telegram.ext import CallbackContext, ConversationHandler
from telegram import Update
import checkrailway

DATE = range(1)

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text(
        text=f"""Assalomu aleykum {user.full_name}. Ushbu bot yordamida joylar sonini aniqlashingiz mumkin. /railwaycount""",
    )

async def railway_start(update: Update, context: CallbackContext):
    await update.message.reply_text("Sanani kiriting ushbu formatda (day.month.year)!")
    return DATE

async def railway_count(update: Update, context: CallbackContext):
    context.user_data['date'] = update.message.text.strip()
    date = context.user_data['date']
    if checkrailway.is_valid_date(date):
        freeSeats = checkrailway.reilway_counts(date=date)
        await update.message.reply_text(f"Bo'sh joylar soni: {freeSeats}")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Xato kiritdingiz, ushbu formatda bo'lsin (day.month.year)!")
        return DATE

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Amalyot bajarilmadi!')
    return ConversationHandler.END


    