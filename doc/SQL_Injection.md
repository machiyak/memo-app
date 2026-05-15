# SQL Injection

## 概要

SQL Injection が発生する原因と対策を整理する。

SQL Injection は、ユーザー入力がSQL文の構造の一部として解釈されてしまうことで発生する脆弱性である。
本来、ユーザー入力は値として扱われるべきだが、SQL文字列に直接埋め込むと、入力内容によってSQL文の意味が変わってしまう可能性がある。

---

## 脆弱な実装

脆弱な実装では、ユーザー入力をSQL文に直接埋め込んでいる。

```python
query = f"""
SELECT * FROM users
WHERE username = '{username}'
AND password_hash = '{password}'
"""
user = conn.execute(query).fetchone()
```

この実装では、`username` や `password` の内容が、単なる値ではなくSQL文として解釈される可能性がある。

例えば、ユーザー名として`user' OR '1'='1' --`のような値が入力されるとqueryは

```python
SELECT * FROM users
WHERE username = 'user' OR '1'='1' --'
AND password_hash = 'anything'
```
となるが、このWHEREの条件文は以下のようになる。
```python
username = 'user'
OR '1' = '1' --'
AND password_hash = 'anything'
```
`'1' = '1'`は常に真でその後はコメントアウトされるため、queryは
```python
SELECT * FROM users
WHERE username = 'Suser' OR TRUE
```
となり、この場合はパスワードなしで`user`にログインできてしまう。


---

## 問題点

問題は、ユーザー入力とSQL文の構造が分離されていないことである。

```python
query = f"SELECT * FROM users WHERE username = '{username}'"
```

このような書き方では、`username` が単なる検索値ではなく、SQL文の一部になり得る。

本来は、次の2つを分離して扱う必要がある。

```text
ユーザー入力 = データ
SQL文 = 命令
```


---

## 安全な実装

安全な実装では、ユーザー入力をSQL文に直接埋め込まず、プレースホルダを使っている。

```python
user = conn.execute(
    "SELECT * FROM users WHERE username = ?",
    (username,)
).fetchone()
```

この `?` がプレースホルダである。
値は第2引数で渡す。

```python
(username,)
```

これにより、`username` の内容はSQL文の構造としてではなく、単なる値として扱われる。

