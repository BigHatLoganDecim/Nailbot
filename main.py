import os
import re
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")
SHEETS_WEBHOOK = os.getenv("SHEETS_WEBHOOK")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Записаться", "Цены")
    markup.row("Расписание", "Контакты")
    return markup

def parse_booking_input(text):
    text = text.lower()
    name_match = re.search(r"(меня зовут|имя|я)\s+([а-яёa-z]{3,})", text)
    name = name_match.group(2).capitalize() if name_match else "Без имени"

    service = "Маникюр" if "маник" in text else "Педикюр" if "педик" in text else "Услуга не указана"
    now = datetime.now()
    date = None

    if "сегодня" in text:
        date = now
    elif "завтра" in text:
        date = now + timedelta(days=1)
    elif "послезавтра" in text:
        date = now + timedelta(days=2)
    else:
        date_match = re.search(r"(\d{1,2})[ .-]?(январ[ья]|феврал[ья]|март[ае]?|апрел[ья]|ма[йя]|июн[ья]|июл[ья]|август[ае]?|сентябр[ья]|октябр[ья]|ноябр[ья]|декабр[ья])", text)
        if date_match:
            day = int(date_match.group(1))
            month_str = date_match.group(2)
            months = {'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4, 'май': 5, 'мая': 5, 'июн': 6, 'июл': 7,
                      'август': 8, 'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12}
            for key in months:
                if month_str.startswith(key):
                    try:
                        date = now.replace(month=months[key], day=day)
                    except:
                        pass
        elif re.search(r"\d{1,2}[./-]\d{1,2}", text):
            try:
                date = datetime.strptime(re.search(r"\d{1,2}[./-]\d{1,2}", text).group(), "%d.%m")
                date = date.replace(year=now.year)
            except:
                pass

    time_match = re.search(r"(в\s*)?(\d{1,2})([:.](\d{2}))?", text)
    if time_match:
        hour = int(time_match.group(2))
        minute = int(time_match.group(4)) if time_match.group(4) else 0
        if date:
            date = date.replace(hour=hour, minute=minute, second=0)
        else:
            date = now.replace(hour=hour, minute=minute, second=0)

    date_str = date.strftime("%d.%m.%Y %H:%M") if date else "Дата не указана"

    return {
        "name": name,
        "service": service,
        "date": date_str
    }

def fake_gpt_response(text):
    text = text.lower()
    if any(w in text for w in ["привет", "здравствуй", "добрый", "ку", "йо", "хай"]):
        return random.choice([
            "Привет! Хочешь узнать расписание или записаться?",
            "Здравствуй! Чем могу помочь: запись, цены, расписание?",
            "Привет-привет! Я твой бот-мастер по ноготочкам. Пиши!"
        ])
    if any(w in text for w in ["цена", "стоимость", "прайс", "сколько стоит"]):
        return random.choice([
            "Маникюр — 1500₽, педикюр — 2000₽. Хочешь записаться?",
            "Прайс такой: маникюр 1500, педикюр 2000. Остались вопросы?",
            "Маникюр с покрытием — 1500₽, педикюр — 2000₽. Запишем тебя?"
        ])
    if any(w in text for w in ["где", "адрес", "как доехать"]):
        return random.choice([
            "Салон рядом с метро. Уточни район — и я подскажу!",
            "Я напишу точный адрес после записи, ок?",
            "Удобное местоположение, подскажу после записи."
        ])
    if any(w in text for w in ["расписание", "график", "когда свободно", "свободно"]):
        return random.choice([
            "Завтра свободно в 13:00 и 16:30. Подходит?",
            "Есть окна в среду и пятницу. Напиши удобное время!",
            "Когда тебе удобно? Я подскажу свободные окошки."
        ])
    if any(w in text for w in ["запиши", "записаться", "записать", "можно на", "я хочу"]):
        return random.choice([
            "Супер! Напиши имя, услугу и время — и я всё внесу.",
            "Конечно! Когда удобно и что делаем: маникюр или педикюр?",
            "Готова записать! Напиши дату, имя и что делать."
        ])
    if any(w in text for w in ["спасибо", "благодарю", "ок", "понятно"]):
        return random.choice([
            "Всегда рада помочь!",
            "Обращайся, я на связи.",
            "Спасибо тебе! Жду на процедуре."
        ])
    if any(w in text for w in ["пока", "до свидания", "бай", "увидимся"]):
        return random.choice([
            "До встречи! Удачного дня!",
            "Пока-пока! Записывайся, если что!",
            "Счастливо! Я всегда тут, если что."
        ])
    return random.choice([
        "Не совсем поняла, но если хочешь записаться — просто напиши имя, дату и процедуру!",
        "Хочешь уточнить цены или расписание? Я подскажу.",
        "Запись простая: имя, дата и что делать — и я всё оформлю!"
    ])

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Бот работает!", 200

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{TOKEN}"
    success = bot.set_webhook(url=url)
    return "Webhook установлен" if success else "Ошибка", 200

@bot.message_handler(commands=["start", "help"])
def greet(message):
    bot.send_message(message.chat.id,
                     "Привет! Напиши имя, процедуру и дату/время — я запишу тебя.",
                     reply_markup=main_menu())

@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    text = message.text.lower()

    if "цены" in text:
        bot.send_message(message.chat.id, "Маникюр — 1500₽, педикюр — 2000₽.", reply_markup=main_menu())
        return
    elif "расписание" in text:
        bot.send_message(message.chat.id, "Свободно: завтра в 13:00 и пятницу в 16:30.", reply_markup=main_menu())
        return
    elif "контакт" in text:
        bot.send_message(message.chat.id, "Телефон: +7 999 123-45-67\nInstagram: @yourpage", reply_markup=main_menu())
        return
    elif "записаться" in text:
        bot.send_message(message.chat.id, "Напиши имя, услугу и дату/время — например: 'Я Анна. Маникюр. Завтра в 15:00'",
                         reply_markup=main_menu())
        return

    parsed = parse_booking_input(message.text)
    payload = {
        "name": parsed["name"],
        "service": parsed["service"],
        "date": parsed["date"],
        "comment": message.text
    }

    try:
        r = requests.post(SHEETS_WEBHOOK, json=payload, timeout=10)
        if r.ok:
            bot.send_message(message.chat.id,
                             f"Записала: {parsed['service']} на {parsed['date']} для {parsed['name']}.",
                             reply_markup=main_menu())
            return
    except Exception as e:
        print("Ошибка отправки:", e)

    response = fake_gpt_response(message.text)
    bot.send_message(message.chat.id, response, reply_markup=main_menu())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)