import os
import requests
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Список fallback моделей Hugging Face
HF_MODELS = [
    "tiiuae/falcon-rw-1b",
    "google/flan-t5-base",
    "google/flan-t5-small",
    "google/flan-t5-xl",
    "google/flan-t5-large",
    "mistralai/Mistral-7B-Instruct-v0.1"
]

# Функция обращения к Hugging Face
def ask_model(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    for model in HF_MODELS:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}"
            response = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and "generated_text" in result[0]:
                    return result[0]["generated_text"]
                elif isinstance(result, dict):
                    return result.get("generated_text") or result.get("summary_text")
            elif response.status_code == 503:
                continue  # модель пока неактивна
        except Exception as e:
            print(f"[Ошибка модели {model}] {e}")
    return "Извините, сейчас не могу ответить. Попробуйте позже."

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    update = types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Бот запущен!"

# Устанавливаем вебхук при запуске
@app.before_first_request
def setup_webhook():
    if RENDER_HOSTNAME:
        webhook_url = f"https://{RENDER_HOSTNAME}/{TOKEN}"
        success = bot.set_webhook(url=webhook_url)
        print("Webhook установлен" if success else "Ошибка установки вебхука")

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для записи на маникюр и общения. Можешь спросить что угодно!")

@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    text = message.text.lower()
    if "цены" in text:
        bot.send_message(message.chat.id, "Маникюр — 1500 руб, педикюр — 2000 руб.")
    elif "расписание" in text:
        bot.send_message(message.chat.id, "Свободно завтра в 13:00 и в пятницу в 16:30.")
    elif "записаться" in text:
        bot.send_message(message.chat.id, "Напиши дату и время, я тебя запишу.")
    else:
        reply = ask_model(message.text)
        bot.send_message(message.chat.id, reply)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)