import os
import requests
import telebot
from flask import Flask, request
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройки токенов
TOKEN = os.getenv("TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Google Таблицы
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
gs = gspread.authorize(credentials)
sheet = gs.open("nailbot-записи").sheet1

# Список fallback моделей Hugging Face
HF_MODELS = [
    "tiiuae/falcon-rw-1b",
    "google/flan-t5-base",
    "google/flan-t5-small",
    "google/flan-t5-xl",
    "google/flan-t5-large",
    "mistralai/Mistral-7B-Instruct-v0.1"
]

# Функция общения с Hugging Face
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
                result = response.json()
                if isinstance(result, list) and "generated_text" in result[0]:
                    return result[0]["generated_text"]
                elif isinstance(result, dict):
                    return result.get("generated_text") or result.get("summary_text")
        except Exception as e:
            print(f"Ошибка при обращении к модели {model}: {e}")
    return "Извините, сейчас не могу ответить. Попробуйте позже."

# Flask маршруты
@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Бот запущен!"

@app.route("/set_webhook")
def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    if bot.set_webhook(url):
        return "Webhook установлен"
    return "Ошибка установки вебхука"

# Команды меню
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Цены", "Расписание", "Записаться")
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для записи на маникюр и общения. Выбери команду ниже или напиши свой вопрос!",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text.lower() == "цены")
def handle_prices(message):
    bot.send_message(message.chat.id, "Маникюр — 1500 руб, педикюр — 2000 руб. Хочешь записаться?")

@bot.message_handler(func=lambda m: m.text.lower() == "расписание")
def handle_schedule(message):
    bot.send_message(message.chat.id, "Свободные окна: завтра 13:00, пятница 16:30.")

@bot.message_handler(func=lambda m: m.text.lower() == "записаться")
def handle_booking(message):
    msg = bot.send_message(message.chat.id, "Напиши дату и время, например: 12 мая, 14:00")
    bot.register_next_step_handler(msg, save_booking)

def save_booking(message):
    user = message.from_user.first_name or "Unknown"
    text = message.text
    sheet.append_row([user, text])
    bot.send_message(message.chat.id, "Готово! Ты в списке.")

# Общий обработчик
@bot.message_handler(func=lambda msg: True)
def handle_anything(message):
    reply = ask_model(message.text)
    bot.send_message(message.chat.id, reply)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)