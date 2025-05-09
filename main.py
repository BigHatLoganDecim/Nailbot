import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# Переменные окружения
TOKEN = os.getenv("TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

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

# Функция для запроса к Hugging Face с фолбэком
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
            elif response.status_code == 503:
                print(f"Модель {model} не активна. Пробую следующую...")
                continue
            else:
                print(f"Ответ {response.status_code} от модели {model}: {response.text}")
        except Exception as e:
            print(f"Ошибка при обращении к модели {model}: {e}")
    return "Извините, сейчас не могу ответить. Попробуйте позже."

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
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    success = bot.set_webhook(url=webhook_url)
    return "Webhook установлен" if success else "Ошибка установки вебхука", 200

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для записи на маникюр и общения. Можешь спросить что угодно!")

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_text = message.text.strip().lower()
    if "цены" in user_text:
        bot.send_message(message.chat.id, "Маникюр — 1500 руб, педикюр — 2000 руб. Записаться?")
    elif "расписание" in user_text:
        bot.send_message(message.chat.id, "Свободные окна: завтра 13:00, пятница 16:30.")
    elif "записаться" in user_text:
        bot.send_message(message.chat.id, "Напиши дату и время, я запишу тебя!")
    else:
        reply = ask_model(message.text)
        bot.send_message(message.chat.id, reply)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)