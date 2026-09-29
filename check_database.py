import sqlite3
from pathlib import Path


# ========================================
# データベースの場所
# ========================================

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "database" / "library.db"


print("=" * 60)
print("データベース確認")
print("=" * 60)

print(f"DBの場所：{DB_PATH}")
print(f"DBの存在：{DB_PATH.exists()}")


if not DB_PATH.exists():
    print()
    print("library.dbが見つかりませんでした。")
    print("check_database.pyをapp.pyと同じ階層に置いてください。")
    raise SystemExit


# ========================================
# データベース接続
# ========================================

conn = sqlite3.connect(DB_PATH)


# ========================================
# テーブル一覧
# ========================================

tables = conn.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
    """
).fetchall()


print()
print("=" * 60)
print("テーブル一覧")
print("=" * 60)

for table in tables:
    print(table[0])


# ========================================
# 各テーブルの構造
# ========================================

for table in tables:

    table_name = table[0]

    # SQLite内部テーブルは除外
    if table_name.startswith("sqlite_"):
        continue

    print()
    print("=" * 60)
    print(f"{table_name} テーブル")
    print("=" * 60)

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    print(
        "番号 | 列名 | データ型 | NOT NULL | 初期値 | 主キー"
    )

    for column in columns:
        print(
            f"{column[0]} | "
            f"{column[1]} | "
            f"{column[2]} | "
            f"{column[3]} | "
            f"{column[4]} | "
            f"{column[5]}"
        )

    count = conn.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    print(f"登録件数：{count}件")


# ========================================
# booksテーブルのインデックス
# ========================================

print()
print("=" * 60)
print("booksテーブルのインデックス")
print("=" * 60)

indexes = conn.execute(
    "PRAGMA index_list(books)"
).fetchall()

if indexes:
    for index in indexes:
        print(index)
else:
    print("インデックスは設定されていません。")


# ========================================
# booksテーブルの先頭データ
# ========================================

print()
print("=" * 60)
print("booksテーブルの先頭1件")
print("=" * 60)

book = conn.execute(
    "SELECT * FROM books LIMIT 1"
).fetchone()

if book is None:
    print("書籍データは登録されていません。")
else:
    column_names = [
        description[0]
        for description in conn.execute(
            "SELECT * FROM books LIMIT 1"
        ).description
    ]

    for column_name, value in zip(column_names, book):
        print(f"{column_name}：{value}")


conn.close()

print()
print("=" * 60)
print("確認完了")
print("=" * 60)