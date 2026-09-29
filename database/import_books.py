import csv
import shutil
import sqlite3
from collections import Counter
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

DB_PATH = (
    BASE_DIR
    / "database"
    / "library.db"
)


# ========================================
# 値の変換
# ========================================

def normalize_text(value):

    if value is None:
        return ""

    return str(value).strip()


def empty_to_none(value):

    normalized_value = normalize_text(value)

    if normalized_value == "":
        return None

    return normalized_value


def convert_boolean(value):

    normalized_value = normalize_text(
        value
    ).upper()

    if normalized_value == "TRUE":
        return 1

    return 0


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
# 履歴ファイル名を作成
# ========================================

def create_history_path():

    today = datetime.now().strftime(
        "%Y%m%d"
    )

    HISTORY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    number = 1

    while True:

        filename = (
            f"{today}_{number:02d}.csv"
        )

        history_path = (
            HISTORY_DIR / filename
        )

        if not history_path.exists():
            return history_path

        number += 1


# ========================================
# CSVの必須項目を確認
# ========================================

def validate_csv(rows, fieldnames):

    required_columns = {
        "id",
        "title",
        "authors_list",
    }

    current_columns = set(
        fieldnames or []
    )

    missing_columns = (
        required_columns
        - current_columns
    )

    if missing_columns:

        missing_text = ", ".join(
            sorted(missing_columns)
        )

        raise ValueError(
            "CSVに必須列がありません："
            f"{missing_text}"
        )

    if not rows:

        raise ValueError(
            "CSVに書籍データがありません。"
        )

    casican_ids = [
        normalize_text(row.get("id"))
        for row in rows
    ]

    if any(
        casican_id == ""
        for casican_id in casican_ids
    ):

        raise ValueError(
            "カシカンIDが空欄の行があります。"
        )

    duplicated_ids = [
        casican_id
        for casican_id, count
        in Counter(casican_ids).items()
        if count > 1
    ]

    if duplicated_ids:

        duplicated_text = ", ".join(
            duplicated_ids
        )

        raise ValueError(
            "CSV内でカシカンIDが"
            "重複しています："
            f"{duplicated_text}"
        )


# ========================================
# CSVを読み込む
# ========================================

def read_csv(csv_path):

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        rows = list(reader)

        validate_csv(
            rows,
            reader.fieldnames
        )

        return rows


# ========================================
# 1件のCSVをインポート
# ========================================

def import_one_csv(csv_path):

    print()
    print("=" * 60)
    print(f"処理開始：{csv_path.name}")
    print("=" * 60)

    rows = read_csv(csv_path)

    print(f"CSV件数：{len(rows)}件")

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    inserted_count = 0
    updated_count = 0

    try:

        conn.execute("BEGIN")

        for row in rows:

            casican_id = normalize_text(
                row.get("id")
            )

            existing_book = conn.execute(
                """
                SELECT book_id
                FROM books
                WHERE casican_id = ?
                """,
                (casican_id,)
            ).fetchone()

            if existing_book is None:

                # ----------------------
                # 新規書籍
                # ----------------------

                conn.execute(
                    """
                    INSERT INTO books (
                        casican_id,
                        title,
                        description,
                        author,
                        publisher,
                        genre,
                        isbn,
                        release_date,
                        location,
                        quantity,
                        is_hidden,
                        casican_url,
                        casican_qr_url,
                        casican_created_at,
                        updated_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, CURRENT_TIMESTAMP
                    )
                    """,
                    (
                        casican_id,

                        normalize_text(
                            row.get("title")
                        ),

                        empty_to_none(
                            row.get("description")
                        ),

                        empty_to_none(
                            row.get("authors_list")
                        ),

                        empty_to_none(
                            row.get("publisher")
                        ),

                        empty_to_none(
                            row.get("category")
                        ),

                        empty_to_none(
                            row.get("isbn")
                        ),

                        empty_to_none(
                            row.get("release_date")
                        ),

                        empty_to_none(
                            row.get("location")
                        ),

                        convert_integer(
                            row.get("quantity"),
                            default=1
                        ),

                        convert_boolean(
                            row.get("is_hidden")
                        ),

                        empty_to_none(
                            row.get("url")
                        ),

                        empty_to_none(
                            row.get("qr_url")
                        ),

                        empty_to_none(
                            row.get("created_at")
                        ),
                    )
                )

                inserted_count += 1

            else:

                # ----------------------
                # 既存書籍
                # ----------------------
                #
                # cover_image
                # media_type
                # tags
                # is_available
                # is_owner_pick
                # is_featured
                # created_at
                #
                # 上記は更新しない
                # ----------------------

                conn.execute(
                    """
                    UPDATE books
                    SET
                        title = ?,

                        description =
                            COALESCE(
                                ?,
                                description
                            ),

                        author =
                            COALESCE(
                                ?,
                                author
                            ),

                        publisher =
                            COALESCE(
                                ?,
                                publisher
                            ),

                        genre =
                            COALESCE(
                                ?,
                                genre
                            ),

                        isbn =
                            COALESCE(
                                ?,
                                isbn
                            ),

                        release_date =
                            COALESCE(
                                ?,
                                release_date
                            ),

                        location =
                            COALESCE(
                                ?,
                                location
                            ),

                        quantity = ?,
                        is_hidden = ?,

                        casican_url =
                            COALESCE(
                                ?,
                                casican_url
                            ),

                        casican_qr_url =
                            COALESCE(
                                ?,
                                casican_qr_url
                            ),

                        casican_created_at =
                            COALESCE(
                                ?,
                                casican_created_at
                            ),

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE casican_id = ?
                    """,
                    (
                        normalize_text(
                            row.get("title")
                        ),

                        empty_to_none(
                            row.get("description")
                        ),

                        empty_to_none(
                            row.get("authors_list")
                        ),

                        empty_to_none(
                            row.get("publisher")
                        ),

                        empty_to_none(
                            row.get("category")
                        ),

                        empty_to_none(
                            row.get("isbn")
                        ),

                        empty_to_none(
                            row.get("release_date")
                        ),

                        empty_to_none(
                            row.get("location")
                        ),

                        convert_integer(
                            row.get("quantity"),
                            default=1
                        ),

                        convert_boolean(
                            row.get("is_hidden")
                        ),

                        empty_to_none(
                            row.get("url")
                        ),

                        empty_to_none(
                            row.get("qr_url")
                        ),

                        empty_to_none(
                            row.get("created_at")
                        ),

                        casican_id,
                    )
                )

                updated_count += 1

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()

    # DB更新成功後に履歴保存
    history_path = create_history_path()

    shutil.move(
        str(csv_path),
        str(history_path)
    )

    print()
    print("インポート成功")
    print(f"新規登録：{inserted_count}件")
    print(f"既存更新：{updated_count}件")

    print(
        f"処理合計："
        f"{inserted_count + updated_count}件"
    )

    print(
        f"履歴保存："
        f"{history_path.name}"
    )

    return {
        "inserted": inserted_count,
        "updated": updated_count,
        "history": history_path.name,
    }


# ========================================
# import内の全CSVを処理
# ========================================

def import_all_csv_files():

    print("=" * 60)
    print("カシカンCSV一括インポート")
    print("=" * 60)

    print(f"DB：{DB_PATH}")
    print(f"取込元：{IMPORT_DIR}")
    print(f"履歴先：{HISTORY_DIR}")

    IMPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    HISTORY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    csv_files = sorted(
        IMPORT_DIR.glob("*.csv")
    )

    if not csv_files:

        print()
        print(
            "インポート対象のCSVは"
            "ありません。"
        )

        return

    print()
    print(
        f"対象CSV：{len(csv_files)}件"
    )

    total_inserted = 0
    total_updated = 0
    success_count = 0
    failed_count = 0

    for csv_path in csv_files:

        try:

            result = import_one_csv(
                csv_path
            )

            total_inserted += (
                result["inserted"]
            )

            total_updated += (
                result["updated"]
            )

            success_count += 1

        except Exception as error:

            failed_count += 1

            print()
            print(
                f"処理失敗：{csv_path.name}"
            )

            print(error)

            print(
                "このCSVはimportフォルダに"
                "残しています。"
            )

    print()
    print("=" * 60)
    print("一括インポート完了")
    print("=" * 60)

    print(
        f"成功CSV：{success_count}件"
    )

    print(
        f"失敗CSV：{failed_count}件"
    )

    print(
        f"新規登録合計："
        f"{total_inserted}件"
    )

    print(
        f"既存更新合計："
        f"{total_updated}件"
    )


# ========================================
# このファイルを直接実行した場合
# ========================================

if __name__ == "__main__":

    import_all_csv_files()