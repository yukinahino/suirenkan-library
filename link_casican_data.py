import csv
import sqlite3
from collections import Counter
from pathlib import Path


# ========================================
# ファイル・フォルダの場所
# ========================================

BASE_DIR = Path(__file__).parent

DB_PATH = (
    BASE_DIR
    / "database"
    / "library.db"
)

IMPORT_DIR = (
    BASE_DIR
    / "data"
    / "import"
)

HISTORY_DIR = (
    BASE_DIR
    / "data"
    / "import_history"
)


# ========================================
# 使用するCSVを探す
# ========================================

def find_csv_file():

    # 未処理のCSVを優先
    import_files = sorted(
        IMPORT_DIR.glob("*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    if import_files:
        return import_files[0]

    # なければ履歴内の最新CSVを使用
    history_files = sorted(
        HISTORY_DIR.glob("*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    if history_files:
        return history_files[0]

    return None


# ========================================
# 文字列を比較用に整える
# ========================================

def normalize_text(value):

    if value is None:
        return ""

    return str(value).strip()


# ========================================
# TRUE／FALSEを0／1へ変換
# ========================================

def convert_boolean(value):

    normalized_value = normalize_text(
        value
    ).upper()

    if normalized_value == "TRUE":
        return 1

    return 0


# ========================================
# 数値を変換
# ========================================

def convert_integer(value, default=0):

    normalized_value = normalize_text(
        value
    )

    if normalized_value == "":
        return default

    try:
        return int(normalized_value)

    except ValueError:
        return default


# ========================================
# CSV読み込み
# ========================================

def read_csv(csv_path):

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        return list(reader)


# ========================================
# 既存書籍との照合
# ========================================

def link_casican_data():

    print("=" * 60)
    print("既存書籍とカシカンCSVの紐づけ")
    print("=" * 60)

    if not DB_PATH.exists():

        print(
            "library.dbが見つかりません。"
        )

        print(f"確認場所：{DB_PATH}")

        return

    csv_path = find_csv_file()

    if csv_path is None:

        print(
            "照合に使用できるCSVが"
            "見つかりません。"
        )

        print()
        print("確認場所：")
        print(f"・{IMPORT_DIR}")
        print(f"・{HISTORY_DIR}")

        return

    print(f"使用するCSV：{csv_path}")

    csv_rows = read_csv(csv_path)

    print(
        f"CSV登録件数："
        f"{len(csv_rows)}件"
    )

    # ------------------------------
    # CSV内のID重複を確認
    # ------------------------------

    casican_ids = [
        normalize_text(row.get("id"))
        for row in csv_rows
    ]

    empty_ids = [
        casican_id
        for casican_id in casican_ids
        if casican_id == ""
    ]

    duplicated_ids = [
        casican_id
        for casican_id, count
        in Counter(casican_ids).items()
        if casican_id != "" and count > 1
    ]

    if empty_ids:

        print()
        print(
            "エラー：idが空欄の行があります。"
        )

        return

    if duplicated_ids:

        print()
        print(
            "エラー：CSV内でidが"
            "重複しています。"
        )

        for casican_id in duplicated_ids:
            print(f"・{casican_id}")

        return

    # ------------------------------
    # DB接続
    # ------------------------------

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    books = conn.execute(
        """
        SELECT
            book_id,
            title,
            author,
            casican_id
        FROM books
        ORDER BY book_id
        """
    ).fetchall()

    print(
        f"SQLite書籍件数："
        f"{len(books)}件"
    )

    # タイトル別に既存書籍を整理
    books_by_title = {}

    for book in books:

        normalized_title = normalize_text(
            book["title"]
        )

        books_by_title.setdefault(
            normalized_title,
            []
        ).append(book)

    matched_data = []
    unmatched_rows = []
    ambiguous_rows = []

    # ------------------------------
    # CSVとDBを照合
    # ------------------------------

    for row in csv_rows:

        title = normalize_text(
            row.get("title")
        )

        author = normalize_text(
            row.get("authors_list")
        )

        candidates = books_by_title.get(
            title,
            []
        )

        # タイトルで1件だけ見つかった場合
        if len(candidates) == 1:

            book = candidates[0]

            matched_data.append(
                (book, row)
            )

            continue

        # 同じタイトルが複数ある場合は
        # 著者も使って照合
        if len(candidates) > 1:

            author_matches = [
                book
                for book in candidates
                if normalize_text(
                    book["author"]
                ) == author
            ]

            if len(author_matches) == 1:

                matched_data.append(
                    (author_matches[0], row)
                )

            else:

                ambiguous_rows.append(
                    {
                        "title": title,
                        "author": author
                    }
                )

            continue

        unmatched_rows.append(
            {
                "title": title,
                "author": author
            }
        )

    # ------------------------------
    # 照合結果を表示
    # ------------------------------

    print()
    print("=" * 60)
    print("照合結果")
    print("=" * 60)

    print(
        f"一致：{len(matched_data)}件"
    )

    print(
        f"不一致：{len(unmatched_rows)}件"
    )

    print(
        f"候補重複：{len(ambiguous_rows)}件"
    )

    if unmatched_rows:

        print()
        print("一致しなかった書籍：")

        for row in unmatched_rows:

            print(
                f"・{row['title']}"
                f"／{row['author']}"
            )

    if ambiguous_rows:

        print()
        print(
            "同名書籍が複数あり、"
            "特定できなかった書籍："
        )

        for row in ambiguous_rows:

            print(
                f"・{row['title']}"
                f"／{row['author']}"
            )

    # 1件でも判定できない場合は更新しない
    if unmatched_rows or ambiguous_rows:

        print()
        print(
            "安全のためDBは更新していません。"
        )

        conn.close()

        return

    # CSV件数と一致件数が異なる場合も中止
    if len(matched_data) != len(csv_rows):

        print()
        print(
            "安全のためDBは更新していません。"
        )

        conn.close()

        return

    # ------------------------------
    # DBを更新
    # ------------------------------

    try:

        conn.execute("BEGIN")

        for book, row in matched_data:

            conn.execute(
                """
                UPDATE books
                SET
                    casican_id = ?,
                    quantity = ?,
                    is_hidden = ?,
                    casican_url = ?,
                    casican_qr_url = ?,
                    casican_created_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE book_id = ?
                """,
                (
                    normalize_text(
                        row.get("id")
                    ),

                    convert_integer(
                        row.get("quantity"),
                        default=1
                    ),

                    convert_boolean(
                        row.get("is_hidden")
                    ),

                    normalize_text(
                        row.get("url")
                    ),

                    normalize_text(
                        row.get("qr_url")
                    ),

                    normalize_text(
                        row.get("created_at")
                    ),

                    book["book_id"],
                )
            )

        conn.commit()

    except Exception as error:

        conn.rollback()

        print()
        print("更新に失敗しました。")
        print(error)

        conn.close()

        return

    # ------------------------------
    # 更新後の確認
    # ------------------------------

    linked_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM books
        WHERE casican_id IS NOT NULL
          AND casican_id != ''
        """
    ).fetchone()[0]

    duplicate_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT casican_id
            FROM books
            WHERE casican_id IS NOT NULL
              AND casican_id != ''
            GROUP BY casican_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    conn.close()

    print()
    print("=" * 60)
    print("紐づけ完了")
    print("=" * 60)

    print(
        f"今回更新："
        f"{len(matched_data)}件"
    )

    print(
        f"カシカンID設定済み："
        f"{linked_count}件"
    )

    print(
        f"カシカンID重複："
        f"{duplicate_count}件"
    )


# ========================================
# このファイルを直接実行した場合
# ========================================

if __name__ == "__main__":

    link_casican_data()