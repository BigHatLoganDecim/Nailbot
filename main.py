import os
import requests
from flask import Flask, request
import telebot
from telebot import types
import json

import datetime

import re

import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Настройки ---
TOKEN = os.getenv("TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- Кнопочное меню ---
menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_markup.add("Цены", "Расписание")
menu_markup.add("Записаться", "Контакты")

# --- Расширенный словарь ---
INTENT_KEYWORDS = {
    "greeting": [
        "привет", "здравствуйте", "добрый день", "добрый вечер", "хай", "йоу", "здорово"
    ],
    "price": [
        "цена", "стоимость", "прайс", "сколько стоит", "почём", "расценки"
    ],
    "book": [
        "записаться", "запиши меня", "можно записаться", "хочу на маникюр", "запиши", "мне нужна запись"
    ],
    "time": [
        "свободное время", "расписание", "когда есть время", "свободно", "когда можно", "свободные окна"
    ],
    "contacts": [
        "контакты", "где ты", "как тебя найти", "как записаться", "номер", "телефон"
    ],
    "thanks": [
        "спасибо", "благодарю", "очень признателен", "спс", "пасиб"
    ],
    "cancel": [
        "отмена", "удали запись", "отменить", "я передумал", "отменяй"
    ],
    "offtopic": [
        "кто президент", "что ты умеешь", "как дела", "расскажи анекдот", "ты человек?"
    ]
}

# --- Ответы на неуместные фразы ---
OFFTOPIC_RESPONSES = [
    "Я бот для записи на маникюр, давай поговорим об этом.",
    "Если хочешь маникюр или педикюр — с радостью помогу!",
    "Я создан, чтобы помогать тебе записаться на услуги.",
    "Обратись ко мне, если хочешь узнать цены или записаться.",
    "Хочу быть полезным — задай вопрос по делу.",
    "Расскажу про услуги, расписание и цены — спрашивай!",
    "Я не болтаю, я помогаю! Запись, цены, контакты — всё скажу.",
    "С удовольствием помогу тебе записаться. Спроси!",
    "Ты можешь узнать у меня расписание и стоимость услуг.",
    "Лучше расскажу тебе про маникюр, чем про политику.",
    "Поговорим о маникюре?",
    "У меня для тебя хорошие новости — есть свободные окна!",
    "Хочешь красивый маникюр? Тогда ты по адресу.",
    "Давай лучше про ногти. Я в этом шарю!",
    "Я не умею анекдоты, но умею записывать на ноготочки.",
    "Спроси меня про расписание или цену — не стесняйся.",
    "Если хочешь записаться — я тут!",
    "Говорим только по делу. Маникюр — это моё всё!",
    "Могу предложить услуги и записать тебя — интересно?",
    "Я — ногтевой ассистент, давай к сути."
]

# --- Проверка намерения ---
def get_intent(text):
    text = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for phrase in keywords:
            if phrase in text:
                return intent
    return None

# --- Парсинг для записи ---
def parse_booking(text):
    text = text.lower()
    name_match = re.search(r"\bменя зовут (\w+)", text)
    name = name_match.group(1).capitalize() if name_match else "Без имени"

    if "маникюр" in text:
        service = "Маникюр"
    elif "педикюр" in text:
        service = "Педикюр"
    else:
        service = "Услуга не указана"

    date_match = re.search(r"\bзавтра\b|\bпятниц[аы]\b|\d{1,2}[:.]\d{2}", text)
    date = date_match.group(0) if date_match else "Дата не указана"

    comment = text

    return name, service, date, comment

# --- Ответ пользователю ---
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.send_message(message.chat.id,
        "Привет! Я бот для записи на маникюр и педикюр. Можешь выбрать одну из кнопок или написать свой вопрос!",
        reply_markup=menu_markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    intent = get_intent(message.text)
    if intent == "greeting":
        bot.send_message(message.chat.id, "Привет! Чем могу помочь?", reply_markup=menu_markup)
    elif intent == "price":
        bot.send_message(message.chat.id, "Маникюр — 1500₽, педикюр — 2000₽. Хочешь записаться?", reply_markup=menu_markup)
    elif intent == "time":
        bot.send_message(message.chat.id, "Свободно: завтра в 13:00, пятница в 16:30.", reply_markup=menu_markup)
    elif intent == "book":
        bot.send_message(message.chat.id, "Напиши имя, услугу и дату — я всё запишу!", reply_markup=menu_markup)
    elif intent == "contacts":
        bot.send_message(message.chat.id, "Я нахожусь по адресу: ул. Красоты, 123. Телефон: +7 999 000-00-00", reply_markup=menu_markup)
    elif intent == "thanks":
        bot.send_message(message.chat.id, "Обращайся, всегда рада помочь!", reply_markup=menu_markup)
    elif intent == "cancel":
        bot.send_message(message.chat.id, "Хорошо, запись отменена.", reply_markup=menu_markup)
    elif intent == "offtopic":
        bot.send_message(message.chat.id, random.choice(OFFTOPIC_RESPONSES), reply_markup=menu_markup)
    else:
        name, service, date, comment = parse_booking(message.text)
        post_data = {
            "name": name,
            "service": service,
            "date": date,
            "comment": comment
        }
        try:
            response = requests.post(GOOGLE_SCRIPT_URL, json=post_data)
            if response.status_code == 200:
                bot.send_message(message.chat.id, f"Готово! Записала: {name}, {service}, {date}", reply_markup=menu_markup)
            else:
                bot.send_message(message.chat.id, "Не удалось записать, попробуй позже.", reply_markup=menu_markup)
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при записи: {e}", reply_markup=menu_markup)

# --- Webhook ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{TOKEN}"
    success = bot.set_webhook(url=webhook_url)
    return "Webhook установлен" if success else "Ошибка установки вебхука", 200

@app.route("/")
def index():
    return "Бот работает!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)