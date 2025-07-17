# step1 
# pip install flask
# jinja2 template include, extends(block)
# 파일업로드(사용자가 업로드한 파일을 서버에 저장) : 업로드 용량 제한
from flask import Flask, render_template, request
#  파일 업로드 처리를 위한 모듈(사용자가 업로드한 파일명에 특수문자를 빼)
from werkzeug.utils import secure_filename
import os
# 업로드 폴더 경로 설정(폴더 없으면 폴더 생성)
UPLOAD_FOLDER = './uploads/'
if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
#print(app.config)
# 업로드 용량 제한 (용량 초과시 403 error)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1 

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
    return render_template('upload.html')
  elif request.method == 'POST':
    # 업로드한 파일을 받아 서버 UPLOAD_FOLDER  폴더에 저장
    file = request.files['file']
    # 파일명에 서버에 영향을 미칠 특수문자 빼서 저장
    safe_filename = secure_filename(file.filename)
    file.save(UPLOAD_FOLDER + safe_filename) # 업로드 폴더에 파일 저장
    return render_template("check.html",
                          upload_filename=file.filename,
                          safe_filename=safe_filename)

if __name__ == '__main__':
  app.run(debug=True)