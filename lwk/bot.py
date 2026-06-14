import os
import time
import json
import requests
from dotenv import load_dotenv
from lwk.db.database import Database

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Твой Telegram ID и ID помощников (через запятую).
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS is missing in .env")


class TelegramBot:
    def __init__(self):
        self.db = Database()
        self.offset = 0

    def _get(self, method, **params):
        try:
            resp = requests.get(f"{API_URL}{method}", params=params, timeout=30)
            data = resp.json()
            
            # ВРЕМЕННАЯ ОТЛАДКА: выводим сырой ответ от Telegram API
            if method == "getUpdates":
                print(f"DEBUG: getUpdates response type = {type(data)}")
                if isinstance(data, dict):
                    print(f"DEBUG: 'ok' = {data.get('ok')}, 'result' type = {type(data.get('result'))}")
            
            return data
        except Exception as e:  # Ловим ВСЕ исключения, включая JSONDecodeError
            print(f"Telegram GET error: {e}")
            return {"ok": False}

    def _post(self, method, **data):
        try:
            resp = requests.post(f"{API_URL}{method}", json=data, timeout=30)
            return resp.json()
        except Exception as e:
            print(f"Telegram POST error: {e}")
            return {"ok": False}

    def send_message(self, chat_id, text):
        self._post("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML")

    def process_update(self, update):
        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        user = message.get("from", {})
        username = user.get("username", "")
        first_name = user.get("first_name", "")

        # 1. Маршрутизация: Админ или Пользователь?
        if chat_id in ADMIN_IDS:
            self._handle_admin(chat_id, text)
        else:
            self._handle_user(chat_id, text, username, first_name)

    def _handle_user(self, chat_id, text, username, first_name):
        # Регистрация при первом контакте
        self.db.add_or_update_user(chat_id, username, first_name)

        if text == "/start":
            self.db.add_or_update_user(chat_id, username, first_name)
            msg = (
                f"👋 Привет, {first_name or 'друг'}!\n\n"
                f"Я бот для поиска вакансий в Южной Корее 🇰\n\n"
                f"Отправь /help, чтобы увидеть список команд"
            )
            self.send_message(chat_id, msg)
            return

        if text == "/help":
            msg = (
                "📚 <b>Доступные команды:</b>\n\n"
                "👤 <b>Профиль:</b>\n"
                "  /profile - Показать мой профиль\n"
                "  /set_cities - Изменить города\n"
                "  /set_keywords - Изменить ключевые слова\n"
                "  /set_salary - Изменить мин. зарплату\n\n"
                "💡 <b>Примеры:</b>\n"
                "  /set_cities Сеул, Пусан\n"
                "  /set_keywords Python, IT\n"
                "  /set_salary 3000000"
            )
            self.send_message(chat_id, msg)
            return

        if text == "/profile":
            settings = self.db.get_user_settings(chat_id)
            cities = ", ".join(settings.get("cities", [])) or "Не указаны"
            keywords = ", ".join(settings.get("keywords", [])) or "Не указаны"
            salary = settings.get("min_salary") or "Не указана"
            
            status = "✅ Активен" if self.db.is_user_active(chat_id) else "⏳ Ожидает активации"

            msg = (
                f"📊 <b>Твой профиль:</b>\n\n"
                f"📍 Города: {cities}\n"
                f"🔑 Ключевые слова: {keywords}\n"
                f"💰 Мин. зарплата: {salary} KRW\n"
                f"📌 Статус: {status}\n\n"
                f"Используй /help, чтобы изменить настройки"
            )
            self.send_message(chat_id, msg)
            return

        elif text.startswith("/set_cities"):
            if len(text.split()) < 2:
                self.send_message(chat_id, "❌ Формат: <code>/set_cities Сеул, Пусан</code>")
                return
            cities = [c.strip() for c in text.replace("/set_cities", "").strip().split(",") if c.strip()]
            self.db.update_setting(chat_id, "cities", cities)
            self.send_message(chat_id, f"✅ Города обновлены: {', '.join(cities)}")
            return

        elif text.startswith("/set_keywords"):
            if len(text.split()) < 2:
                self.send_message(chat_id, "❌ Формат: <code>/set_keywords Python, IT</code>")
                return
            keywords = [k.strip() for k in text.replace("/set_keywords", "").strip().split(",") if k.strip()]
            self.db.update_setting(chat_id, "keywords", keywords)
            self.send_message(chat_id, f"✅ Ключевые слова обновлены: {', '.join(keywords)}")
            return

        elif text.startswith("/set_salary"):
            if len(text.split()) < 2:
                self.send_message(chat_id, "❌ Формат: <code>/set_salary 3000000</code>")
                return
            try:
                salary = int(text.replace("/set_salary", "").strip().replace(" ", ""))
                self.db.update_setting(chat_id, "min_salary", salary)
                self.send_message(chat_id, f"✅ Мин. зарплата: {salary:,} KRW")
            except ValueError:
                self.send_message(chat_id, "❌ Введите число: <code>/set_salary 3000000</code>")
            return

        elif text.startswith("/"):
            self.send_message(chat_id, "❓ Неизвестная команда. Отправь /help для списка команд.")    
            
    def _handle_admin(self, chat_id, text):
        if text == "/help" or text == "/start":
            msg = (
                "🔧 <b>Админ-панель:</b>\n\n"
                "👥 <b>Управление пользователями:</b>\n"
                "  /users - Список всех пользователей\n"
                "  /activate &lt;id&gt; - Активировать\n"
                "  /deactivate &lt;id&gt; - Деактивировать\n\n"
                "💡 <b>Примеры:</b>\n"
                "  /activate 123456789\n"
                "  /deactivate 987654321"
            )
            self.send_message(chat_id, msg)
            return

        if text == "/users":
            users = self.db.get_all_users()
            if not users:
                self.send_message(chat_id, "Пользователей пока нет.")
                return
            
            msg = "<b>👥 Пользователи:</b>\n\n"
            for u in users:
                status = "🟢" if u["is_active"] else "🔴"
                name = u["first_name"] or u["username"] or "Unknown"
                
                try:
                    settings = json.loads(u["settings"]) if u["settings"] else {}
                    if not isinstance(settings, dict):
                        settings = {}
                except (json.JSONDecodeError, TypeError):
                    settings = {}
                
                keywords_list = settings.get("keywords", [])
                if not isinstance(keywords_list, list):
                    keywords_list = []
                
                keywords = ", ".join(keywords_list[:3]) if keywords_list else "Нет ключей"
                
                msg += f"{status} <code>{u['telegram_id']}</code> | {name}\n"
                msg += f"   🔑 {keywords}\n"
            
            msg += "\n<i>/help - помощь, /activate &lt;id&gt; - активировать</i>"
            self.send_message(chat_id, msg)
            return

        elif text.startswith("/activate "):
            try:
                user_id = int(text.split()[1])
                self.db.set_active(user_id, True)
                self.send_message(chat_id, f"✅ Пользователь <code>{user_id}</code> активирован.")
                self._post("sendMessage", chat_id=user_id, text="🎉 Ваш профиль активирован! Теперь вы будете получать вакансии.")
            except (IndexError, ValueError):
                self.send_message(chat_id, "❌ Формат: <code>/activate 123456789</code>")

        elif text.startswith("/deactivate "):
            try:
                user_id = int(text.split()[1])
                self.db.set_active(user_id, False)
                self.send_message(chat_id, f"⛔ Пользователь <code>{user_id}</code> деактивирован.")
            except (IndexError, ValueError):
                self.send_message(chat_id, "❌ Формат: <code>/deactivate 123456789</code>")

    def run(self):
        print("🤖 Bot started. Listening for updates...")
        while True:
            try:
                updates = self._get("getUpdates", offset=self.offset, timeout=35)
                
                # Проверяем, что updates - это словарь
                if not isinstance(updates, dict):
                    print(f"ERROR: updates is not a dict! Type: {type(updates)}, Value: {updates}")
                    time.sleep(5)
                    continue
                
                if updates.get("ok"):
                    result = updates.get("result", [])
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА: result должен быть списком
                    if not isinstance(result, list):
                        print(f"ERROR: 'result' is not a list!")
                        print(f"  Type: {type(result)}")
                        print(f"  Value: {result}")
                        print(f"  Full response: {updates}")
                        time.sleep(5)
                        continue
                    
                    # Теперь безопасно итерируемся
                    for update in result:
                        self.offset = update["update_id"] + 1
                        self.process_update(update)
                else:
                    print(f"Telegram API error: {updates.get('description')}")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"Bot connection error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env")
    else:
        TelegramBot().run()