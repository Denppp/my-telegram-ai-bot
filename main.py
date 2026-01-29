import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not TELEGRAM_TOKEN or not HF_TOKEN:
    print("⚠️ ОШИБКА: Не заданы TELEGRAM_TOKEN или HF_TOKEN")

def query_hf(prompt):
    # Используем Gemma-2-2B — публичная, стабильная, быстрая
    url = "https://api-inference.huggingface.co/models/google/gemma-2-2b-it"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        
        if resp.status_code == 503:
            data = resp.json()
            if "estimated_time" in data:
                wait = int(data.get("estimated_time", 30))
                return f"Модель загружается... Попробуйте через {wait} сек."
            return "Модель временно недоступна."

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                text = data[0].get("generated_text", "").strip()
                # Убираем дубли промпта
                if text.startswith(prompt):
                    text = text[len(prompt):].strip()
                return text or "ИИ молчит."
            return str(data)
        else:
            return f"Ошибка Hugging Face: {resp.status_code}"

    except Exception as e:
        return f"Ошибка сети: {str(e)[:80]}"

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
            reply = "Привет! Я — Денчик на базе Дурка-3. Чо хочешь?!"
        else:
            # Для Gemma используем простой промпт
            prompt = f"Question: {text}\nAnswer:"
            reply = query_hf(prompt)

        # Отправка ответа
        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(send_url, json={"chat_id": chat_id, "text": reply}, timeout=5)

    except Exception as e:
        print(f"Ошибка: {e}")

    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
