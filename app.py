from flask import Flask, render_template, request

app = Flask(__name__)

# memo記録用list
memos = []

# /というURLでGET, POSTの両方を受け付ける
@app.route("/", methods=["GET", "POST"])
def index():
    content = None

    if request.method == "POST":
        # フォームの中身受け取る
        content = request.form["content"]
        memos.append(content)

    # index.htmlをレンダリングする
    return render_template("index.html", memos=memos)

if __name__ == "__main__":
    app.run(debug=True)