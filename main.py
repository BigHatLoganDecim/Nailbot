
import os
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")  # Убедись, что переменная TOKEN добавлена в Render
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Бот запущен!"

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = f"https://nailbot-service.onrender.com/{TOKEN}"
    success = bot.set_webhook(url=webhook_url)
    return "Webhook установлен" if success else "Ошибка установки вебхука", 200

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для записи на маникюр и педикюр.")

@bot.message_handler(func=lambda msg: True)
def fallback(message):
    bot.send_message(message.chat.id, "Напиши: /start, 'цены', 'расписание' или 'записаться'.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
import requests

WEBHOOK_URL = "https://nailbot-service.onrender.com/" + TOKEN
requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
@app.route("/set_webhook")
def set_webhook():
    s = bot.set_webhook(url="https://nailbot-service.onrender.com/" + TOKEN)
    return "Webhook set" if s else "Webhook failed"