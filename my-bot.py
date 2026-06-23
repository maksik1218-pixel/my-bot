import telebot
from telebot import apihelper, types
import time
import sqlite3
import os

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) # замените на реальный токен

# PROXY_URL = 'http://a56j7MHTi:8rk9jmyZ7@142.111.253.156:64874'
# apihelper.proxy = {'http': PROXY_URL, 'https': PROXY_URL}


# ---------- Функции для работы с БД ----------
def init_db():
    """Создаёт таблицу users, если её нет."""
    conn = sqlite3.connect('user.sql')
    cursor = conn.cursor()
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )''')
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def add_user(user_id, username, first_name):
    """Добавляет пользователя в таблицу (если его ещё нет)."""
    conn = sqlite3.connect('user.sql')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT OR IGNORE INTO users (id, username, first_name) VALUES (?, ?, ?)',
            (user_id, username, first_name)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ---------- Функция создания клавиатуры (вынесена отдельно) ----------
def main_menu():
    """Возвращает объект InlineKeyboardMarkup с кнопками."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('👤Обо мне', callback_data='about')
    btn2 = types.InlineKeyboardButton('💰 Услуги', callback_data='services')
    btn3 = types.InlineKeyboardButton('📂 Портфолио', callback_data='portfolio')
    btn4 = types.InlineKeyboardButton('📱 Контакты', callback_data='contacts')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    return markup

# ---------- Обработчик команды /start (ОДИН, правильно написанный) ----------
@bot.message_handler(commands=['start'])
def start(message):
    # 1. Инициализация БД
    init_db()
    # 2. Добавление пользователя
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    # 3. Получаем клавиатуру
    keyboard = main_menu()
    # 4. Отправляем приветствие с клавиатурой
    bot.send_message(message.chat.id, 'Добро пожаловать! Выберите раздел:', reply_markup=keyboard)

# ---------- Обработчик нажатий на кнопки ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Формируем текст в зависимости от нажатой кнопки
    if call.data == 'about':
        text = '👤 Обо мне: я разработчик Telegram-ботов.'
    elif call.data == 'services':
        text = '💰 Услуги: создание ботов, автоматизация, парсинг.'
    elif call.data == 'portfolio':
        text = '📂 Портфолио: примеры работ можно посмотреть на моём сайте.'
    elif call.data == 'contacts':
        text = '📱 Контакты: @my_username или почта example@mail.ru'
    else:
        text = 'Раздел в разработке.'

    # Отправляем сообщение с текстом (исправлено – теперь текст правильно формируется)
    bot.send_message(call.message.chat.id, text)
    # Отвечаем на callback, чтобы убрать «часики» у кнопки
    bot.answer_callback_query(call.id)

# ---------- Основной цикл ----------
while True:
    try:
        print('Бот запускается')
        bot.get_me()
        print('Бот готов к работе')
        print(bot.get_me())
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f'Бот упал: {e}. Перезапуск через 5 секунд')
        time.sleep(5)