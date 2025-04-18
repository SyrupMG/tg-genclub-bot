import time
from datetime import datetime
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.types import UserProfilePhoto
import asyncio
import sys
from collections import defaultdict
import csv
import os
from dotenv import load_dotenv

# Загружаем переменные среды из .env файла
load_dotenv()

class TelegramAnalyzer:
    def __init__(self):
        # Пытаемся получить API-данные из переменных среды
        self.api_id = os.environ.get('TELEGRAM_API_ID')
        self.api_hash = os.environ.get('TELEGRAM_API_HASH')
        self.client = None
        self.suspicious_users = []
    
    async def interactive_login(self):
        """Интерактивная авторизация в аккаунт Telegram"""
        print("Добро пожаловать в анализатор подозрительных пользователей Telegram.")
        print("-" * 60)
        
        # Проверяем наличие API-данных в переменных среды
        if not self.api_id or not self.api_hash:
            print("API-данные не найдены в переменных среды (.env).")
            self.api_id = input("Введите ваш API ID: ")
            self.api_hash = input("Введите ваш API Hash: ")
        else:
            print("API-данные успешно загружены из переменных среды.")
        
        # Создаем клиент и авторизуемся
        self.client = TelegramClient('anon_session', self.api_id, self.api_hash)
        await self.client.start()
        
        if not await self.client.is_user_authorized():
            print("Требуется авторизация...")
            phone = input("Введите ваш номер телефона: ")
            await self.client.send_code_request(phone)
            code = input("Введите полученный код: ")
            await self.client.sign_in(phone, code)
        
        print("Авторизация успешна!")
    
    async def analyze_channel(self):
        """Анализ пользователей канала"""
        channel_input = input("Введите @username или ссылку на канал: ")
        
        try:
            channel = await self.client.get_entity(channel_input)
        except ValueError:
            print(f"Ошибка: Канал '{channel_input}' не найден.")
            return
        
        print(f"Начинаю анализ канала: {channel.title}")
        
        # Получаем всех участников канала
        all_participants = []
        print("Получаю список участников...")
        
        try:
            all_participants = await self.client.get_participants(channel)
            print(f"Найдено {len(all_participants)} участников.")
        except Exception as e:
            print(f"Ошибка при получении участников: {e}")
            return
        
        # Анализ каждого пользователя
        results = []
        
        for i, user in enumerate(all_participants):
            sys.stdout.write(f"\rАнализ пользователя {i+1}/{len(all_participants)}")
            sys.stdout.flush()
            
            suspiciousness = 100  # Базовый уровень подозрительности
            reasons = []
            
            # Проверка 1: Удаленный аккаунт
            if user.deleted:
                suspiciousness += 1000
                reasons.append("Удаленный аккаунт (+1000)")
                results.append({
                    "user_id": user.id,
                    "username": "Удаленный аккаунт",
                    "suspiciousness": suspiciousness,
                    "reasons": reasons
                })
                continue
            
            # Получаем полную информацию о пользователе
            try:
                full_user = await self.client(functions.users.GetFullUserRequest(id=user.id))
                user_info = full_user.full_user
            except Exception as e:
                print(f"\nОшибка при получении информации о пользователе {user.id}: {e}")
                continue
            
            # Проверка 2: Отсутствие фото профиля
            if not user.photo or isinstance(user.photo, types.UserProfilePhotoEmpty):
                suspiciousness += 20
                reasons.append("Отсутствует фото профиля (+20)")
            
            # Проверка 3: Дата публикации фотографий
            if not user.photo or not isinstance(user.photo, types.UserProfilePhotoEmpty):
                try:
                    photos = await self.client.get_profile_photos(user.id)
                    
                    if len(photos) >= 2:
                        # Группируем фото по времени загрузки с допуском в 1 минуту
                        photo_dates = defaultdict(list)
                        
                        for photo in photos:
                            # Округляем до минуты
                            minute_timestamp = int(photo.date.timestamp() // 60) * 60
                            photo_dates[minute_timestamp].append(photo)
                        
                        for timestamp, grouped_photos in photo_dates.items():
                            if len(grouped_photos) >= 2:
                                suspiciousness += 100  # За первые 2 фото
                                reasons.append(f"Найдены {len(grouped_photos)} фото, загруженные одновременно (+{100 + 50*(len(grouped_photos)-2)})")
                                
                                # Добавляем по 50 за каждое последующее фото
                                if len(grouped_photos) > 2:
                                    suspiciousness += 50 * (len(grouped_photos) - 2)
                
                except Exception as e:
                    print(f"\nОшибка при анализе фотографий пользователя {user.id}: {e}")
            
            # Проверка 4: Наличие личного канала
            if user_info.about and ("t.me/" in user_info.about or "@" in user_info.about):
                suspiciousness -= 20
                reasons.append("Указан личный канал (-20)")
            
            # Проверка 5: Отсутствие описания
            if not user_info.about:
                suspiciousness += 20
                reasons.append("Отсутствует описание (+20)")
            
            results.append({
                "user_id": user.id,
                "username": user.username if user.username else f"{user.first_name} {user.last_name if user.last_name else ''}",
                "suspiciousness": suspiciousness,
                "reasons": reasons
            })
        
        print("\nАнализ завершен!")
        return results
    
    def save_results(self, results):
        """Сохранение результатов в файл CSV"""
        if not results:
            print("Нет результатов для сохранения.")
            return
        
        # Сортировка по уровню подозрительности
        sorted_results = sorted(results, key=lambda x: x["suspiciousness"], reverse=True)
        
        filename = f"suspicious_users_{int(time.time())}.csv"
        
        with open(filename, "w", encoding="utf-8", newline='') as f:
            fieldnames = ['ID', 'Имя', 'Подозрительность', 'Причины', 'Ссылка']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for user in sorted_results:
                # Формируем ссылку на профиль в Telegram
                if user['username']:
                    tg_link = f"https://t.me/{user['username']}"
                else:
                    tg_link = f"tg://user?id={user['user_id']}"
                
                writer.writerow({
                    'ID': user['user_id'],
                    'Имя': user['username'],
                    'Подозрительность': user['suspiciousness'],
                    'Причины': '; '.join(user['reasons']),
                    'Ссылка': tg_link
                })
        
        print(f"Результаты сохранены в файл {filename}")

async def main():
    analyzer = TelegramAnalyzer()
    await analyzer.interactive_login()
    
    while True:
        print("\nВыберите действие:")
        print("1. Анализировать канал")
        print("2. Выход")
        
        choice = input("Ваш выбор: ")
        
        if choice == "1":
            results = await analyzer.analyze_channel()
            if results:
                analyzer.save_results(results)
        elif choice == "2":
            break
        else:
            print("Неверный выбор. Попробуйте еще раз.")

if __name__ == "__main__":
    asyncio.run(main())
