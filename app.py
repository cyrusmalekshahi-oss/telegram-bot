import os
import sqlite3
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

app = Flask(__name__)

# ساخت دیتابیس
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS messages (group_msg_id INTEGER, user_id INTEGER)")
conn.commit()

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=data)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.json

    if "message" in update:
        message = update["message"]

        # اگر پیام از گروه بود و ریپلای داشت
        if str(message["chat"]["id"]) == GROUP_ID and "reply_to_message" in message:
            reply_msg_id = message["reply_to_message"]["message_id"]

            cursor.execute("SELECT user_id FROM messages WHERE group_msg_id=?", (reply_msg_id,))
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                send_message(user_id, message.get("text", ""))
            return "ok"

        # اگر پیام از کاربر خصوصی بود
        user_id = message["from"]["id"]
        first_name = message["from"].get("first_name", "")
        last_name = message["from"].get("last_name", "")
        username = message["from"].get("username", "ندارد")
        text = message.get("text", "")

        full_name = f"{first_name} {last_name}"

        info = f"""
📩 پیام جدید

👤 نام: {full_name}
🔗 یوزرنیم: @{username}
🆔 آیدی عددی: <code>{user_id}</code>

💬 پیام:
{text}
"""

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": GROUP_ID,
            "text": info,
            "parse_mode": "HTML"
        })

        group_message_id = r.json()["result"]["message_id"]

        cursor.execute("INSERT INTO messages VALUES (?,?)", (group_message_id, user_id))
        conn.commit()

    return "ok"

@app.route("/")
def home():
    return "Bot is running"
