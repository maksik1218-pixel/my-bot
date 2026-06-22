
import telebot
from telebot import apihelper
import time
from telebot import types
import requests
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Прокси только для телеграм-бота
PROXY_URL = 'http://xdskxhwf:6uy1n5ujov90@198.105.121.200:6462'
apihelper.proxy = {'http': PROXY_URL, 'https': PROXY_URL}

# ----------------- Глобальные переменные для настроек -----------------
# Здесь хранятся последние извлечённые email
last_emails = []

# Настройки отправителя и письма (заполняются пользователем)
sender_email = None
sender_password = None
email_subject = None
email_body = None

# Флаг, что настройки уже введены
settings_ready = False

# ----------------- Обработчики команд -----------------

@bot.message_handler(func=lambda message: message.text.lower() == 'привет')
def hello_message(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

@bot.message_handler(func=lambda message: message.text.lower() == 'id')
def id_message(message):
    bot.reply_to(message, f'ID: {message.from_user.id}')

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, '<b>Все</b> <u>доступные команды бота</u>', parse_mode='html')

# ----------------- Функция парсинга email (без прокси) -----------------
def extract_emails(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        if response.encoding is None:
            response.encoding = 'utf-8'
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found = re.findall(email_pattern, response.text)
        return sorted(set(found))
    except Exception as e:
        print(f'Ошибка парсинга: {e}')
        return None

# ----------------- Команда /start – главное меню -----------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_parse = types.KeyboardButton('Парсить email')
    btn_send = types.KeyboardButton('Отправить рассылку')
    btn_settings = types.KeyboardButton('Изменить настройки')
    markup.row(btn_parse)
    markup.row(btn_send)
    markup.row(btn_settings)
    bot.send_message(
        message.chat.id,
        'Привет! Нажми "Парсить email", затем отправь ссылку на сайт.\n'
        'После парсинга настрой отправителя и письмо (если ещё не настроено).\n'
        'Затем нажми "Отправить рассылку".',
        reply_markup=markup
    )

# ----------------- Обработчик кнопки "Парсить email" -----------------
@bot.message_handler(func=lambda message: message.text == 'Парсить email')
def ask_for_url(message):
    bot.send_message(
        message.chat.id,
        'Отправьте URL сайта (например, https://example.ru)'
    )
    bot.register_next_step_handler(message, process_url)

# ----------------- Обработка полученного URL -----------------
def process_url(message):
    global last_emails
    url = message.text.strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        bot.reply_to(message, 'Пожалуйста, отправьте корректный URL, начинающийся с http:// или https://')
        bot.register_next_step_handler(message, process_url)
        return

    emails = extract_emails(url)
    if emails is None:
        bot.reply_to(message, '❌ Не удалось загрузить сайт. Проверьте URL или доступность сайта.')
    elif not emails:
        bot.reply_to(message, '🔍 На этом сайте не найдено email-адресов.')
    else:
        last_emails = emails
        result = f'✅ Найдено {len(emails)} email(ов):\n\n' + '\n'.join(emails)
        bot.reply_to(message, result)

# ----------------- Кнопка "Изменить настройки" -----------------
@bot.message_handler(func=lambda message: message.text == 'Изменить настройки')
def change_settings(message):
    global sender_email, sender_password, email_subject, email_body, settings_ready
    # Сбросим настройки, чтобы запросить заново
    sender_email = None
    sender_password = None
    email_subject = None
    email_body = None
    settings_ready = False
    bot.send_message(
        message.chat.id,
        'Настройки сброшены. Пожалуйста, введите их снова.\n'
        'Отправьте ваш email-адрес отправителя (например, mymail@gmail.com):'
    )
    bot.register_next_step_handler(message, get_sender_email)

# ----------------- Пошаговый сбор настроек -----------------
def get_sender_email(message):
    global sender_email
    sender_email = message.text.strip()
    if '@' not in sender_email:
        bot.reply_to(message, 'Некорректный email. Попробуйте снова:')
        bot.register_next_step_handler(message, get_sender_email)
        return
    bot.send_message(
        message.chat.id,
        'Отправьте пароль приложения (для Gmail) или пароль от почты:'
    )
    bot.register_next_step_handler(message, get_sender_password)

def get_sender_password(message):
    global sender_password
    sender_password = message.text.strip()  # В реальном проекте не выводите пароль в лог!
    bot.send_message(
        message.chat.id,
        'Введите тему письма:'
    )
    bot.register_next_step_handler(message, get_email_subject)

def get_email_subject(message):
    global email_subject
    email_subject = message.text.strip()
    bot.send_message(
        message.chat.id,
        'Введите текст письма (можно использовать переносы строк):'
    )
    bot.register_next_step_handler(message, get_email_body)

def get_email_body(message):
    global email_body, settings_ready
    email_body = message.text.strip()
    settings_ready = True
    bot.send_message(
        message.chat.id,
        '✅ Настройки сохранены!\n'
        f'Отправитель: {sender_email}\n'
        f'Тема: {email_subject}\n'
        f'Текст: {email_body[:50]}...'
    )

# ----------------- Кнопка "Отправить рассылку" -----------------
@bot.message_handler(func=lambda message: message.text == 'Отправить рассылку')
def send_newsletter(message):
    global last_emails, settings_ready, sender_email, sender_password, email_subject, email_body

    # Проверяем, есть ли email для рассылки
    if not last_emails:
        bot.reply_to(message, 'Сначала спарсите email с сайта (кнопка "Парсить email").')
        return

    # Проверяем, настроены ли отправитель и письмо
    if not settings_ready:
        bot.send_message(
            message.chat.id,
            'Настройки не введены. Сейчас мы их запросим.\n'
            'Отправьте ваш email-адрес отправителя (например, mymail@gmail.com):'
        )
        bot.register_next_step_handler(message, get_sender_email)
        return

    # Отправляем письма
    bot.send_message(message.chat.id, f'⏳ Начинаю рассылку на {len(last_emails)} адресов...')

    success_count = 0
    fail_count = 0
    for recipient in last_emails:
        try:
            send_email(sender_email, sender_password, recipient, email_subject, email_body)
            success_count += 1
        except Exception as e:
            print(f'Ошибка отправки на {recipient}: {e}')
            fail_count += 1

    bot.send_message(
        message.chat.id,
        f'📬 Рассылка завершена.\n'
        f'✅ Успешно: {success_count}\n'
        f'❌ Ошибок: {fail_count}'
    )

# ----------------- Функция отправки одного письма (через SMTP) -----------------
def send_email(sender, password, recipient, subject, body):
    # Для Gmail используем smtp.gmail.com:587
    # Для Яндекс – smtp.yandex.ru:587, для Mail.ru – smtp.mail.ru:587
    # Здесь пример для Gmail, можно изменить сервер в зависимости от почты
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, recipient, msg.as_string())
    server.quit()

# ----------------- Запуск бота -----------------
while True:
    try:
        print('Бот запускается...')
        bot.get_me()
        print('Бот готов к работе...')
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f'Бот упал: {e}. Перезапуск через 5 секунд')
        time.sleep(5)