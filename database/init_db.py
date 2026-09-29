import sqlite3
from pathlib import Path


# このファイルと同じdatabaseフォルダ内にlibrary.dbを作成
DB_PATH = Path(__file__).parent / "library.db"


def init_db():
    # SQLiteデータベースに接続
    conn = sqlite3.connect(DB_PATH)

    # SQLを実行するためのカーソルを作成
    cursor = conn.cursor()

    # booksテーブルを作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            author TEXT,
            publisher TEXT,
            media_type TEXT,
            genre TEXT,
            isbn TEXT,
            release_date TEXT,
            cover_image TEXT,
            tags TEXT,
            location TEXT,
            is_available INTEGER NOT NULL DEFAULT 1,
            is_owner_pick INTEGER NOT NULL DEFAULT 0,
            is_featured INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 変更を保存
    conn.commit()

    # データベースとの接続を終了
    conn.close()

    print("データベースを作成しました。")
    print(DB_PATH)


if __name__ == "__main__":
    init_db()