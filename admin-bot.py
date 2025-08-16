from telegram.ext import (
    CommandHandler, MessageHandler, filters, 
    ConversationHandler, Application, CallbackQueryHandler
)
from telegram import Update
from config import get_token
import handlers

async def setup_scheduler(app: Application):
    """Bot ishga tushgandan keyin scheduler start qilinadi"""
    handlers.scheduler.start()
    
    await handlers.restart_active_signals(app)

def main():
    TOKEN = get_token()

    dp = Application.builder().token(TOKEN).post_init(setup_scheduler).build()

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
        allow_reentry=True

    )
    edit_comment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handlers.ask_new_comment, pattern='edit_comment')],
        states={
            handlers.EDIT_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.save_new_comment)]
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
        allow_reentry=True
    )

    dp.add_handler(edit_comment_conv)
    dp.add_handler(conv_handler)
    dp.add_handler(admin_handler)
    dp.add_handler(CommandHandler('viewactives', handlers.view_actives))
    dp.add_handler(CallbackQueryHandler(handlers.stop_signal, pattern="stop_signal"))

    dp.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == '__main__':
    main()
