import telebot
from telebot import types
import datetime
import threading
import time
import os
from flask import Flask

# Сюди вставте токен, який дав @BotFather
TOKEN = '8685131460:AAETnfmADzzhRAjD9mTosqtzYJb_x_cRAf8' 

# Сюди вставте ID вашої групи (з мінусом)
GROUP_ID = -1004481002817 

bot = telebot.TeleBot(TOKEN)
stats_data = {}

STATUS_OPTIONS = [
    '💼 На роботі', 
    '☕ Перерва 5 хв', 
    '☕ Перерва 10 хв', 
    '☕ Перерва 15 хв', 
    '☕ Перерва 30 хв', 
    '🍲 Обід', 
    '🏠 Додому'
]

# Створюємо мікро-сайт для обходу обмежень безкоштовного хостингу
app = Flask('')

@app.route('/')
def home():
    return "Бот працює!"

def run_web_server():
    # Порт підлаштовується під хмару Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# Автоочищення о 08:00
def auto_clear():
    while True:
        now = datetime.datetime.now()
        if now.hour == 8 and now.minute == 0:
            stats_data.clear()
            try:
                bot.send_message(GROUP_ID, "🔄 Статистику автоматично очищено. Почався новий робочий день!")
            except:
                pass
            time.sleep(60)
        time.sleep(30)

# Функція для гарного відображення часу
def format_time(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0: parts.append(f"{hours} god")
    if minutes > 0: parts.append(f"{minutes} хв")
    if seconds > 0 or not parts: parts.append(f"{seconds} сек")
    return " ".join(parts)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(status) for status in STATUS_OPTIONS]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Привіт! Обери свій статус:", reply_markup=markup)

@bot.message_handler(commands=['clear'])
def clear_stats(message):
    stats_data.clear()
    bot.send_message(message.chat.id, "🧹 Загальну статистику команди очищено вручну!")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if not stats_data:
        bot.send_message(message.chat.id, "📊 Статистика поки порожня.")
        return
    text = "📊 **Загальна статистика команди:**\n"
    text += f"📅 Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}\n"
    text += "────────────────────\n\n"
    now = datetime.datetime.now()
    for user_id, data in stats_data.items():
        arr_time = data['arrival'].strftime('%H:%M') if data['arrival'] else "Не відмітився"
        dep_time = data['departure'].strftime('%H:%M') if data['departure'] else "На зміні"
        total_break = data['total_break']
        if data['last_status'] in ['☕ Перерва 5 хв', '☕ Перерва 10 хв', '☕ Перерва 15 хв', '☕ Перерва 30 хв', '🍲 Обід']:
            total_break += (now - data['last_time'])
        if data['arrival']:
            end_point = data['departure'] if data['departure'] else now
            total_elapsed = end_point - data['arrival']
            pure_work = total_elapsed - total_break
            if pure_work.total_seconds() < 0: pure_work = datetime.timedelta()
            work_duration = format_time(pure_work)
        else:
            work_duration = "0 хв"
        break_duration = format_time(total_break)
        text += f"👤 **{data['name']}**\n"
        text += f"➡️ Прихід: {arr_time} | ⬅️ Ухід: {dep_time}\n"
        text += f"☕ На перервах: {break_duration}\n"
        text += f"💼 **Чиста робота:** {work_duration}\n"
        text += f"📌 Статус: {data['last_status']}\n"
        text += "────────────────────\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text in STATUS_OPTIONS)
def handle_status(message):
    user_id = message.from_user.id
    name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    status = message.text
    now = datetime.datetime.now()
    if user_id not in stats_data:
        stats_data[user_id] = {'name': name, 'arrival': None, 'departure': None, 'total_break': datetime.timedelta(), 'last_status': None, 'last_time': now}
    user = stats_data[user_id]
    if user['last_status'] in ['☕ Перерва 5 хв', '☕ Перерва 10 хв', '☕ Перерва 15 хв', '☕ Перерва 30 хв', '🍲 Обід']:
        user['total_break'] += (now - user['last_time'])
    if status == '💼 На роботі' and user['arrival'] is None: user['arrival'] = now
    elif status == '🏠 Додому': user['departure'] = now
    user['last_status'] = status
    user['last_time'] = now
    try:
        bot.send_message(GROUP_ID, f"🔔 **Статус:** {name} — {status}", parse_mode="Markdown")
        bot.send_message(message.chat.id, f"Статус «{status}» надіслано в чат!")
    except:
        pass

if __name__ == '__main__':
    # Запуск сайту-заглушки у фоні
    threading.Thread(target=run_web_server, daemon=True).start()
    # Запуск таймера очищення
    threading.Thread(target=auto_clear, daemon=True).start()
    print("Бот готовий до безкоштовного хостингу...")
    bot.infinity_polling()
