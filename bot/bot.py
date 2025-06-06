import os
import random
import logging
import html

import random
from telegram import Update, Chat, Message, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes,
    CallbackContext,
    MessageHandler,
    CallbackQueryHandler,
    filters, 
    PicklePersistence
)
from telegram.error import TelegramError

from markov_gen import generate_markov_text
from draw_func import circle_picture, face_picture
from spam_validator import validate_spam_text
from very_sus import very_sus

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

async def very_sus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = await very_sus()
    await update.message.reply_text(answer)

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

    text = update.effective_message.text or update.effective_message.caption
    # no text, we cant check that for spam
    if text is None or text == "": 
        logger.debug(f"no text in message: {update.effective_message}")
        return

    spam_probability = await validate_spam_text(text)
    logger.debug(f"checked message: {text}\nspam prob: {spam_probability}")
    if spam_probability >= 1:
        logger.debug(f"It's ABSOLUTELY spam!!!\nmessage:{text}\nfrom: {user.name}")
        try:
            await update.effective_chat.delete_message(message_id=update.message.message_id)
            await update.effective_chat.ban_member(user_id=user.id)
        except Exception as e:
            logger.debug(f"Error deleting message: {e} or banning user: {user}")
    elif spam_probability >= 0.65:
        logger.debug(f"It's very probably spam!!!\nmessage:{text}\nfrom: {user.name}")
        try:
            await update.effective_chat.delete_message(message_id=update.message.message_id)

            await notify_admins_about_delete(update.effective_chat, update.message, context.bot, "spam")
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
        await update.message.reply_text(f"Этот текст - СПАМ ({spam_probability})")
    else:
        await update.message.reply_text(f"Думаю, не спа ({spam_probability})")
    
async def notify_admins_about_delete(chat: Chat, message: Message, bot: Bot, reason: str):
    chat_link = f"<a href='https://t.me/{chat.username}'>{html.escape(chat.title)}</a>" if chat.username else html.escape(chat.title)
    user_mention = f"<a href='tg://user?id={message.from_user.id}'>{html.escape(message.from_user.name)}</a>"

    notification = "" 
    if reason == "spam":
        notification = f"Из чата {chat_link} было удалено сообщение похожее на спам:\n\n"
    else:
        notification = f"Из чата {chat_link} было удалено сообщение по причине: {reason}\n\n"
    notification += f"{user_mention}\n"
    notification += f"<blockquote>{html.escape(message.text)}</blockquote>\n\n"
    notification += f"<i>Если вы считаете, что это ошибка, восстановите сообщение через настройки чата</i>"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Забанить пользователя", callback_data=f"ban_user:{chat.id}:{message.from_user.id}")]
    ])

    for admin in await chat.get_administrators():
        try:
            await bot.send_message(
                chat_id=admin.user.id,
                text=notification,
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.debug(f"Failed to send notification to admin {admin.user.id}: {e}")

async def ban_user_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    bot: Bot = context.bot

    # Extract data from callback_data
    _, chat_id, user_id = query.data.split(':')
    chat_id = int(chat_id)
    user_id = int(user_id)

    # Check if the user who pressed the button is an admin of the chat
    try:
        chat_member = await bot.get_chat_member(chat_id, query.from_user.id)
        if chat_member.status not in ['creator', 'administrator']:
            await query.edit_message_text("У вас нет прав для выполнения этого действия.")
            return
    except TelegramError:
        await query.edit_message_text("Не удалось проверить права администратора.")
        return

    try:
        # Ban the user
        await bot.ban_chat_member(chat_id, user_id)
        
        # Notify the admin that the user was banned
        await query.edit_message_text(
            text=f"Пользователь (ID: {user_id}) был успешно забанен в чате (ID: {chat_id}).",
            parse_mode='HTML'
        )
    except Exception as e:
        # If there's an error, inform the admin
        await query.edit_message_text(
            text=f"Не удалось забанить пользователя (ID: {user_id}) в чате (ID: {chat_id}). Ошибка: {str(e)}",
            parse_mode='HTML'
        )

async def chat_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if command was called by admin
    if not update.effective_chat:
        logger.debug(f"This command can only be used in a chat. Ignore")
        return
    try:
        user = update.effective_user
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        
        if chat_member.status not in ['creator', 'administrator']:
            logger.debug(f"This command is only available to chat administrators. Ignore")
            return
        
        chat = update.effective_chat
        chat_info = f"""
        Chat Information:
        ID: {chat.id}
        Type: {chat.type}
        Title: {chat.title}
        Members count: {await chat.get_member_count()}
        Username: {f'@{chat.username}' if chat.username else 'No username'}
        Invite link: {await chat.export_invite_link() if chat.type != 'private' else 'N/A'}
        """
        await update.message.reply_text(chat_info)
    except Exception as e:
        logger.error(f"Error in chat_info: {e}")

def main():
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        raise ValueError("No token provided")
    
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(TOKEN).persistence(persistence).build()
    
    application.add_handler(CommandHandler("start", start_command, filters.ChatType.PRIVATE))

    application.add_handler(CommandHandler("draw_circle", draw_circle))
    application.add_handler(CommandHandler("draw_face", draw_face))

    application.add_handler(CommandHandler("markov", markov_command))
    application.add_handler(CommandHandler("sus", very_sus_command))

    application.add_handler(CommandHandler("spam_check", spam_check, filters.ChatType.PRIVATE))

    application.add_handler(CommandHandler("chat_info", chat_info_command))

    # SPAM tracker
    application.add_handler(MessageHandler(filters.ALL, validate_spam_updates), 2)
    application.add_handler(CallbackQueryHandler(ban_user_callback, pattern="^ban_user:"))
    application.add_handler(MessageHandler(filters.ALL, track_updates), -1)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
