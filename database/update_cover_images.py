import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent

DB_PATH = BASE_DIR / "database" / "library.db"
IMAGE_DIR = BASE_DIR / "static" / "images" / "books"


def update_cover_images():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    books = cursor.execute(
        "SELECT book_id, title FROM books ORDER BY book_id"
    ).fetchall()

    updated_count = 0
    missing_count = 0

    for book_id, title in books:

        image_path = IMAGE_DIR / f"{book_id}.jpg"

        if image_path.exists():

            cover_image = f"images/books/{book_id}.jpg"

            cursor.execute(
                """
                UPDATE books
                SET cover_image = ?
                WHERE book_id = ?
                """,
                (cover_image, book_id)
            )

            print(f"登録：{book_id} | {title}")
            updated_count += 1

        else:

            print(f"画像なし：{book_id} | {title}")
            missing_count += 1

    conn.commit()
    conn.close()

    print("-" * 50)
    print("書影の登録が完了しました。")
    print(f"登録：{updated_count}件")
    print(f"画像なし：{missing_count}件")


if __name__ == "__main__":
    update_cover_images()