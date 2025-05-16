import telebot
import os
import requests
import json
from telebot import types
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import random

# Замените на свой токен бота
BOT_TOKEN = '7523449606:AAFzY6zj4DcLvExWWINPEfBfbbZvZ7Ou5TI'
# Замените на свой API ключ
YANDEX_WEATHER_API_KEY = '164f589d-01ab-483e-9dd6-5e49488b7412'

bot = telebot.TeleBot(BOT_TOKEN)

# Папка для сохранения файлов
FILES_DIR = 'files'
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# --- Функции для работы с файлами ---

def list_files():

    try:
        return [f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))]
    except FileNotFoundError:
        return []

def delete_file(filename):

    try:
        os.remove(os.path.join(FILES_DIR, filename))
        return True
    except FileNotFoundError:
        return False

def search_files(query):

    files = list_files()
    return [f for f in files if query.lower() in f.lower()]

# --- Функции для работы с погодой ---

def get_coordinates(city):

    geolocator = Nominatim(user_agent="telegram_bot")  # Укажите user_agent
    try:
        location = geolocator.geocode(city, timeout=5)  # Установите таймаут
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        print(f"Ошибка: Timeout при геокодировании города {city}")
        return None, None
    except GeocoderServiceError as e:
        print(f"Ошибка геокодирования: {e}")
        return None, None
    except Exception as e:
        print(f"Другая ошибка геокодирования: {e}")
        return None, None

def get_weather(city):
    """Получает данные о погоде"""
    lat, lon = get_coordinates(city)
    if lat is None or lon is None:
        print(f"Не удалось получить координаты для города {city}")
        return None

    url = f'https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}&lang=ru_RU&limit=1&hours=true'
    headers = {'X-Yandex-API-Key': YANDEX_WEATHER_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = json.loads(response.text)
        return data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return None
    except json.JSONDecodeError:
        print("Ошибка при разборе JSON ответа.")
        return None

def format_weather_message(weather_data):
    """Форматирует данные о погоде в сообщение."""
    if not weather_data:
        return "Не удалось получить данные о погоде."

    try:
        temperature = weather_data['fact']['temp']
        condition = weather_data['fact']['condition']
        humidity = weather_data['fact']['humidity']
        wind_speed = weather_data['fact']['wind_speed']

        condition_descriptions = {
            "clear": "Ясно",
            "partly-cloudy": "Малооблачно",
            "cloudy": "Облачно с прояснениями",
            "overcast": "Пасмурно",
            "drizzle": "Морось",
            "light-rain": "Небольшой дождь",
            "rain": "Дождь",
            "moderate-rain": "Умеренный дождь",
            "heavy-rain": "Сильный дождь",
            "continuous-heavy-rain": "Длительный сильный дождь",
            "showers": "Ливень",
            "wet-snow": "Дождь со снегом",
            "light-snow": "Небольшой снег",
            "snow": "Снег",
            "snow-showers": "Снегопад",
            "hail": "Град",
            "thunderstorm": "Гроза",
            "thunderstorm-with-rain": "Гроза с дождем",
            "thunderstorm-with-hail": "Гроза с градом",
        }

        description = condition_descriptions.get(condition, condition)  # Если код не найден, используем исходный код
        city = weather_data.get("geo_object", {}).get("locality", {}).get("name")

        message = f"Погода в городе {city}:\n" # Добавляем название города
        message += f"Температура: {temperature}°C\n"
        message += f"Описание: {description}\n"
        message += f"Влажность: {humidity}%\n"
        message += f"Скорость ветра: {wind_speed} м/с"
        return message
    except KeyError as e:
        print(f"Отсутствует ожидаемый ключ в данных о погоде: {e}")
        return "Ошибка при обработке данных о погоде."
    except TypeError as e:
        print(f"Ошибка типа данных при обработке данных о погоде: {e}")
        return "Ошибка при обработке данных о погоде. Возможно, город не найден."

# --- Функции для работы с цитатами ---
quotes = [
    "Будущее принадлежит тем, кто верит в красоту своей мечты. - Элеонора Рузвельт",
    "Единственный способ делать великую работу — любить то, что вы делаете. - Стив Джобс",
    "Жизнь — это то, что происходит с вами, пока вы строите планы. - Джон Леннон",
    "Успех - это не ключ к счастью. Счастье - это ключ к успеху. Если вы любите то, что делаете, вы обязательно добьетесь успеха. - Альберт Швейцер",
    "Не бойтесь совершенства, вам никогда его не достичь. - Сальвадор Дали",

]

def get_random_quote():
    """Возвращает случайную цитату."""
    return random.choice(quotes)

# --- Функции для игры "Угадай число" ---
game_states = {}

def start_guessing_game(chat_id):
    """Начинает игру "Угадай число"."""
    secret_number = random.randint(1, 100)
    game_states[chat_id] = {"number": secret_number, "attempts": 0}
    return "Я загадал число от 1 до 100. Попробуй угадать!"

def process_guess(chat_id, guess):
    """Обрабатывает попытку угадать число."""
    if chat_id not in game_states:
        return "Игра не началась. Нажмите 'Игра: Угадай число', чтобы начать."

    secret_number = game_states[chat_id]["number"]
    attempts = game_states[chat_id]["attempts"] + 1
    game_states[chat_id]["attempts"] = attempts

    if guess < secret_number:
        return "Больше."
    elif guess > secret_number:
        return "Меньше."
    else:
        del game_states[chat_id]  # Завершаем игру
        return f"Поздравляю! Ты угадал число {secret_number} за {attempts} попыток."

# --- Обработчики сообщений ---

# Состояние для поиска файла
user_states = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Список файлов")
    item2 = types.KeyboardButton("Поиск файла")
    item3 = types.KeyboardButton("Узнать погоду")
    item4 = types.KeyboardButton("Цитата дня")
    item5 = types.KeyboardButton("Игра: Угадай число")
    markup.add(item1, item2, item3, item4, item5)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Список файлов")
def list_files_handler(message):
    """Выводит список файлов с кнопками для скачивания и удаления."""
    files = list_files()
    if not files:
        bot.reply_to(message, "Файлов пока нет.")
        return

    markup = types.InlineKeyboardMarkup()
    for file in files:
        download_button = types.InlineKeyboardButton(text=f"Скачать: {file}", callback_data=f"download:{file}")
        delete_button = types.InlineKeyboardButton(text=f"Удалить: {file}", callback_data=f"delete:{file}")
        markup.add(download_button, delete_button)

    bot.send_message(message.chat.id, "Список файлов:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Узнать погоду")
def weather_query_handler(message):
    """Запрашивает город для получения погоды."""
    bot.send_message(message.chat.id, "Введите название города:")
    bot.register_next_step_handler(message, get_weather_for_city)

def get_weather_for_city(message):
    """Получает погоду для введенного города."""
    city = message.text
    weather_data = get_weather(city)
    if weather_data:
        weather_message = format_weather_message(weather_data)
        bot.send_message(message.chat.id, weather_message)
    else:
        bot.send_message(message.chat.id, "Не удалось получить данные о погоде для этого города.")

@bot.message_handler(func=lambda message: message.text == "Поиск файла")
def search_file_query(message):
    """Запрашивает поисковый запрос у пользователя."""
    bot.send_message(message.chat.id, "Введите часть названия файла для поиска:")
    user_states[message.chat.id] = "waiting_for_search_query"
    bot.register_next_step_handler(message, search_file_handler)

def search_file_handler(message):
    """Ищет файлы по запросу, полученному от пользователя."""
    if user_states.get(message.chat.id) == "waiting_for_search_query":
        query = message.text
        results = search_files(query)
        if results:
            message_text = "Результаты поиска:\n" + "\n".join(results)
            bot.send_message(message.chat.id, message_text)
        else:
            bot.send_message(message.chat.id, "Файлы не найдены.")
        user_states.pop(message.chat.id, None)
    else:
        bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, используйте меню.")

@bot.message_handler(func=lambda message: message.text == "Цитата дня")
def quote_of_the_day(message):
    """Отправляет случайную цитату."""
    quote = get_random_quote()
    bot.send_message(message.chat.id, quote)

@bot.message_handler(func=lambda message: message.text == "Игра: Угадай число")
def handle_guessing_game_start(message):
    """Обрабатывает нажатие кнопки 'Игра: Угадай число'."""
    chat_id = message.chat.id
    bot.send_message(chat_id, start_guessing_game(chat_id))
    bot.register_next_step_handler(message, handle_guess)

def handle_guess(message):
    """Обрабатывает попытки угадать число."""
    chat_id = message.chat.id
    try:
        guess = int(message.text)  # Преобразуем ввод пользователя в число
        result = process_guess(chat_id, guess)  # Обрабатываем попытку
        bot.send_message(chat_id, result)  # Отправляем результат
        if chat_id in game_states:
            bot.register_next_step_handler(message, handle_guess)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите целое число.")
        bot.register_next_step_handler(message, handle_guess)
    except Exception as e:
        print(f"Ошибка в игре 'Угадай число': {e}")
        bot.send_message(chat_id, "Произошла ошибка в игре. Попробуйте начать заново.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Сохраняет отправленный файл."""
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        filename = message.document.file_name
        filepath = os.path.join(FILES_DIR, filename)

        with open(filepath, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, f"Файл '{filename}' сохранен.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при сохранении файла: {e}")

# --- Обработчик CallbackQuery (для кнопок) ---

@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    """Обрабатывает нажатия на кнопки."""
    data = call.data
    if data.startswith('download:'):
        filename = data[len('download:'):]
        filepath = os.path.join(FILES_DIR, filename)
        try:
            with open(filepath, 'rb') as file:
                bot.send_document(call.message.chat.id, file, caption=f"Файл: {filename}")
        except FileNotFoundError:
            bot.answer_callback_query(call.id, "Файл не найден.")
        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка при отправке файла: {e}")

    elif data.startswith('delete:'):
        filename = data[len('delete:'):]
        if delete_file(filename):
            bot.answer_callback_query(call.id, f"Файл '{filename}' удален.")
            bot.edit_message_text("Список файлов:", call.message.chat.id, call.message.message_id)  # Удаляем сообщение
            list_files_handler(call.message) # Отправляем новый список
        else:
            bot.answer_callback_query(call.id, f"Файл '{filename}' не найден.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()