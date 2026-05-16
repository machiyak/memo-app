# CSRF

## 概要

CSRF が発生する原因と対策を整理する。

CSRFはCross-Site Request Forgeryの略であり、ログイン済みユーザーのブラウザに、本人の意図しないリクエストを送信させる攻撃である。

Webアプリケーションでは、ログイン状態をCookieやセッションによって管理することが多い。ブラウザは対象サイトにリクエストを送る際、そのサイトのCookieを自動的に送信する。そのため、外部サイトから状態変更リクエストを送らされた場合でも、サーバー側から見るとログイン済みユーザー本人の操作に見える可能性がある。

---

## 今回のアプリで問題になる箇所

今回のメモアプリでは、以下のような状態を変更する処理がある。

* メモ投稿
* メモ削除
* ログアウト

これらの処理では、ログイン済みユーザーのセッション情報を利用して処理を行っている。

例えば、メモ削除処理では、ログイン中のユーザーIDを用いて、自分のメモだけを削除できるようにしている。

```python
conn.execute(
    "DELETE FROM memos WHERE id = ? AND user_id = ?",
    (memo_id, session["user_id"])
)
```

この実装では、他人のメモを削除できないようにする所有者チェックは行っている。

しかし、この処理だけでは、リクエストが本当にアプリ内の正規フォームから送信されたものかは確認していない。そのため、CSRFには弱い可能性がある。

---

## CSRFが成立する流れ

CSRFでは、攻撃者はユーザーのパスワードを知っている必要はない。問題になるのは、ユーザーがすでに対象サイトにログインしている状態である。

典型的な流れは次のようになる。

```text
ユーザーがメモアプリにログインしている
↓
ブラウザにはセッションCookieが保存されている
↓
ユーザーが別の悪意あるページを開く
↓
そのページがメモアプリに対してPOSTリクエストを送らせる
↓
ブラウザはメモアプリの Cookie を自動的に送信する
↓
サーバー側ではログイン済みユーザーの操作に見える
```

つまり、CSRFは、ログイン済みユーザーの認証状態を悪用して、本人が意図しない状態変更リクエストを送らせる。

---

## 所有者チェックだけでは不十分な理由

今回の削除処理では、次のように `user_id` を条件に含めている。

```python
conn.execute(
    "DELETE FROM memos WHERE id = ? AND user_id = ?",
    (memo_id, session["user_id"])
)
```

この条件があることで、ログイン中のユーザーは他人のメモを削除できない。
しかし、CSRFは他人の権限ではなく、本人のブラウザに本人の権限で操作させる。

そのため、所有者チェックがあっても、ログイン中の本人のメモを意図せず削除させられる可能性は残る。

---

## 脆弱な実装

CSRF対策がない場合、削除フォームは次のような形になる。

```html
<form method="post" action="/delete/{{ memo['id'] }}">
    <button type="submit">削除</button>
</form>
```

このフォームでは、削除リクエストを送るための特別な確認情報が含まれていない。

また、サーバー側の削除処理も、ログイン済みかどうかと所有者チェックだけで削除を実行している。

```python
@app.route("/delete/<int:memo_id>", methods=["POST"])
def delete_memo(memo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM memos WHERE id = ? AND user_id = ?",
        (memo_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))
```

この実装では、POSTリクエストがアプリ内の正規フォームから送信されたものかどうかを確認していない。

---

## 安全な実装

CSRF対策では、サーバー側でランダムなトークンを生成し、それをセッションに保存する。
そして、フォームにも同じトークンを埋め込む。

POSTリクエストを受け取ったときに、次の2つを比較する。

```text
セッション内のCSRFトークン
フォームから送信されたCSRFトークン
```

この2つが一致した場合だけ、正規フォームから送られたリクエストとみなして処理を続行する。

外部サイトは、同一オリジンポリシーにより、通常は対象サイトのフォーム内に埋め込まれたCSRFトークンやセッション内の値を読み取れない。
そのため、正しいトークンを付けたリクエストを作ることが難しくなる。

---

## CSRFトークンの生成

今回の実装では、`secrets` モジュールを使ってランダムなトークンを生成する。

```python
import secrets
```

```python
def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]
```

この関数では、セッションに `csrf_token` が存在しない場合だけ新しく生成している。
すでに存在する場合は、同じトークンを再利用する。

---

## テンプレートでCSRFトークンを使えるようにする

Flaskの `context_processor` を使うと、テンプレート全体で `csrf_token` を参照できるようになる。

```python
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=get_csrf_token())
```

これにより、HTMLテンプレート側で次のように書ける。

```html
{{ csrf_token }}
```

---

## フォームへのCSRFトークン埋め込み

各フォームでは、hidden inputとして CSRFトークンを埋め込む。

```html
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    ......
</form>
```

これにより、アプリ内の正規フォームから送信されたPOSTリクエストには、セッション内のトークンと対応する値が含まれる。

---

## CSRFトークンの検証

POSTリクエストを処理する前に、フォームから送信されたトークンとセッション内のトークンを比較し、一致しない場合は不正なリクエストとして処理を拒否する。

```python
if not validate_csrf_token():
    return "不正なリクエストです", 400
```

---

## メモ投稿処理での対策

メモ投稿は状態を変更する処理なので、POST時にCSRFトークンを検証する。

```python
if request.method == "POST":
    if not validate_csrf_token():
        conn.close()
        return "不正なリクエストです", 400

    content = request.form["content"]

    conn.execute(
        "INSERT INTO memos (user_id, content) VALUES (?, ?)",
        (session["user_id"], content)
    )
    conn.commit()
```

これにより、CSRFトークンがない、もしくは一致しないリクエストでは、メモ投稿を実行しない。

---

## メモ削除処理での対策

メモ削除でも、削除処理の前にCSRFトークンを検証する。

```python
@app.route("/delete/<int:memo_id>", methods=["POST"])
def delete_memo(memo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if not validate_csrf_token():
        return "不正なリクエストです", 400

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM memos WHERE id = ? AND user_id = ?",
        (memo_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))
```

この処理では、次の2つを確認している。

```text
1. ログイン済みか
2. 正しいCSRFトークンを持つリクエストか
```

その上で、削除対象のメモがログイン中ユーザーのものかをSQL条件で確認している。

---

## ログアウトについて

ログアウトも状態を変更する処理である。

そのため、セキュリティを意識するなら、GETリンクではなくPOSTフォームで実行する方が望ましい。

脆弱になりやすい例は次のようなGETログアウトである。

```python
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
```

より望ましい形は、POSTに限定し、CSRFトークンを検証する実装である。

```python
@app.route("/logout", methods=["POST"])
def logout():
    if not validate_csrf_token():
        return "不正なリクエストです", 400

    session.clear()
    return redirect(url_for("login"))
```

---

## SQL Injection / XSS との違い

SQL Injection、XSS、CSRF はいずれもWebアプリケーションで重要な脆弱性だが、発生する原因は異なる。

| 脆弱性           | 主な原因                       | 影響する場所      |
| ------------- | -------------------------- | ----------- |
| SQL Injection | 入力がSQL文の構造に混入する            | データベース      |
| XSS           | 入力がHTML/JavaScriptとして出力される | ブラウザ        |
| CSRF          | ログイン済みブラウザに意図しないリクエストを送らせる | 認証済みの状態変更処理 |

SQL InjectionとXSSは、ユーザー入力が「命令」や「構造」として解釈されることが問題である。

一方、CSRF では、入力値そのものよりも、リクエストが本人の意図した操作かどうかをサーバーが区別できないことが問題になる。