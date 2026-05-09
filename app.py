from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

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
    # ユーザー名とパスワードが入力されて登録ボタンが押されたらブラウザ上でで表示する
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        return f"username={username}, password={password}"
    
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)