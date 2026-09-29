import csv
import sqlite3
from datetime import datetime
from pathlib import Path


# ========================================
# プロジェクトのルートを探す
# ========================================

def find_base_dir():

    current_dir = Path(__file__).resolve().parent

    while current_dir != current_dir.parent:

        database_path = (
            current_dir
            / "database"
            / "library.db"
        )

        if database_path.exists():
            return current_dir

        current_dir = current_dir.parent

    raise FileNotFoundError(
        "database/library.dbが"
        "見つかりませんでした。"
    )


BASE_DIR = find_base_dir()

DB_PATH = (
    BASE_DIR
    / "database"
    / "library.db"
)

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "export"
)


# ========================================
# 出力ファイル名を作成
# ========================================

def create_export_path():

    today = datetime.now().strftime(
        "%Y%m%d"
    )

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    number = 1

    while True:

        filename = (
            f"books_master_"
            f"{today}_{number:02d}.csv"
        )

        export_path = (
            EXPORT_DIR / filename
        )

        if not export_path.exists():
            return export_path

        number += 1


# ========================================
# 0／1をTRUE／FALSEへ変換
# ========================================

def convert_boolean(value):

    if value == 1:
        return "TRUE"

    return "FALSE"


# ========================================
# 全所蔵書籍CSVを出力
# ========================================

def export_books():

    print("=" * 60)
    print("全所蔵書籍CSV出力")
    print("=" * 60)

    print(f"対象DB：{DB_PATH}")

    if not DB_PATH.exists():

        print(
            "library.dbが見つかりません。"
        )

        return

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    try:

        books = conn.execute(
            """
            SELECT
                books.book_id,
                books.casican_id,
                books.title,
                books.description,
                books.author,
                books.publisher,
                books.media_type,
                books.genre,
                books.isbn,
                books.release_date,
                books.cover_image,

                COALESCE(
                    GROUP_CONCAT(
                        tags.tag_name,
                        '|'
                    ),
                    books.tags,
                    ''
                ) AS mood_tags,

                books.location,
                books.quantity,
                books.is_available,
                books.is_owner_pick,
                books.is_featured,
                books.is_hidden,
                books.casican_url,
                books.casican_qr_url,
                books.casican_created_at,
                books.created_at,
                books.updated_at

            FROM books

            LEFT JOIN book_tags
                ON books.book_id
                = book_tags.book_id

            LEFT JOIN tags
                ON book_tags.tag_id
                = tags.tag_id

            GROUP BY books.book_id

            ORDER BY books.book_id
            """
        ).fetchall()

    finally:

        conn.close()

    if not books:

        print(
            "出力できる書籍がありません。"
        )

        return

    export_path = create_export_path()

    fieldnames = [
        "book_id",
        "casican_id",
        "title",
        "description",
        "author",
        "publisher",
        "media_type",
        "genre",
        "isbn",
        "release_date",
        "cover_image",
        "mood_tags",
        "location",
        "quantity",
        "is_available",
        "is_owner_pick",
        "is_featured",
        "is_hidden",
        "casican_url",
        "casican_qr_url",
        "casican_created_at",
        "created_at",
        "updated_at",
    ]

    with open(
        export_path,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for book in books:

            row = dict(book)

            row["is_available"] = (
                convert_boolean(
                    book["is_available"]
                )
            )

            row["is_owner_pick"] = (
                convert_boolean(
                    book["is_owner_pick"]
                )
            )

            row["is_featured"] = (
                convert_boolean(
                    book["is_featured"]
                )
            )

            row["is_hidden"] = (
                convert_boolean(
                    book["is_hidden"]
                )
            )

            writer.writerow(row)

    print()
    print("CSV出力が完了しました。")

    print(
        f"出力件数：{len(books)}件"
    )

    print(
        f"保存先：{export_path}"
    )


# ========================================
# このファイルを直接実行した場合
# ========================================

if __name__ == "__main__":

    export_books()