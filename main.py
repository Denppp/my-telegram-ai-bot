import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Загружаем токены из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Убедись, что токены заданы
if not TELEGRAM_TOKEN or not HF_TOKEN:
    print("⚠️ ОШИБКА: Не заданы TELEGRAM_TOKEN или HF_TOKEN")

def query_hf(prompt):
    """Запрос к Hugging Face Inference API"""
    url = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "return_full_text": False,
            "do_sample": True
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        
        # Модель "спит" — ждёт загрузки
        if resp.status_code == 503:
            data = resp.json()
            if "estimated_time" in data:
                wait = int(data.get("estimated_time", 30))
                return f"Модель загружается... Попробуйте через {wait} секунд."
            else:
                return "Модель временно недоступна."

        # Успешный ответ
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                generated = data[0].get("generated_text", "").strip()
                # Убираем дубли исходного промпта (если модель его вернула)
                if generated.startswith(prompt):
                    generated = generated[len(prompt):].strip()
                return generated or "ИИ не дал ответа."
            return str(data)
        else:
            return f"Ошибка Hugging Face: {resp.status_code}"

    except Exception as e:
        return f"Ошибка сети: {str(e)[:80]}"

@app.route("/", methods=["POST"])
def webhook():
    """Обработка входящих сообщений от Telegram"""
    try:
        update = request.get_json()
        if not update or "message" not in update:
            return jsonify({"ok": True})

        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()

        # Приветствие
        if text == "/start":
            reply = "Привет! Я — Денчик на базе Дурка-3. Напишите любой вопрос — отвечу."
        else:
            # Формат промпта для Phi-3
            prompt = f"<|user|>{text}<|end|>\n<|assistant|>"
            reply = query_hf(prompt)

        # Отправка ответа в Telegram
        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        send_resp = requests.post(
            send_url,
            json={"chat_id": chat_id, "text": reply},
            timeout=5
        )
        if send_resp.status_code != 200:
            print(f"❌ Ошибка отправки в Telegram: {send_resp.text}")

    except Exception as e:
        print(f"🔥 Ошибка в обработке: {e}")

    return jsonify({"ok": True})

# Health-check (не обязателен, но полезен)
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "telegram-ai-bot"})

# Запуск локально (не используется в Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
