from flask import Flask
from flask import render_template
from flask import request
from flask import abort
from models import Member
from filters import mask_password

app = Flask(__name__)
app.template_filter("mask_pw")(mask_password) # filter 

@app.errorhandler(404) # 예외 페이지 처리
def errorhandler(error):
  return render_template("404_pageNotFound.html"), 404

@app.route("/", methods=["GET"])
def index():
  return render_template("2_postetc/index.html") 

@app.route("/join", methods=["GET", "POST"]) 
def join():
  if request.method == "GET":
    return render_template("2_postetc/join.html") 
  elif request.method == "POST":
    #name = request.form.get('name')
    #id   = request.form.get('id') # id 파라미터를 type="number"보내옴
    #print(type(id)) # <class 'str'>
    #pw   = request.form.get('pw')
    #addr = request.form.get('addr')
    # print(request.form.to_dict()) # {'name': 'hong', 'id': '123', 'pw': '1234', 'addr': 'seoul'}
    member = Member(**request.form.to_dict()) # 파라미터를 dict로 변환  
    #print(type(member.id))
    return render_template("2_postetc/result.html", member=member)
  
@app.route("/update/<name>/<id>/<pw>/<addr>", methods=["PATCH"])
def update(name, id, pw, addr):
  return f"{name}님 정보가 수정되었습니다"

@app.route("/delete/<id>", methods=["DELETE"])
def delete(id):
  # delete from 테이블명 where id = id 를 DBMS에 전송하기
  return f"{id}님 정보가 삭제되었습니다"