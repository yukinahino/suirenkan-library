import csv
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


# ========================================
# ファイル・フォルダの場所
# ========================================

# プロジェクトのルートフォルダ
BASE_DIR = Path(__file__).parent.parent

# 読み込むCSV
CSV_PATH = BASE_DIR / "data" / "import" / "sample_data.csv"

# CSVの履歴保存先
HISTORY_DIR = BASE_DIR / "data" / "import_history"

# SQLiteデータベース
DB_PATH = BASE_DIR / "database" / "library.db"


# ========================================
# CSV履歴保存
# ========================================

def save_import_history():
    """インポート済みCSVを日付＋連番の名前で履歴保存する"""

    # 今日の日付を YYYYMMDD 形式で取得
    today = datetime.now().strftime("%Y%m%d")

    # 履歴フォルダがなければ作成
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    # 01から順番に、まだ使われていない番号を探す
    number = 1

    while True:
        filename = f"{today}_{number:02d}.csv"
        history_path = HISTORY_DIR / filename

        if not history_path.exists():
            break

        number += 1

    # CSVを履歴フォルダへ移動
    shutil.move(str(CSV_PATH), str(history_path))

    return filename


# ========================================
# CSV → SQLite インポート
# ========================================

def import_books():

    # CSVが存在するか確認
    if not CSV_PATH.exists():
        print("インポートするCSVが見つかりません。")
        print(f"確認場所：{CSV_PATH}")
        return

    # データベースに接続
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 登録件数
    imported_count = 0

    try:
        # CSVを開く
        with open(
            CSV_PATH,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            # 1行ずつbooksテーブルへ登録
            for row in reader:

                cursor.execute(
                    """
                    INSERT INTO books (
                        title,
                        description,
                        author,
                        publisher,
                        genre,
                        isbn,
                        release_date,
                        location
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["title"],
                        row["description"],
                        row["authors_list"],
                        row["publisher"],
                        row["category"],
                        row["isbn"],
                        row["release_date"],
                        row["location"],
                    ),
                )

                imported_count += 1

        # DBへの登録後、CSVを履歴保存
        history_filename = save_import_history()

        # 両方成功したらDBへの変更を確定
        conn.commit()

        print("CSVのインポートが完了しました。")
        print(f"登録件数：{imported_count}件")
        print(f"履歴ファイル：{history_filename}")

    except Exception as error:

        # DBへの変更を取り消す
        conn.rollback()

        print("インポート中にエラーが発生しました。")
        print(error)

    finally:

        # DBとの接続を終了
        conn.close()


# ========================================
# このファイルを直接実行した場合
# ========================================

if __name__ == "__main__":
    import_books()