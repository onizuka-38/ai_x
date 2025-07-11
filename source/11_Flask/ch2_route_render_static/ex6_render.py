from flask import Flask, url_for, render_template
app = Flask(__name__)
@app.route("/")
def hello():
    # templates/06_index.html
    return render_template("06_index.html")

@app.route("/profile/<name>/<int:age>")
def get_profile(name, age):
    return "<h1>profile : {}님 {}살입니다</h1>".format(name, age)

if __name__=="__main__":
    with app.test_request_context():
        print('hello 뷰함수의 요청경로 :', url_for('hello'))
        print(url_for("get_profile", name="hong", age=32))
    app.run(debug=True, port=80)