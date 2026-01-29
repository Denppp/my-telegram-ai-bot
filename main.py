# main.py — Telegram-бот с ИИ через Hugging Face Inference API
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "microsoft/Phi-3-mini-4k-instruct"  # можно заменить на "meta-llama/Llama-3.1-8B-Instruct"

def query_hf(prompt):
    API_URL = "https://api-inference.huggingface.co/models/" + HF_MODEL
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        data = response.json()
        if isinstance(data, list):
            return data[0].get("generated_text", "Ошибка генерации")
        return str(data.get("generated_text", data))
    except Exception as e:
        return f"Ошибка: {str(e)[:60]}"

@app.route("/", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" not in update:
        return jsonify({"ok": True})

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if text == "/start":
        reply = "Привет! Я — ИИ-помощник. Пишите — отвечу."
    else:
        # Формируем промпт для модели
        prompt = f"<|user|>{text}<|assistant|>"
        reply = query_hf(prompt)

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": reply}
    )
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port(os.environ.get("PORT", 8080)))
