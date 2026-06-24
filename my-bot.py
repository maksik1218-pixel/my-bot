import telebot
from telebot import apihelper, types
import time
import sqlite3
import os

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('user.db')
    cur = conn.cursor()

    cur.execute('''
                CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                username TEXT,
                )
                ''')
    conn.commit()
    cur.close()
    conn.close()




def main_menu_keyboard():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton(text = ' 💅Услуги')
        btn2 = types.KeyboardButton(text = '💰 Прайс-лист')
        btn3 = types.KeyboardButton(text = '📅Записаться')
        btn4 = types.KeyboardButton(text = '📱 Контакты')
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        return markup

        bot.send_message(message.chat.id, f"Добро пожаловать в 'Салон', {message.from_user.first_name}! \nВыбирайте нужный раздел в меню ниже:", reply_markup=markup)
# Обработчик нажатий

@bot.message_handler(content_types=['text'])
def handle_text(message):
     if message.text == '💅Услуги':
          text = ('Наши услуги: \n')
          'Маникюр и педикюр\n'
          'Стрижки и окрашивание\n'
          'Уход за лицом\n'
          'Макияж'
          
          bot.send_message(message.chat.id, text)
     
     elif message.text == '💰 Прайс-лист':
          text = ('Прайс-лист\n')
          '- Маникюр: от 1500\n'
          '- Стрижка: от 2000\n'
          
          bot.send_message(message.chat.id, text)

     elif message.text == '📱 Контакты':
          bot.send_message(message.chat.id, '🏠 Адрес: ул Красивая, д.10\n 📞 Тел: 7 (999) 000-00-00\n ⏰ Часы работы: 10:00 - 21:00')

     elif message.text == '📅Записаться':
          msg = bot.send_message(message.chat.id, 'Введите ваше имя и желаемую услугу:')
          bot.register_next_step_handler(msg, process_name)

# Процесс записи 
def process_name(message):
     user_data = {}
     user_data['name'] = message.text
     msg = bot.send_message(message.chat.id, 'Введите ваш номер телефона для связи')
     bot.register_next_step_handler(msg, process_phone, user_data)

def process_phone(message, user_data):
     phone = message.text
     name = user_data['name']



@bot.message_handler(commands=['start'])
def start(message):
     conn = sqlite3.connect('salon_beauty.sql')
     cur = conn.cursor()
     cur.execute('INSERT INTO appointments(user_id, client_name, phone) VALUES (?, ?, ?)',
                 (message.from_user.id, process_name, process_phone))
     conn.commit()
     conn.close()

     bot.send_message(message.chat.id, f'✅Спасибо мы свяжемся с вами по номеру {process_phone} для подтверждения записи.')








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