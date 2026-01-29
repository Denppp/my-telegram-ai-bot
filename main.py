import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Загружаем токены из переменных окружения (безопасно!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Проверка на старте
if not TELEGRAM_TOKEN:
    print("⚠️ ОШИБКА: Не задан TELEGRAM_TOKEN")
if not OPENROUTER_API_KEY:
    print("⚠️ ОШИБКА: Не задан OPENROUTER_API_KEY")

def query_ai(prompt):
    """Запрос к OpenRouter (OpenAI-compatible API)"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/gemma-2-2b-it",
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
        if not
