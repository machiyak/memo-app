from flask import Flask, render_template, request

app = Flask(__name__)

# /というURLでGET, POSTの両方を受け付ける
@app.route("/", methods=["GET", "POST"])
def index():
    content = None

    if request.method == "POST":
        # フォームの中身受け取る
        content = request.form["content"]

    # index.htmlをレンダリングする
    return render_template("index.html", content=content)

if __name__ == "__main__":
    app.run(debug=True)