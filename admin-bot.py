from telegram.ext import (
    CommandHandler, MessageHandler, filters, 
    ConversationHandler, Application, CallbackQueryHandler
)
from telegram import Update
from config import get_token
import handlers
import asyncio

async def start_jobs(dp):
    job_queue = dp.job_queue
    await job_queue.start()

    await handlers.restart_active_signals(dp)

def main():
    TOKEN = get_token()

    dp = Application.builder().token(TOKEN).build()

    dp.add_handler(CommandHandler('start', handlers.start))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("railwaycount", handlers.railway_start)],
        states={
            handlers.FROM_CITY: [CallbackQueryHandler(handlers.from_city_selected)],
            handlers.TO_CITY: [CallbackQueryHandler(handlers.to_city_selected)],
            handlers.DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.select_class)],
            handlers.SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.railway_count)],
            handlers.SIGNAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.signal_start)],
            handlers.ADD_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.add_comment_signal)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
        allow_reentry=True
    )

    admin_handler = ConversationHandler(
        entry_points=[CommandHandler('addadmin', handlers.admin_start)],
        states={
            handlers.ID_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.insert_admin)]
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(admin_handler)
    dp.add_handler(CommandHandler('viewactives', handlers.view_actives))
    dp.add_handler(CallbackQueryHandler(handlers.stop_signal, pattern="stop_signal"))

    asyncio.get_event_loop().run_until_complete(start_jobs(dp))

    dp.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == '__main__':
    main()
