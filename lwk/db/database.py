import sqlite3
import json
from pathlib import Path
from lwk.models.user_profile import UserProfile

# Храним БД в lwk/data/lwk.db
DB_PATH = Path(__file__).parent.parent / "data" / "lwk.db"

class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_active INTEGER DEFAULT 0,
                settings TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_or_update_user(self, telegram_id: int, username: str, first_name: str):
        """Регистрация или обновление имени пользователя при повторном /start"""
        self.conn.execute("""
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name
        """, (telegram_id, username, first_name))
        self.conn.commit()

    def set_active(self, telegram_id: int, is_active: bool):
        """CRM: Активация или деактивация пользователя"""
        self.conn.execute(
            "UPDATE users SET is_active = ? WHERE telegram_id = ?",
            (1 if is_active else 0, telegram_id)
        )
        self.conn.commit()

    # --- НОВЫЕ МЕТОДЫ ДЛЯ БОТА ---

    def get_user_settings(self, telegram_id: int) -> dict:
        """Безопасно возвращает настройки пользователя как словарь"""
        cursor = self.conn.execute("SELECT settings FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        if row and row["settings"]:
            try:
                settings = json.loads(row["settings"])
                if isinstance(settings, dict):
                    return settings
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    def update_setting(self, telegram_id: int, key: str, value):
        """Обновляет один конкретный ключ в настройках (боту так проще)"""
        settings = self.get_user_settings(telegram_id)
        settings[key] = value
        self.conn.execute(
            "UPDATE users SET settings = ? WHERE telegram_id = ?",
            (json.dumps(settings, ensure_ascii=False), telegram_id)
        )
        self.conn.commit()

    def get_all_users(self) -> list[dict]:
        """Возвращает список всех пользователей для админ-панели"""
        cursor = self.conn.execute(
            "SELECT telegram_id, username, first_name, is_active, settings FROM users ORDER BY created_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def is_user_active(self, telegram_id: int) -> bool:
        """Проверяет, активен ли конкретный пользователь"""
        cursor = self.conn.execute("SELECT is_active FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        return bool(row and row["is_active"] == 1)

    # --- СУЩЕСТВУЮЩИЙ МЕТОД ДЛЯ ПАРСЕРА (main.py) ---

    def get_active_users(self) -> list[UserProfile]:
        """Загрузка профилей для матчинга (только активные)"""
        cursor = self.conn.execute("SELECT * FROM users WHERE is_active = 1")
        users = []
        for row in cursor.fetchall():
            settings = json.loads(row["settings"]) if row["settings"] else {}
            users.append(UserProfile(
                name=row["first_name"] or row["username"] or "User",
                telegram_id=row["telegram_id"],
                cities=settings.get("cities", []),
                min_salary=settings.get("min_salary"),
                required_visas=settings.get("required_visas", []),
                keywords=settings.get("keywords", [])
            ))
        return users