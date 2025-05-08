
from flask import Flask, request
from telebot import TeleBot, types
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = TeleBot(TOKEN)
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

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для записи на маникюр и педикюр.")

@bot.message_handler(func=lambda msg: True)
def fallback(message):
    bot.send_message(message.chat.id, "Напиши: /start, 'цены', 'расписание' или 'записаться'.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
