import sqlite3
from datetime import datetime
from pathlib import Path


# ========================================
# ファイル・フォルダの場所
# ========================================

BASE_DIR = Path(__file__).parent

DB_PATH = BASE_DIR / "database" / "library.db"

BACKUP_DIR = BASE_DIR / "database" / "backups"


# ========================================
# バックアップファイル名を作成
# ========================================

def create_backup_path():

    today = datetime.now().strftime("%Y%m%d")

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    number = 1

    while True:

        backup_filename = (
            f"library_before_phase1_"
            f"{today}_{number:02d}.db"
        )

        backup_path = (
            BACKUP_DIR / backup_filename
        )

        if not backup_path.exists():
            return backup_path

        number += 1


# ========================================
# SQLiteのバックアップ
# ========================================

def backup_database():

    backup_path = create_backup_path()

    source_conn = sqlite3.connect(DB_PATH)

    backup_conn = sqlite3.connect(backup_path)

    try:

        source_conn.backup(backup_conn)

    finally:

        backup_conn.close()
        source_conn.close()

    return backup_path


# ========================================
# 現在の列名を取得
# ========================================

def get_column_names(conn, table_name):

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        column[1]
        for column in columns
    }


# ========================================
# 列がなければ追加
# ========================================

def add_column_if_missing(
    conn,
    table_name,
    column_name,
    column_definition
):

    current_columns = get_column_names(
        conn,
        table_name
    )

    if column_name in current_columns:

        print(
            f"変更なし："
            f"{table_name}.{column_name}"
            f" はすでに存在します。"
        )

        return

    conn.execute(
        f"""
        ALTER TABLE {table_name}
        ADD COLUMN {column_name}
        {column_definition}
        """
    )

    print(
        f"列を追加："
        f"{table_name}.{column_name}"
    )


# ========================================
# PHASE1用DB移行
# ========================================

def migrate_database():

    if not DB_PATH.exists():

        print(
            "library.dbが見つかりません。"
        )

        print(
            f"確認場所：{DB_PATH}"
        )

        return

    print("=" * 60)
    print("PHASE1 データベース移行")
    print("=" * 60)

    print(f"対象DB：{DB_PATH}")

    # 最初にバックアップを作成
    backup_path = backup_database()

    print()
    print(
        f"バックアップ作成："
        f"{backup_path}"
    )

    conn = sqlite3.connect(DB_PATH)

    # 外部キー制約を有効にする
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:

        # ------------------------------
        # トランザクション開始
        # ------------------------------

        conn.execute("BEGIN")

        print()
        print("=" * 60)
        print("booksテーブルへの列追加")
        print("=" * 60)

        add_column_if_missing(
            conn,
            "books",
            "casican_id",
            "TEXT"
        )

        add_column_if_missing(
            conn,
            "books",
            "quantity",
            "INTEGER NOT NULL DEFAULT 1"
        )

        add_column_if_missing(
            conn,
            "books",
            "is_hidden",
            "INTEGER NOT NULL DEFAULT 0"
        )

        add_column_if_missing(
            conn,
            "books",
            "casican_url",
            "TEXT"
        )

        add_column_if_missing(
            conn,
            "books",
            "casican_qr_url",
            "TEXT"
        )

        add_column_if_missing(
            conn,
            "books",
            "casican_created_at",
            "TEXT"
        )

        add_column_if_missing(
            conn,
            "books",
            "updated_at",
            "TEXT"
        )

        # 既存データのupdated_atを、
        # 現在のcreated_atで初期化する
        conn.execute(
            """
            UPDATE books
            SET updated_at = created_at
            WHERE updated_at IS NULL
            """
        )

        # ------------------------------
        # カシカンIDの重複防止
        # ------------------------------

        conn.execute(
            """
            CREATE UNIQUE INDEX
            IF NOT EXISTS
            idx_books_casican_id
            ON books(casican_id)
            """
        )

        print(
            "インデックス確認："
            "idx_books_casican_id"
        )

        # ------------------------------
        # tagsテーブル
        # ------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                tag_id INTEGER
                    PRIMARY KEY AUTOINCREMENT,

                tag_name TEXT
                    NOT NULL
                    UNIQUE,

                tag_type TEXT,

                icon TEXT,

                display_order INTEGER
                    NOT NULL
                    DEFAULT 0
            )
            """
        )

        print(
            "テーブル確認：tags"
        )

        # ------------------------------
        # book_tagsテーブル
        # ------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS book_tags (
                book_id INTEGER
                    NOT NULL,

                tag_id INTEGER
                    NOT NULL,

                PRIMARY KEY (
                    book_id,
                    tag_id
                ),

                FOREIGN KEY (book_id)
                    REFERENCES books(book_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (tag_id)
                    REFERENCES tags(tag_id)
                    ON DELETE CASCADE
            )
            """
        )

        print(
            "テーブル確認：book_tags"
        )

        # すべて成功した場合だけ確定
        conn.commit()

        print()
        print("=" * 60)
        print("データベース移行完了")
        print("=" * 60)

    except Exception as error:

        conn.rollback()

        print()
        print("=" * 60)
        print("移行に失敗しました")
        print("=" * 60)

        print(error)

        print()
        print(
            "DBへの変更は取り消されました。"
        )

        print(
            "移行前のバックアップも"
            "保存されています。"
        )

        return

    finally:

        conn.close()


# ========================================
# 移行結果の確認
# ========================================

def check_result():

    conn = sqlite3.connect(DB_PATH)

    print()
    print("=" * 60)
    print("移行後の確認")
    print("=" * 60)

    tables = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    print()
    print("テーブル一覧：")

    for table in tables:
        print(f"・{table[0]}")

    columns = conn.execute(
        "PRAGMA table_info(books)"
    ).fetchall()

    print()
    print("booksテーブルの列：")

    for column in columns:
        print(
            f"・{column[1]} "
            f"({column[2]})"
        )

    indexes = conn.execute(
        "PRAGMA index_list(books)"
    ).fetchall()

    print()
    print("booksテーブルのインデックス：")

    for index in indexes:
        print(f"・{index[1]}")

    book_count = conn.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    user_count = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    print()
    print(f"書籍件数：{book_count}件")
    print(f"ユーザー件数：{user_count}件")

    conn.close()


# ========================================
# このファイルを直接実行した場合
# ========================================

if __name__ == "__main__":

    migrate_database()

    check_result()