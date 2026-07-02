import telebot
from telebot import types
import os
import html
from flask import Flask
import threading

# Твої актуальні дані
TOKEN = '8685131460:AAGfTPfn5V92_k7E--vg0NRt65MUV8PFjDw'
GROUP_ID = -1004313121326 

bot = telebot.TeleBot(TOKEN)

# Твої фірмові кнопки
STATUS_OPTIONS = [
    '💼 Я бізнесмен', 
    '☕ Чіл 5 хв', 
    '☕ Отойшов 10 хв', 
    '☕ Перекур 15 хв', 
    '☕ Хава ю?...Смачного 30 хв', 
    '🍲 Обід', 
    '🏠 Пісяти та спати'
]

app = Flask('')

@app.route('/')
def home():
    return "Бот працює!"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# Команда /start (Запуск та виклик кнопок)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(status) for status in STATUS_OPTIONS]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Сап салага, ну, вибирай або юзай команди з /help:", reply_markup=markup)

# Нова команда /help (Інструкція для всіх)
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📋 <b>Шпаргалка по командах бота:</b>\n\n"
        "🚀 /start — Увімкнути бота та викликати кнопки статусів\n"
        "ℹ️ /help — Показати цю довідку\n\n"
        "⏳ <code>/late [твій текст]</code> — Сповістити групу про запізнення.\n"
        "<i>Приклад: /late на 10 хв, пробки</i>\n\n"
        "📊 <code>/report [твій текст]</code> — Надіслати швидкий звіт у групу.\n"
        "<i>Приклад: /report Зробив завдання, клієнт задоволений</i>"
    )
    try:
        bot.send_message(message.chat.id, help_text, parse_mode="HTML")
    except:
        pass

# Нова команда /late (Сповіщення про запізнення)
@bot.message_handler(commands=['late'])
def handle_late(message):
    name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    safe_name = html.escape(name)
    
    # Отримуємо текст, який юзер написав після команди /late
    args = message.text.split(maxsplit=1)
    late_reason = args[1] if len(args) > 1 else "запізнюється (не вказав на скільки)"
    safe_reason = html.escape(late_reason)
    
    try:
        bot.send_message(message.chat.id, "⏰ Сповіщення про запізнення надіслано в групу!")
    except:
        pass

    try:
        group_message = f"⏳ <b>Запізнення:</b> {safe_name} — {safe_reason}"
        bot.send_message(GROUP_ID, group_message, parse_mode="HTML")
    except Exception as e:
        print(f"Помилка відправки в групу: {e}")

# Нова команда /report (Швидкий звіт у групу)
@bot.message_handler(commands=['report'])
def handle_report(message):
    name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    safe_name = html.escape(name)
    
    # Отримуємо текст після команди /report
    args = message.text.split(maxsplit=1)
    
    if len(args) > 1:
        report_text = html.escape(args[1])
        try:
            bot.send_message(message.chat.id, "✅ Твій звіт успішно закинуто в групу!")
        except:
            pass
        
        try:
            group_message = f"📋 <b>Швидкий звіт від:</b> {safe_name}\n────────────────────\n{report_text}"
            bot.send_message(GROUP_ID, group_message, parse_mode="HTML")
        except Exception as e:
            print(f"Помилка відправки в групу: {e}")
    else:
        try:
            bot.send_message(message.chat.id, "⚠️ Салага, ти забув написати текст звіту!\nПриклад: <code>/report Здав касу, все ок</code>", parse_mode="HTML")
        except:
            pass

# Обробка натискання на звичайні кнопки статусів
@bot.message_handler(func=lambda message: message.text in STATUS_OPTIONS)
def handle_status(message):
    name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    status = message.text
    
    try:
        bot.send_message(message.chat.id, f"Статус «{status}» прийнято!")
    except:
        pass

    try:
        safe_name = html.escape(name)
        group_message = f"🔔 <b>Муд:</b> {safe_name} — {status}"
        bot.send_message(GROUP_ID, group_message, parse_mode="HTML")
    except Exception as e:
        print(f"Помилка відправки в групу: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Ультра-заряджений бот сповіщень запущено...")
    bot.infinity_polling()
