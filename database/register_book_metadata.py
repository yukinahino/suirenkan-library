import sqlite3
from datetime import datetime
from pathlib import Path


# ========================================
# ファイル・フォルダの場所
# ========================================

DATABASE_DIR = Path(__file__).resolve().parent
DB_PATH = DATABASE_DIR / "library.db"
BACKUP_DIR = DATABASE_DIR / "backups"


# ========================================
# タグの初期データ
# ========================================

TAGS = [
    ("泣ける", "気分", "😢", 1),
    ("考えさせられる", "気分", "💭", 2),
    ("心を整える", "気分", "🌿", 3),
    ("週末にじっくり", "シチュエーション", "☕", 4),
    ("気軽に読める", "シチュエーション", "📖", 5),
    ("暮らしを楽しむ", "シチュエーション", "🏠", 6),
    ("旅に出たい", "シチュエーション", "✈", 7),
    ("創作のヒント", "目的", "🎨", 8),
    ("仕事に役立つ", "目的", "💼", 9),
    ("学びたい", "目的", "📚", 10),
]


# ========================================
# 書籍ごとの分類
# ========================================

BOOK_SETTINGS = [
    {
        "book_id": 1,
        "media_type": "絵本",
        "genre": "文学・絵本",
        "tags": [
            "泣ける",
            "考えさせられる",
            "週末にじっくり",
        ],
        "owner_pick": 1,
        "featured": 1,
    },
    {
        "book_id": 2,
        "media_type": "書籍",
        "genre": "芸術・哲学",
        "tags": [
            "考えさせられる",
            "創作のヒント",
            "週末にじっくり",
        ],
        "owner_pick": 1,
        "featured": 0,
    },
    {
        "book_id": 3,
        "media_type": "書籍",
        "genre": "デザイン",
        "tags": [
            "仕事に役立つ",
            "学びたい",
            "創作のヒント",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
    {
        "book_id": 4,
        "media_type": "書籍",
        "genre": "自己啓発・健康",
        "tags": [
            "心を整える",
            "気軽に読める",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
    {
        "book_id": 5,
        "media_type": "書籍",
        "genre": "ビジネス",
        "tags": [
            "仕事に役立つ",
            "学びたい",
            "週末にじっくり",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
    {
        "book_id": 6,
        "media_type": "書籍",
        "genre": "健康・暮らし",
        "tags": [
            "心を整える",
            "暮らしを楽しむ",
            "気軽に読める",
        ],
        "owner_pick": 1,
        "featured": 0,
    },
    {
        "book_id": 7,
        "media_type": "書籍",
        "genre": "ビジネス",
        "tags": [
            "仕事に役立つ",
            "学びたい",
            "創作のヒント",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
    {
        "book_id": 8,
        "media_type": "書籍",
        "genre": "ビジネス",
        "tags": [
            "仕事に役立つ",
            "学びたい",
            "創作のヒント",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
    {
        "book_id": 9,
        "media_type": "書籍",
        "genre": "社会・経済",
        "tags": [
            "考えさせられる",
            "仕事に役立つ",
            "週末にじっくり",
        ],
        "owner_pick": 1,
        "featured": 0,
    },
    {
        "book_id": 10,
        "media_type": "書籍",
        "genre": "哲学・暮らし",
        "tags": [
            "考えさせられる",
            "暮らしを楽しむ",
            "気軽に読める",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
    {
        "book_id": 11,
        "media_type": "書籍",
        "genre": "語学・旅行",
        "tags": [
            "学びたい",
            "旅に出たい",
            "気軽に読める",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
    {
        "book_id": 12,
        "media_type": "書籍",
        "genre": "語学・旅行",
        "tags": [
            "学びたい",
            "旅に出たい",
            "気軽に読める",
        ],
        "owner_pick": 0,
        "featured": 0,
    },
]


# ========================================
# DBバックアップ
# ========================================

def backup_database():

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / f"library_before_metadata_{timestamp}.db"
    )

    source_conn = sqlite3.connect(DB_PATH)
    backup_conn = sqlite3.connect(backup_path)

    try:
        source_conn.backup(backup_conn)

    finally:
        backup_conn.close()
        source_conn.close()

    return backup_path


# ========================================
# 分類・タグを登録
# ========================================

def register_metadata():

    print("=" * 60)
    print("書籍分類・タグ登録")
    print("=" * 60)

    if not DB_PATH.exists():

        print(
            "library.dbが見つかりません。"
        )

        print(f"確認場所：{DB_PATH}")

        return

    backup_path = backup_database()

    print(
        f"バックアップ：{backup_path}"
    )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    try:

        conn.execute("BEGIN")

        # ------------------------------
        # 対象書籍の存在確認
        # ------------------------------

        book_ids = {
            row["book_id"]
            for row in conn.execute(
                "SELECT book_id FROM books"
            ).fetchall()
        }

        required_ids = {
            setting["book_id"]
            for setting in BOOK_SETTINGS
        }

        missing_ids = (
            required_ids - book_ids
        )

        if missing_ids:

            raise ValueError(
                "存在しないbook_id："
                + ", ".join(
                    str(book_id)
                    for book_id
                    in sorted(missing_ids)
                )
            )

        # ------------------------------
        # タグを登録
        # ------------------------------

        for tag in TAGS:

            conn.execute(
                """
                INSERT INTO tags (
                    tag_name,
                    tag_type,
                    icon,
                    display_order
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(tag_name)
                DO UPDATE SET
                    tag_type =
                        excluded.tag_type,
                    icon =
                        excluded.icon,
                    display_order =
                        excluded.display_order
                """,
                tag
            )

        tag_rows = conn.execute(
            """
            SELECT tag_id, tag_name
            FROM tags
            """
        ).fetchall()

        tag_ids = {
            row["tag_name"]: row["tag_id"]
            for row in tag_rows
        }

        # ------------------------------
        # MV指定を一旦解除
        # ------------------------------

        conn.execute(
            """
            UPDATE books
            SET is_featured = 0
            """
        )

        # ------------------------------
        # 書籍へ分類・タグを登録
        # ------------------------------

        for setting in BOOK_SETTINGS:

            book_id = setting["book_id"]

            conn.execute(
                """
                UPDATE books
                SET
                    media_type = ?,
                    genre = ?,
                    is_owner_pick = ?,
                    is_featured = ?,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE book_id = ?
                """,
                (
                    setting["media_type"],
                    setting["genre"],
                    setting["owner_pick"],
                    setting["featured"],
                    book_id,
                )
            )

            # 既存のタグ関連を解除
            conn.execute(
                """
                DELETE FROM book_tags
                WHERE book_id = ?
                """,
                (book_id,)
            )

            # 新しいタグを関連づける
            for tag_name in setting["tags"]:

                tag_id = tag_ids[tag_name]

                conn.execute(
                    """
                    INSERT INTO book_tags (
                        book_id,
                        tag_id
                    )
                    VALUES (?, ?)
                    """,
                    (
                        book_id,
                        tag_id,
                    )
                )

        conn.commit()

    except Exception as error:

        conn.rollback()

        print()
        print("登録に失敗しました。")
        print(error)
        print("DBの変更は取り消されました。")

        conn.close()

        return

    # ====================================
    # 登録結果を確認
    # ====================================

    books = conn.execute(
        """
        SELECT
            books.book_id,
            books.title,
            books.media_type,
            books.genre,
            books.is_owner_pick,
            books.is_featured,
            GROUP_CONCAT(
                tags.tag_name,
                '／'
            ) AS tag_names

        FROM books

        LEFT JOIN book_tags
            ON books.book_id =
               book_tags.book_id

        LEFT JOIN tags
            ON book_tags.tag_id =
               tags.tag_id

        GROUP BY books.book_id

        ORDER BY books.book_id
        """
    ).fetchall()

    tag_count = conn.execute(
        "SELECT COUNT(*) FROM tags"
    ).fetchone()[0]

    conn.close()

    print()
    print("=" * 60)
    print("登録結果")
    print("=" * 60)

    for book in books:

        print()
        print(
            f"{book['book_id']}："
            f"{book['title']}"
        )

        print(
            f"  種別：{book['media_type']}"
        )

        print(
            f"  ジャンル：{book['genre']}"
        )

        print(
            f"  タグ：{book['tag_names']}"
        )

        print(
            f"  イチオシ："
            f"{book['is_owner_pick']}"
        )

        print(
            f"  MV：{book['is_featured']}"
        )

    print()
    print("=" * 60)
    print("登録完了")
    print("=" * 60)

    print(f"登録書籍：{len(books)}件")
    print(f"登録タグ：{tag_count}件")


# ========================================
# 直接実行した場合
# ========================================

if __name__ == "__main__":

    register_metadata()