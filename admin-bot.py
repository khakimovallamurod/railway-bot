from telegram.ext import Updater, CommandHandler, MessageHandler, filters, ConversationHandler, Application, CallbackQueryHandler
from telegram import Update
from config import get_token
import handlers
import asyncio

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

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('viewactives', handlers.view_actives))
    dp.add_handler(CallbackQueryHandler(handlers.stop_signal, pattern="stop_signal"))
    job_queue = dp.job_queue
    job_queue.start()  
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handlers.restart_active_signals(dp))  # Qayta yuklash
    
    dp.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == '__main__':
    main()