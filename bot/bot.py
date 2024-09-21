import os
import random
import logging

import random
from telegram import Update, Chat, Message, Bot
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    MessageHandler, 
    filters, 
    PicklePersistence
)

from markov_gen import generate_markov_text
from draw_func import circle_picture, face_picture
from spam_validator import validate_spam_text

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("tg-genclub-bot")
logger.setLevel(logging.DEBUG)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_called = context.user_data.get("start_called", False)
    if start_called:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Ты уже стартовал чат, попробуй что-нибудь более изобретательное"
            )
    else:
        context.user_data["start_called"] = True
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Привет! Я Клубень! Не знаю, что ты делаешь у меня в личке, но тебе стоит сходить в @gen_c"
            )

async def draw_circle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:    
    await update.message.reply_photo(circle_picture())

async def draw_face(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_photo(face_picture())

async def markov_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markov_text = generate_markov_text()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=markov_text)

async def sus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_data = context.chat_data

    # Get all users in the chat
    users = [user for user in chat_data.keys() if user.startswith("user_data_")]

    # Filter users with no text messages
    silent_users = [user for user in users if chat_data[user].get("messages_count", 0) == 0]

    if not silent_users:
        await update.message.reply_text("Сейчас нет никого, кто вызывает у меня подозрения")
        return

    # Select a random silent user
    random_user_key = random.choice(silent_users)
    user_id = int(random_user_key.split("_")[-1])

    # Get the user's information
    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    user = chat_member.user

    # Create a mention for the user
    user_mention = user.mention_html()

    await update.message.reply_html(f"SUS пользователь: {user_mention}")

async def track_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return

    user_data_key = f"user_data:{user.id}"
    user_data: dict = context.chat_data.setdefault(user_data_key, dict())

    user_data["updates_count"] = user_data.get("updates_count", 0) + 1

    if update.message and update.message.text:
        user_data["messages_count"] = user_data.get("messages_count", 0) + 1

async def validate_spam_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return

    user_data_key = f"user_data:{user.id}"
    user_data: dict = context.chat_data.setdefault(user_data_key, dict())

    messages_count = user_data.get("messages_count", 0)

    # if user already wrote something more than 2 times, then skip and suggest, that they are not spammer
    if messages_count >= 2:
        logger.debug(f"user {user.id} already has {messages_count} message, so no spam check")
        return

    text = update.effective_message.text
    # no text, we cant check that for spam
    if text is None or text == "": 
        logger.debug(f"no text in message: {update.effective_message}")
        return

    spam_probability = await validate_spam_text(text)
    logger.debug(f"checked message: {text}\nspam prob: {spam_probability}")
    if spam_probability >= 0.65:
        logger.debug(f"It's very probably spam!!!\nmessage:{text}\nfrom: {user.name}")
        try:
            await update.effective_chat.delete_message(message_id=update.message.message_id)

            await notify_admins_about_delete(update.effective_chat, update.message, context.bot, "потенциально спам")
        except Exception as e:
            logger.debug(f"Error deleting message: {e}")
    else: 
        return
    
async def spam_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the text after the command
    text = ' '.join(context.args)

    if not update.message: 
        logger.warning(f"А как мы вообще сюда попали?\nupdate: {update}")
        return
    
    if not text:
        await update.message.reply_text("После команды должен быть текст для проверки")
        return

    spam_probability = await validate_spam_text(text)
    is_spam = spam_probability >= 0.65
    
    if is_spam:
        await update.message.reply_text("Этот текст - СПАМ")
    else:
        await update.message.reply_text("Думаю, не спам")
    
async def notify_admins_about_delete(chat: Chat, message: Message, bot: Bot, reason: str):
    admins = await chat.get_administrators()
    notification = f"Из чата {chat.title} было удалено сообщение по причине: спам\n"
    notification += f"Контент сообщения: {message.text}\n\n"
    notification += f"Если вы считаете, что это ошибка, восстановите сообщение через настройки чата. В случае, если это не ошибка, возможно, стоит забанить пользователя и удалить пользователя"

    for admin in admins:
        try:
            await bot.send_message(
                chat_id=admin.user.id,
                text=notification
            )
        except Exception as e:
            logger.debug(f"Failed to send notification to admin {admin.user.id}: {e}")

def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No token provided")
    
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(token).persistence(persistence).build()
    
    application.add_handler(CommandHandler("start", start_command, filters.ChatType.PRIVATE))

    application.add_handler(CommandHandler("draw_circle", draw_circle))
    application.add_handler(CommandHandler("draw_face", draw_face))

    application.add_handler(CommandHandler("markov", markov_command))
    application.add_handler(CommandHandler("sus", sus_command))

    application.add_handler(CommandHandler("spam_check", spam_check, filters.ChatType.PRIVATE))
    # SPAM tracker
    application.add_handler(MessageHandler(filters.ALL, validate_spam_updates), 2)
    application.add_handler(MessageHandler(filters.ALL, track_updates), -1)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
