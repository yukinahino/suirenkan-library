import sqlite3
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, session, request, redirect, url_for


app = Flask(__name__)

# セッションを使用するための秘密鍵
app.secret_key = "suirenkan-library-secret-key"


# ========================================
# データベース設定
# ========================================

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "database" / "library.db"

print("DB_PATH:", DB_PATH)


def get_db_connection():
    """SQLiteデータベースに接続する"""

    conn = sqlite3.connect(DB_PATH)

    # SELECTしたデータを列名で取得できるようにする
    conn.row_factory = sqlite3.Row

    return conn

# ========================================
# 共通のセッション管理／未ログインの場合はログイン画面へ
# ========================================
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        # 未ログインならログイン画面へ
        if "user_id" not in session:
            return redirect(url_for("login"))

        # ログイン済みなら本来の処理を実行
        return view(*args, **kwargs)

    return wrapped_view

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        # 未ログインならログイン画面へ
        if "user_id" not in session:
            return redirect(url_for("login"))

        # 管理者でなければホームへ
        if session.get("role") != "admin":
            return redirect(url_for("index"))

        # 管理者なら本来の処理を実行
        return view(*args, **kwargs)

    return wrapped_view

# ========================================
# 画面ルーティング
# ========================================

@app.route("/")
@login_required
def index():

    conn = get_db_connection()

    # MVに指定された本を1冊取得
    featured_book = conn.execute(
        """
        SELECT *
        FROM books
        WHERE is_featured = 1
          AND is_hidden = 0
        ORDER BY book_id
        LIMIT 1
        """
    ).fetchone()

    # MV指定本がない場合は、最新の本を代わりに表示
    if featured_book is None:
        featured_book = conn.execute(
            """
            SELECT *
            FROM books
            WHERE is_hidden = 0
            ORDER BY book_id DESC
            LIMIT 1
            """
        ).fetchone()

    # 新着書籍
    new_books = conn.execute(
        """
        SELECT *
        FROM books
        WHERE is_hidden = 0
        ORDER BY book_id DESC
        LIMIT 12
        """
    ).fetchall()

    # 管理人オススメ
    owner_picks = conn.execute(
        """
        SELECT *
        FROM books
        WHERE is_owner_pick = 1
          AND is_hidden = 0
        ORDER BY book_id
        """
    ).fetchall()

    # タグ名から書籍を取得する処理
    def get_books_by_tag(tag_name):

        return conn.execute(
            """
            SELECT DISTINCT books.*
            FROM books
            INNER JOIN book_tags
                ON books.book_id = book_tags.book_id
            INNER JOIN tags
                ON book_tags.tag_id = tags.tag_id
            WHERE tags.tag_name = ?
              AND books.is_hidden = 0
            ORDER BY books.book_id
            """,
            (tag_name,)
        ).fetchall()

    # ホームに表示する気分タグ
    mood_sections = [
        {
            "title": "🌿 #心を整える 本",
            "books": get_books_by_tag("心を整える")
        },
        {
            "title": "☕ #週末にじっくり 読みたい本",
            "books": get_books_by_tag("週末にじっくり")
        },
        {
            "title": "💼 #仕事に役立つ 本",
            "books": get_books_by_tag("仕事に役立つ")
        }
    ]

    conn.close()

    return render_template(
        "index.html",
        featured_book=featured_book,
        new_books=new_books,
        owner_picks=owner_picks,
        mood_sections=mood_sections
    )

@app.route("/book/<int:book_id>")
@login_required
def book_detail(book_id):

    conn = get_db_connection()

    # 本の基本情報を取得
    book = conn.execute(
        "SELECT * FROM books WHERE book_id = ?",
        (book_id,)
    ).fetchone()

    # 本に登録されているタグを取得
    book_tags = conn.execute(
        """
        SELECT tags.tag_name
        FROM tags
        INNER JOIN book_tags
            ON tags.tag_id = book_tags.tag_id
        WHERE book_tags.book_id = ?
        ORDER BY tags.tag_id
        """,
        (book_id,)
    ).fetchall()

    conn.close()

    if book is None:
        return "本が見つかりませんでした。", 404

    return render_template(
        "book_detail.html",
        book=book,
        book_tags=book_tags
    )


@app.route("/search")
@login_required
def search():

    # URLから検索条件を取得
    keyword = request.args.get("keyword", "").strip()
    tag = request.args.get("tag", "").strip()
    category = request.args.get("category", "").strip()

    books = []

    conn = get_db_connection()

    # ------------------------------
    # タグ検索
    # ------------------------------
    if tag:

        books = conn.execute(
            """
            SELECT DISTINCT books.*
            FROM books
            INNER JOIN book_tags
                ON books.book_id = book_tags.book_id
            INNER JOIN tags
                ON book_tags.tag_id = tags.tag_id
            WHERE tags.tag_name = ?
            AND books.is_hidden = 0
            ORDER BY books.book_id
            """,
            (tag,)
        ).fetchall()

    # ------------------------------
    # カテゴリ検索
    # ------------------------------
    elif category:

        books = conn.execute(
            """
            SELECT *
            FROM books
            WHERE media_type = ?
            AND is_hidden = 0
            ORDER BY book_id
            """,
            (category,)
        ).fetchall()

    # ------------------------------
    # キーワード検索
    # ------------------------------
    elif keyword:

        search_word = f"%{keyword}%"

        books = conn.execute(
            """
            SELECT DISTINCT books.*
            FROM books
            LEFT JOIN book_tags
                ON books.book_id = book_tags.book_id
            LEFT JOIN tags
                ON book_tags.tag_id = tags.tag_id
            WHERE books.is_hidden = 0
              AND (
                  books.title LIKE ?
                  OR books.author LIKE ?
                  OR books.description LIKE ?
                  OR books.publisher LIKE ?
                  OR books.genre LIKE ?
                  OR tags.tag_name LIKE ?
              )
            ORDER BY books.book_id
            """,
            (
                search_word,
                search_word,
                search_word,
                search_word,
                search_word,
                search_word
            )
        ).fetchall()

    conn.close()

    return render_template(
    "search.html",
    books=books,
    keyword=keyword,
    tag=tag,
    category=category
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    # ログインフォームが送信された場合
    if request.method == "POST":

        user_id = request.form.get("user_id")
        password = request.form.get("password")

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT * FROM users
            WHERE user_id = ? AND password = ?
            """,
            (user_id, password)
        ).fetchone()

        conn.close()

        # ユーザーが見つかった場合
        if user:

            # セッションにユーザー情報を保存
            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            # 管理者の場合
            if user["role"] == "admin":
                return redirect(url_for("admin"))

            # 一般ユーザーの場合
            return redirect(url_for("index"))

        # 認証失敗
        return render_template(
            "login.html",
            error="ユーザーIDまたはパスワードが違います。"
        )

    # GETの場合は普通にログイン画面を表示
    return render_template("login.html")


@app.route("/admin")
@admin_required
def admin():
    
    return render_template("admin.html")


@app.route("/mypage")
@login_required
def mypage():

    return render_template("mypage.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
