import sqlite3

DB_NAME = "memo.db"

conn = sqlite3.connect(DB_NAME)
# DB操作用カーソル
cur = conn.cursor()

# メモを記録するためのmemosテーブルを作成し、メモのid, メモの内容, メモ作成日時の3つの列を作成
cur.execute("""
CREATE TABLE IF NOT EXISTS memos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL            
)
""")

conn.commit()
conn.close()

print("Database inisialized.")
