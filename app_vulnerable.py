import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"

DB_NAME = "memo.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()

    if request.method == "POST":
        content = request.form["content"]
        conn.execute(
            "INSERT INTO memos (user_id, content) VALUES (?, ?)",
            (session["user_id"], content)
        )
        conn.commit()
        conn.close()
        # フォーム再送信を防ぐために"/"にリダイレクト
        return redirect(url_for("index"))

    # ログイン中のユーザーのメモのみ表示する
    memos = conn.execute(
        "SELECT * FROM  memos WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("index.html", memos=memos)

@app.route("/delete/<int:memo_id>", methods=["POST"])
def delete_memo(memo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()

    conn.execute(
        # 他人のidを指定してもuser_idが一致しなければ削除されない
        "DELETE FROM memos WHERE id = ? AND user_id = ?",
        (memo_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))

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
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        # SQL Injectionが起こる
        query = f"""
        SELECT * FROM users
        WHERE username = '{username}'
        AND password_hash = '{password}'
        """
        user = conn.execute(query).fetchone

        conn.close()

        if user is None:
            return "ユーザーが存在しません"
        
        # passwordをhash化してpassword hashと一致するかをチェックする
        if not check_password_hash(user["password_hash"], password):
            return "パスワードが違います"
        
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect(url_for("index"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)