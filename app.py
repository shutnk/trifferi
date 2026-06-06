import threading
import requests
import time
import json
from flask import Flask, render_template

TOKEN = "8934522015:AAHJuYuqOu9-CYyhTZavQ-MDlCn1Sw4T4vw"
WEB_URL = "https://ba5a204e401767.lhr.life"
API_URL = "https://api.telegram.org/bot" + TOKEN

running = True

app = Flask(__name__, template_folder="templates")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/catalog")
def catalog():
    return render_template("catalog.html")

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

def send_message(chat_id, text, keyboard=None):
    try:
        url = API_URL + "/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if keyboard:
            data["reply_markup"] = json.dumps({"inline_keyboard": keyboard})
        resp = requests.post(url, json=data, timeout=5)
        print("Sent:", resp.status_code)
    except Exception as e:
        print("Send error:", e)

def get_updates(offset=0):
    try:
        url = API_URL + "/getUpdates"
        params = {"offset": offset, "timeout": 5}
        r = requests.post(url, json=params, timeout=10)
        return r.json().get("result", [])
    except Exception as e:
        print("Get error:", e)
        return []

def handle_update(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        print("Message:", text)
        if text == "/start":
            kb = [[{"text": "\U0001F6CD Открыть магазин", "web_app": {"url": WEB_URL}}]]
            send_message(chat_id, "\U0001F44B Привет! Добро пожаловать в TRIFFERI \u2728", kb)

def run_bot():
    global running
    print("Bot starting...")
    offset = 0
    while running:
        try:
            updates = get_updates(offset)
            for upd in updates:
                offset = upd["update_id"] + 1
                handle_update(upd)
            time.sleep(0.5)
        except:
            time.sleep(1)

def run_flask():
    print("Flask running...")
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("TRIFFERI starting...")
    print("URL:", WEB_URL)
    t1 = threading.Thread(target=run_flask, daemon=True)
    t1.start()
    run_bot()
