import os
import random
import io

import markovify
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from collections import defaultdict
from PIL import Image, ImageDraw

with open("markov.txt", "r", encoding="utf-8") as f:
    text = f.read()
model = markovify.Text(text)

# Dictionary to store users and their message count
user_messages = defaultdict(int)

def generate_markov_text(sentences=5):
    result = []
    for _ in range(sentences):
        sentence = model.make_sentence(tries=100)
        if sentence:
            result.append(sentence)
    return " ".join(result)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def markov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markov_text = generate_markov_text()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=markov_text)

async def silent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Get all chat members
    chat_members = await context.bot.get_chat_administrators(chat_id)
    
    silent_users = []
    for member in chat_members:
        user = member.user
        if user_messages[user.id] == 0 and not user.is_bot:
            silent_users.append(user.full_name)
    
    if silent_users:
        random_silent_user = random.choice(silent_users)
        response = f"A random silent user: {random_silent_user}"
    else:
        response = "No silent users found."
    
    await context.bot.send_message(chat_id=chat_id, text=response)

async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_messages[user_id] += 1

def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No token provided")
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draw_circle", draw_circle))
    application.add_handler(CommandHandler("markov", markov))
    application.add_handler(CommandHandler("silent", silent))
    
    # Add a message handler to track user messages
    application.add_handler(MessageHandler(filters.ALL, track_messages))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
