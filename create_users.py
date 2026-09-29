import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "library.db"
print("DB_PATH;", DB_PATH)


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# usersテーブルを作成
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL
)
""")


# 動作確認用ユーザー
users = [
    ("user01", "test1234", "一般ユーザー", "user"),
    ("admin01", "admin1234", "管理者", "admin")
]


for user in users:
    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, password, name, role)
        VALUES (?, ?, ?, ?)
    """, user)


conn.commit()
conn.close()

print("usersテーブルの作成とテストユーザーの登録が完了しました。")