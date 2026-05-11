import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# 一次的な秘密鍵（本来の開発ではやってはいけない）、環境変数から読み取る
app.secret_key = "dev-secret-key"

# memo用DB
DB_NAME = "memo.db"

# connを取得する
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    # 取得されるDBの型を辞書型にする
    conn.row_factory = sqlite3.Row
    return conn


# /でGET, POSTの両方を受け付ける
@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db_connection()

    if request.method == "POST":
        # フォームの中身受け取る
        content = request.form["content"]
        
        conn.execute(
            "INSERT INTO memos (content) VALUES (?)",
            (content,)
        )
        conn.commit()
        conn.close()
        # フォーム再送信を防ぐために"/"にリダイレクト
        return redirect(url_for("index"))

    memos = conn.execute(
        "SELECT * FROM  memos ORDER BY created_at DESC"
    ).fetchall()

    conn.close()

    # index.htmlをレンダリングする
    return render_template("index.html", memos=memos)

# /registerでregister.htmlをレンダリング
@app.route("/register", methods=["GET", "POST"])
def register():
    # ユーザー名とパスワードが入力されて登録ボタンが押されたらDBに保存する
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "このユーザー名は既に使われています。"

        conn.close()
        # indexに戻る
        return redirect(url_for("index"))
    
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)