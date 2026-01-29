import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def query_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"  # ← без пробелов
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "tngtech/deepseek-r1t2-chimera:free",
        "messages": [
            {"role": "system", "content": "Ты — ИИ-Денчик на Durka-3.0. Отвечай коротко, дерзко и по делу."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.7
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            error = resp.json().get("error", {}).get("message", "Unknown")
            return f"Ошибка ИИ: {resp.status_code} — {error[:80]}"
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
            reply = "Привет! Я — ИИ-Денчик на Durka-3.0. Чо хотел?!"
        else:
            reply = query_ai(text)

        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",  # ← без пробелов
            json={"chat_id": chat_id, "text": reply},
            timeout=5
        )

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
