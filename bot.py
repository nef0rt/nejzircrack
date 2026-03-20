import telebot
import json
import os
import random
import string
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

BOT_TOKEN = "8255755052:AAFjHxgUKDccQVi33kWGuUXkARcR85CxXDQ"
DB_FILE = "key.json"

# ==================== DATABASE ====================

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    data = {"users": {}}
    save_db(data)
    return data

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_key():
    chars = string.ascii_uppercase + string.digits
    p1 = ''.join(random.choices(chars, k=4))
    p2 = ''.join(random.choices(chars, k=4))
    return f"{p1}-{p2}"

def is_key_valid(key):
    data = load_db()
    for uid, info in data["users"].items():
        if info["key"] == key:
            return True, info["name"]
    return False, None

# ==================== TELEGRAM BOT ====================

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or "User"
    username = message.from_user.username or "нет"

    data = load_db()

    if user_id in data["users"]:
        key = data["users"][user_id]["key"]
    else:
        key = generate_key()
        # убедимся что ключ уникален
        existing_keys = [u["key"] for u in data["users"].values()]
        while key in existing_keys:
            key = generate_key()

        data["users"][user_id] = {
            "key": key,
            "name": name,
            "username": username
        }
        save_db(data)

    bot.send_message(
        message.chat.id,
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Вот твой ключ для <b>Neizzir Crack Free</b>\n"
        f"(кряк платного Neizzir):\n\n"
        f"🔑 Ключ: <code>{key}</code>\n\n"
        f"📋 Нажми на ключ чтобы скопировать\n"
        f"💉 Вставь его в приложение Neizzir для активации",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['mykey'])
def cmd_mykey(message):
    user_id = str(message.from_user.id)
    data = load_db()

    if user_id in data["users"]:
        key = data["users"][user_id]["key"]
        bot.send_message(
            message.chat.id,
            f"🔑 Твой ключ: <code>{key}</code>",
            parse_mode='HTML'
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ У тебя нет ключа. Нажми /start чтобы получить."
        )

# ==================== HTTP API SERVER ====================

class KeyAPIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/api/validate':
            params = urllib.parse.parse_qs(parsed.query)
            key = params.get('key', [''])[0].strip().upper()

            valid, name = is_key_valid(key)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            resp = json.dumps({"valid": valid, "name": name})
            self.wfile.write(resp.encode())

        elif parsed.path == '/api/keys':
            # для дебага — список всех ключей
            data = load_db()
            keys_list = [
                {"user_id": uid, "key": info["key"], "name": info["name"]}
                for uid, info in data["users"].items()
            ]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(keys_list, ensure_ascii=False).encode())

        elif parsed.path == '/' or parsed.path == '/index.html':
            # отдаём index.html
            try:
                with open('index.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"index.html not found")
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # тихий режим

def run_api_server(port=5000):
    server = HTTPServer(('0.0.0.0', port), KeyAPIHandler)
    print(f"🌐 API сервер: http://localhost:{port}")
    print(f"🌐 Приложение: http://localhost:{port}/index.html")
    server.serve_forever()

# ==================== MAIN ====================

if __name__ == '__main__':
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║      NEIZZIR KEY SYSTEM v1.0         ║")
    print("  ║      Black Russia Cheat Panel        ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    # Создаём БД если нет
    load_db()
    print(f"📂 База данных: {DB_FILE}")

    # Запускаем API сервер в фоне
    api_thread = Thread(target=run_api_server, args=(5000,), daemon=True)
    api_thread.start()

    # Запускаем бота
    print("🤖 Бот @FraZzerNFTBot запущен...")
    print("=" * 42)
    print()

    bot.infinity_polling()
