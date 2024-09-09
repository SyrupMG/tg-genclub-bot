import os

from telegram import Update
from telegram.ext import Application, CommandHandler

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your Telegram bot. And this was updated from git")

async def draw_circle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    WIDTH = 512
    HEIGHT = 512

    img = Image.new('RGB', (WIDTH, HEIGHT), color='white')
    draw = ImageDraw.Draw(img)
    
    center_x = random.randint(0, WIDTH)
    center_y = random.randint(0, HEIGHT)
    radius = random.randint(10, WIDTH / 2)
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    draw.ellipse([center_x-radius, center_y-radius, center_x+radius, center_y+radius], fill=color)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    await update.message.reply_photo(img_byte_arr)

def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No token provided")

    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draw_circle", draw_circle))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
