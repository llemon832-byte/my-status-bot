import telebot
from telebot import types
import datetime
import threading
import time
import os
import html
from flask import Flask
from zoneinfo import ZoneInfo

# Нові дані, які ви надали
TOKEN = '8685131460:AAGfTPfn5V92_k7E--vg0NRt65MUV8PFjDw'
GROUP_ID = -1004313121326 

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

def get_kyiv_time():
    return datetime.datetime.now(ZoneInfo("Europe/Kyiv"))

app = Flask('')

@app.route('/')
def home():
    return "Бот працює!"

def run_web_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# Автоочищення о 08:00 за Києвом
def auto_clear():
    while True:
        now = get_kyiv_time()
        if now.hour == 8 and now.minute == 0:
            stats_data.clear()
            try:
                bot.send_message(GROUP_ID, "🔄 Статистику автоматично очищено. До роботи!")
            except:
                pass
            time.sleep(60)
        time.sleep(30)

def format_time(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0: parts.append(f"{hours} год")
    if minutes > 0: parts.append(f"{minutes} хв")
    if seconds > 0 or not parts: parts.append(f"{seconds} сек")
    return " ".join(parts)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(status) for status in STATUS_OPTIONS]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Сап салага, ну, вибирай:", reply_markup=markup)

@bot.message_handler(commands=['clear'])
def clear_stats(message):
    stats_data.clear()
    bot.send_message(message.chat.id, "🧹 Почистив історію в хром)")

# Команда /stats на безпечному HTML
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if not stats_data:
        bot.send_message(message.chat.id, "📊 Бездельніки,ніц ще не зробили")
        return
    
    now = get_kyiv_time()
    text = "📊 <b>Загальна статистика команди:</b>\n"
    text += f"📅 Дата: {now.strftime('%d.%m.%Y')}\n"
    text += "────────────────────\n\n"
    
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
        
        # Безпечно екрануємо ім'я для HTML
        safe_name = html.escape(data['name'])
        
        text += f"👤 <b>{safe_name}</b>\n"
        text += f"➡️ Прихід: {arr_time} | ⬅️ Ухід: {dep_time}\n"
        text += f"☕ Чілив: {break_duration}\n"
        text += f"💼 <b>Работал:</b> {work_duration}\n"
        text += f"📌 Статус: {data['last_status']}\n"
        text += "────────────────────\n"
        
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text in STATUS_OPTIONS)
def handle_status(message):
    user_id = message.from_user.id
    name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    status = message.text
    now = get_kyiv_time()
    
    if user_id not in stats_data:
        stats_data[user_id] = {'name': name, 'arrival': None, 'departure': None, 'total_break': datetime.timedelta(), 'last_status': None, 'last_time': now}
        
    user = stats_data[user_id]
    
    if user['last_status'] in ['☕ Перерва 5 хв', '☕ Перерва 10 хв', '☕ Перерва 15 хв', '☕ Перерва 30 хв', '🍲 Обід']:
        user['total_break'] += (now - user['last_time'])
        
    if status == '💼 На роботі' and user['arrival'] is None: 
        user['arrival'] = now
    elif status == '🏠 Додому': 
        user['departure'] = now
        
    user['last_status'] = status
    user['last_time'] = now
    
    # 1. Спочатку відповідаємо користувачу в приват
    try:
        bot.send_message(message.chat.id, f"Статус «{status}» прийнято!")
    except:
        pass

    # 2. Потім надсилаємо повідомлення в групу
    try:
        safe_name = html.escape(name)
        group_message = f"🔔 <b>Муд:</b> {safe_name} — {status}"
        bot.send_message(GROUP_ID, group_message, parse_mode="HTML")
    except Exception as e:
        print(f"Помилка відправки в групу: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=auto_clear, daemon=True).start()
    print("Бот запущено з новим токеном...")
    bot.infinity_polling()
