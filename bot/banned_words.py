banned_texts = [
    "казино №",
    "пишите плюс в личные сообщения",
    "удаленка с выгодными условиями",
    "напиши «+» в лс",
    "Haпиши “+” в личкy",
    "напишите мне «плюс»",
    "напишите \"плюс\", объясню",
    "возможность дополнительного дохода на выгодных условиях",
    "Доход от * рублей в день",
    "кто хочет зарабатывать ежедневно от",
    "Ищу *–* человек, кто хочет зарабатывать ежедневно от *-* рублей",
    "Пассивный доход, * долларов в день",
    "Ищу * активных людей",
    "нужно * человека, доход от * долларов в неделю",
    "Ищу * человека в команду доход от * долларов в неделю",
    "пишите старт в личные сообщения",
    "СРОЧНО ВОЗЬМУ на удаленную деятельность *-* человека",
    "За подробностями пишите + в лс",
    "— твой билет в новый мир",
    "переходи по ссылке",
    "Открыт набор с доходом",
    "Удалёнка, новый форма от ",
    "выйти на доход от ",
    "Нужны люди для дела, доходность от ",
    "гибкая неполная занятость, с выходом до * долларов в день",
    "в поиске заинтересованных в доп заработке"
]

def contains_banned_texts(message: str) -> bool:
    for banned_text in banned_texts:
        banned_text = banned_text.replace("*", "")
        banned_text = ' '.join(banned_text.split())
        banned_text = banned_text.lower()

        cleaned_message = clean_message(message).lower()

        if banned_text in cleaned_message:
            return True
    return False

# Удаляем все цифры
# Удаляем эмодзи (Unicode символы, которые не являются буквами или знаками препинания)
# Удаляем лишние пробелы между словами
def clean_message(message: str) -> str:
    message = ''.join(char for char in message if not char.isdigit())
    
    message = ''.join(char for char in message if char.isprintable() and not char.isdigit())
    
    message = ' '.join(message.split())
    
    return message