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

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def generate_tracking_code():
    return "#" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.json
    data = load_data()

    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        full_name = message["from"].get("first_name", "")
        username = message["from"].get("username", "ندارد")
        text = message.get("text", "")

        # فقط ادمین داخل گروه
        if chat_id == GROUP_ID and user_id == ADMIN_ID:

            # روشن کردن بات
            if text.strip() == "روشن":
                data["bot_active"] = True
                save_data(data)
                send_message(GROUP_ID, "✅ بات فعال شد.")
                return "ok"

            # خاموش کردن بات
            if text.strip() == "خاموش":
                data["bot_active"] = False
                save_data(data)
                send_message(GROUP_ID, "⛔ بات غیرفعال شد.")
                return "ok"

            # اگر ریپلای باشد
            if "reply_to_message" in message:
                replied_text = message["reply_to_message"]["text"]

                if "🆔 آیدی:" in replied_text:
                    target_id = int(replied_text.split("🆔 آیدی:")[1].split("\n")[0].strip())

                    if text.strip() == "بلاک":
                        if target_id not in data["blocked"]:
                            data["blocked"].append(target_id)
                            save_data(data)
                        send_message(GROUP_ID, "⛔ کاربر بلاک شد.")
                        return "ok"

                    if text.strip() == "آنبلاک":
                        if target_id in data["blocked"]:
                            data["blocked"].remove(target_id)
                            save_data(data)
                        send_message(GROUP_ID, "✅ کاربر آنبلاک شد.")
                        return "ok"

                    # پاسخ عادی
                    send_message(target_id, f"📩 پاسخ ادمین:\n\n{text}")
                    return "ok"

        # اگر کاربر بلاک باشد
        if user_id in data["blocked"]:
            send_message(chat_id, "⛔ شما مسدود شده‌اید.")
            return "ok"

        # اگر بات خاموش باشد
        if not data.get("bot_active", True):
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📩 ارتباط با ادمین", "callback_data": "contact"}]
                ]
            }
            send_message(chat_id,
                         "⚠️ درحال حاضر امکان ارسال پیام وجود ندارد.\nلطفا مجددا امتحان کنید.",
                         keyboard)
            return "ok"

        # استارت
        if text == "/start":
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📩 ارتباط با ادمین", "callback_data": "contact"}]
                ]
            }
            send_message(chat_id,
                         "👋 <b>به سیستم ارتباط با مدیریت خوش آمدید</b>\n\n"
                         "برای ارسال پیام روی دکمه زیر کلیک کنید.",
                         keyboard)
            return "ok"

        # ارسال پیام کاربر
        if chat_id != GROUP_ID:
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
            send_message(chat_id,
                         f"✅ پیام شما با موفقیت ارسال شد.\n"
                         f"📌 کد پیگیری شما: {tracking}")
            return "ok"

    if "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]

        if not load_data().get("bot_active", True):
            send_message(chat_id,
                         "⚠️ درحال حاضر امکان ارسال پیام وجود ندارد.\nلطفا مجددا امتحان کنید.")
            return "ok"

        send_message(chat_id, "✍️ پیام خود را ارسال کنید:")
        return "ok"

    return "ok"

@app.route("/")
def home():
    return "Bot is running!"
