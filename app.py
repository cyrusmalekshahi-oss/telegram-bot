import os
import json
import random
import string
from flask import Flask, request
import requests

app = Flask(name)

BOT_TOKEN = os.environ.get("8786185679:AAEd7Jq5L7rV0Et9quxn-mwSrJikswn8md0")
GROUP_ID = int(os.environ.get("-1003751936222"))
ADMIN_ID = int(os.environ.get("7861717112"))

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"blocked": [], "bot_active": True}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{API_URL}/sendMessage", json=payload)

def generate_code():
    return "#" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data_store = load_data()
    update = request.json

    if "message" not in update:
        return "ok"

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text", "")
    name = msg["from"].get("first_name", "")
    username = msg["from"].get("username", "ندارد")

    # مدیریت داخل گروه
    if chat_id == GROUP_ID and user_id == ADMIN_ID:

        if text == "خاموش":
            data_store["bot_active"] = False
            save_data(data_store)
            send_message(GROUP_ID, "⛔ بات خاموش شد.")
            return "ok"

        if text == "روشن":
            data_store["bot_active"] = True
            save_data(data_store)
            send_message(GROUP_ID, "✅ بات روشن شد.")
            return "ok"

        if "reply_to_message" in msg:
            replied = msg["reply_to_message"]["text"]

            if "🆔:" in replied:
                target_id = int(replied.split("🆔:")[1].split("\n")[0])

                if text == "بلاک":
                    if target_id not in data_store["blocked"]:
                        data_store["blocked"].append(target_id)
                        save_data(data_store)
                    send_message(GROUP_ID, "⛔ کاربر بلاک شد.")
                    return "ok"

                if text == "آنبلاک":
                    if target_id in data_store["blocked"]:
                        data_store["blocked"].remove(target_id)
                        save_data(data_store)
                    send_message(GROUP_ID, "✅ کاربر آنبلاک شد.")
                    return "ok"

                send_message(target_id, f"📩 پاسخ مدیریت:\n\n{text}")
                return "ok"

    # اگر بات خاموش است
    if not data_store["bot_active"]:
        send_message(chat_id, "⚠️ درحال حاضر امکان ارسال پیام وجود ندارد.\nلطفا مجددا امتحان کنید.")
        return "ok"

    # اگر بلاک است
    if user_id in data_store["blocked"]:
        send_message(chat_id, "⛔ شما مسدود شده‌اید.")
        return "ok"

    # استارت
    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": "📩 ارتباط با ادمین", "callback_data": "contact"}]
            ]
        }
        send_message(chat_id,
                     "👋 به سیستم ارتباط با مدیریت خوش آمدید.\nروی دکمه زیر بزنید.",
                     keyboard)
        return "ok"

    # ارسال پیام کاربر
    if chat_id != GROUP_ID:
        code = generate_code()

        admin_text = (
            f"📩 پیام جدید\n\n"
            f"👤 {name}\n"
            f"🔗 @{username}\n"
            f"🆔:{user_id}\n"
            f"📌 کد پیگیری: {code}\n\n"
            f"{text}"
        )

        send_message(GROUP_ID, admin_text)
        send_message(chat_id, f"✅ پیام شما ارسال شد.\nکد پیگیری: {code}")
        return "ok"

    return "ok"

@app.route("/")
def home():
    return "Bot is running"

if name == "main":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
