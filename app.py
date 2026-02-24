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

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

DATA_FILE = "data.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=data)

def generate_tracking_code():
    return "#" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.json
    data = load_data()

    # پیام معمولی
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        full_name = message["from"].get("first_name", "")
        username = message["from"].get("username", "ندارد")
        text = message.get("text", "")

        # فقط ادمین داخل گروه
        if chat_id == GROUP_ID and user_id == ADMIN_ID:

            # بلاک
            if text.startswith("/block"):
                target = int(text.split()[1])
                if target not in data["blocked"]:
                    data["blocked"].append(target)
                    save_data(data)
                send_message(GROUP_ID, "⛔ کاربر بلاک شد.")
                return "ok"

            # آنبلاک
            if text.startswith("/unblock"):
                target = int(text.split()[1])
                if target in data["blocked"]:
                    data["blocked"].remove(target)
                    save_data(data)
                send_message(GROUP_ID, "✅ کاربر آنبلاک شد.")
                return "ok"

            # ریپلای برای پاسخ
            if "reply_to_message" in message:
                replied = message["reply_to_message"]["text"]
                if "🆔 آیدی:" in replied:
                    user_id_line = replied.split("🆔 آیدی:")[1]
                    target_id = int(user_id_line.split("\n")[0].strip())
                    send_message(target_id, f"📩 پاسخ ادمین:\n\n{text}")
                    return "ok"

        # اگر کاربر بلاک باشد
        if user_id in data["blocked"]:
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
                         "👋 <b>به ربات ارتباط با ادمین خوش آمدید</b>\n\nروی دکمه زیر بزنید.",
                         )
            requests.post(f"{TELEGRAM_API}/sendMessage", json={
                "chat_id": chat_id,
                "text": "👇 انتخاب کنید:",
                "reply_markup": keyboard
            })
            return "ok"

        # ارسال پیام کاربر
        if chat_id != GROUP_ID and user_id != ADMIN_ID:
            tracking = generate_tracking_code()
            data["tickets"][tracking] = user_id
            save_data(data)

            admin_text = (
                f"📩 پیام جدید\n\n"
                f"👤 نام: {full_name}\n"
                f"🔗 یوزرنیم: @{username}\n"
                f"🆔 آیدی: {user_id}\n"
                f"📌 کد پیگیری: {tracking}\n\n"
                f"💬 متن:\n{text}"
            )
            send_message(GROUP_ID, admin_text)
            send_message(chat_id, f"✅ پیام شما ارسال شد.\nکد پیگیری شما: {tracking}")
            return "ok"

    return "ok"

@app.route("/")
def home():
    return "Bot is running!"
