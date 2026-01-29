import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔑 Загружаем токены
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "microsoft/Phi-3-mini-4k"

def query_hf(prompt):
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 512}}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()
        if isinstance(data, list):
            return data[0].get("generated_text", "Ошибка")
        return str(data.get("generated_text", data))
    except Exception as e:
        return f"ИИ недоступен: {str(e)[:50]}"

@app.route("/", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        if not update or "message" not in update:
            return jsonify({"ok": True})

        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text == "/start":
            reply = "Привет! Я — Денчик на базе Phi-3. Пишите — отвечу."
        else:
            prompt = f"<|user|>{text}<|assistant|>"
            reply = query_hf(prompt)

        # Отправка ответа
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply},
            timeout=5
        )

    except Exception as e:
        print("Ошибка:", e)

    return jsonify({"ok": True})

if __name__ == "__main__":
    # ✅ КРИТИЧЕСКИ ВАЖНО: правильно!
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
