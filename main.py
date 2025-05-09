import os
from flask import Flask, request
import requests
import telebot
from telebot import types

# Получаем токен Telegram и Hugging Face
TOKEN = os.getenv("TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Hugging Face функция общения
def hf_chat(prompt):
    url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()[0]["generated_text"]
        else:
            return "Ответ от модели не получен. Попробуй позже."
    except Exception as e:
        return f"Ошибка общения с Hugging Face: {e}"

# Основной webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Тестовая страница
@app.route("/")
def index():
    return "Бот работает!"

# Установка вебхука
@app.route("/set_webhook")
def set_webhook():
    webhook_url = f"https://nailbot-service.onrender.com/{TOKEN}"
    success = bot.set_webhook(url=webhook_url)
    return "Webhook установлен" if success else "Ошибка установки вебхука", 200

# Обработка команд
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для записи на маникюр и общения. Можешь спросить что угодно!")

# Общение через Hugging Face
@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    response = hf_chat(message.text)
    bot.send_message(message.chat.id, response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)