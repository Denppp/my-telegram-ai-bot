import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # ← теперь правильно!

def query_ai(prompt):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты — полезный, краткий и вежливый помощник."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.7
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            error_msg = resp.json().get("error", {}).get("message", "Unknown error")
            return f"Ошибка ИИ: {resp.status_code} — {error_msg[:80]}"
    except Exception as e:
        return f"Сеть: {str(e)[:80]}"

@app.route("/", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        if not update or "message" not in update:
            return jsonify({"ok": True})

        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()

        if text == "/start":
            reply = "Привет! Я — ИИ-бот на базе DeepSeek. Задайте любой вопрос!"
        else:
            reply = query_ai(text)

        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(
            send_url,
            json={"chat_id": chat_id, "text": reply},
            timeout=5
        )

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
