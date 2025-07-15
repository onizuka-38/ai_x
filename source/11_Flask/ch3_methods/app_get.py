# python -m venv .venv (가상환경 생성 방법1)
# ctrl+shift+p => select interpreter => 가상환경만들기 => .venv로 가상환경만들기 
# => 인터프리터경로입력 => 찾기(python.exe) (가상환경 생성 방법2)
# .venv\Scripts\activate (가상환경 들어가기)
# python -m pip install --upgrade pip
# pip install flask
from flask import Flask # 앱 객체
from flask import render_template # html 렌더링
from flask import request # get/post방식으로 파라미터 데이터 받기
from flask import abort # 강제로 예외발생
from models import Member
from filters import mask_password

app = Flask(__name__) # 앱 객체 생성

# 필터링 추가 (str -> str문자갯수만큼 *)
app.template_filter("mask_pw")(mask_password)

# @app.template_filter("mask_pw")
# def mask_password(password):
#   return "*" * len(password)

@app.route("/user/<name>", methods=["GET"]) # /user/hong
def viewFunction_handlerFunction(name):
  return f"<h1>{name}님 환영합니다</h1>"

@app.route("/user") # /user
def user():
  name = request.args.get("name") # get방식 파라미터 값 받기
  if name:
    return f"<h1>전달받은 파라미터 이름 : {name}님</h1>"
  else:
    abort(404)

@app.errorhandler(404) # 404 예외 페이지 처리
def errorhandler(error):
  return render_template("404_pageNotFound.html"), 404

@app.route("/", methods=["GET"])
def index():
  return render_template("index.html")

@app.route("/join_form", methods=["GET"])
def join_form():
  return render_template("1_onlyget/join.html")

@app.route("/join", methods=["GET"])
def join():
  name = request.args.get('name') #get방식
  id   = request.args.get('id')
  pw   = request.args.get('pw')
  addr = request.args.get('addr')
  member = Member(name, id, pw, addr)
  return render_template("result.html", member=member)


if __name__=="__main__":
  app.run(debug=True, port=80)