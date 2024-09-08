import os

from telegram import Update
from telegram.ext import Application, CommandHandler

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your Telegram bot.")

def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No token provided")

    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()