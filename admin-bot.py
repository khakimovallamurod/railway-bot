from telegram.ext import Updater, CommandHandler, MessageHandler, filters, ConversationHandler, Application
from config import get_token
import handlers


def main():
    TOKEN = get_token()

    dp = Application.builder().token(TOKEN).build()

    dp.add_handler(CommandHandler('start', handlers.start))
    
    user_test_handler = ConversationHandler(
        entry_points=[CommandHandler('railwaycount', handlers.railway_start)],
        states={
            handlers.DATE: [MessageHandler(filters.TEXT, handlers.railway_count)],
        },
        fallbacks=[CommandHandler('cancel', handlers.cancel)]
    )
    dp.add_handler(user_test_handler)

    dp.run_polling()

if __name__ == '__main__':
    main()