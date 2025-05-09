import os
import json
import requests
from flask import Flask, request
import telebot
from telebot import types

# Переменные окружения
TOKEN = os.getenv("TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
SHEETS_WEBHOOK = os.getenv("SHEETS_WEBHOOK")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

HF_MODELS = [
    "tiiuae/falcon-rw-1b",
    "google/flan-t5-base",
    "google/flan-t5-small",
    "google/flan-t5-xl",
    "google/flan-t5-large",
    "mistralai/Mistral-7B-Instruct-v0.1"
]

def ask_model(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    for model in HF_MODELS:
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={"inputs": prompt},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and "generated_text" in data[0]:
                    return data[0]["generated_text"]
                elif isinstance(data, dict) and "generated_text" in data:
                    return data["generated_text"]
                elif isinstance(data, dict) and "summary_text" in data:
                    return data["summary_text"]
            elif response.status_code == 503:
                continue
        except Exception as e:
            print(f"Ошибка модели {model}: {e}")
    return "Извините, сейчас не могу ответить. Попробуйте позже."

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Бот работает!"

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    success = bot.set_webhook(url=url)
    return "Webhook установлен" if success else "Не удалось установить webhook", 200

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Цены", "Расписание")
    markup.add("Записаться")
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для записи на маникюр и общения. Можешь выбрать одну из кнопок или написать свой вопрос!",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    text = message.text.lower()

    if "цены" in text:
        bot.send_message(message.chat.id, "Маникюр — 1500₽, педикюр — 2000₽. Хочешь записаться?")
    elif "расписание" in text:
        bot.send_message(message.chat.id, "Свободно: завтра в 13:00, пятница в 16:30.")
    elif "записаться" in text:
        bot.send_message(message.chat.id, "Напиши имя, услугу и дату — я всё запишу!")
    elif any(x in text for x in ["запись", "хочу", "услуга", "дата"]):
        try:
            payload = {
                "name": message.from_user.first_name,
                "content": message.text
            }
            r = requests.post(SHEETS_WEBHOOK, json=payload)
            if r.status_code == 200:
                bot.send_message(message.chat.id, "Готово! Ты в списке.")
            else:
                bot.send_message(message.chat.id, "Не удалось записать, но я передам сообщение мастеру.")
        except Exception as e:
            print(f"Ошибка отправки в таблицу: {e}")
            bot.send_message(message.chat.id, "Произошла ошибка при записи.")
    else:
        reply = ask_model(message.text)
        bot.send_message(message.chat.id, reply)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)