import os
from flask import Flask, request
import requests
import telebot
from telebot import types

# Получаем токены из переменных окружения
TELEGRAM_TOKEN = os.getenv("TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Список моделей Hugging Face для резервирования
HF_MODELS = [
    "google/flan-t5-base",
    "tiiuae/falcon-rw-1b"
]

# Функция для общения с Hugging Face
def hf_chat(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}

    for model in HF_MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                generated_text = response.json()[0].get("generated_text")
                if generated_text:
                    return generated_text.strip()
            else:
                print(f"Модель {model} вернула статус {response.status_code}")
        except Exception as e:
            print(f"Ошибка при обращении к модели {model}: {e}")
    return "Извините, сейчас не могу ответить. Попробуйте позже."

# Обработка входящих обновлений от Telegram
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Главная страница
@app.route("/")
def index():
    return "Бот запущен!"

# Установка вебхука
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"https://nailbot-service.onrender.com/{TELEGRAM_TOKEN}"
    success = bot.set_webhook(url=webhook_url)
    return "Webhook установлен" if success else "Ошибка установки вебхука", 200

# Обработка команд /start и /help
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для записи на маникюр и общения. Можешь спросить что угодно!")

# Обработка всех остальных сообщений
@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    response = hf_chat(message.text)
    bot.send_message(message.chat.id, response)

# Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)