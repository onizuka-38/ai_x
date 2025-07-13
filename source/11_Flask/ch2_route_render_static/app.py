# python -m pip install --upgrade pip
# pip install flask
from flask import Flask
app = Flask(__name__) # 웹 인스턴스 생성
@app.route("/") # @ : 데코레이터를 통해 요청가능한 url등록
def handler_viewFunc():
    return "<h1>Hello, World</h1>"

# 파일명이 app.py이면 실행은 flask run (--debug --port=80)
# 파일명이 app.py가 아니면 if 문을 구현하고 python name.py
if __name__=="__main__":
    app.run(port=80, debug=True)