from flask import Flask, render_template

app = Flask(__name__)

# "/"にアクセスされたらindex()を呼び出す
@app.route("/")
def index():

    # index.htmlをレンダリングする
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)