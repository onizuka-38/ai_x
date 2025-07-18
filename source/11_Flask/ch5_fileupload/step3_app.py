# step3 : home.html = 파일첨부화면 + 첨부했던 파일 목록(다운로드 + 삭제)
from flask import Flask, render_template 
from flask_wtf import FlaskForm 
from flask_wtf.file import FileField, FileRequired # 업로드한 파일 객체
from werkzeug.utils import secure_filename # 업로드한 파일명에 특수문자를 빼서 저장
from fileinfo import info # 파일 정보 출력
import os

from flask import send_file # 다운로드 시 필요
from flask import redirect, url_for # 삭제 후 '/'요청경로로 redirect

UPLOAD_FOLDER = './uploads/'

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 5 # 업로드 폴더 용량 제한
app.config['SECRET_KEY'] = "abc" #uuid.uuid4() # CSRF 보호 정책 설정을 하려면 필요

class FileForm(FlaskForm):
  files = FileField(validators=[FileRequired()]) # 업로드한 파일 객체
  
@app.route('/', methods=['GET', 'POST'])
def index():
  form = FileForm()
  if form.validate_on_submit(): # 폼 데이터가 유효한지(POST요청이 유효하게 들어왔는지) 체크
    file = form.files.data # 업로드한 파일 객체
    # 파일명에 서버에 영향을 미칠 특수문자 빼서 저장
    safe_filename = secure_filename(file.filename)
    file.save(UPLOAD_FOLDER + safe_filename) # 업로드 폴더에 파일 저장
    ctime, mtime, atime, size = info(safe_filename) # 파일 정보 출력
    return render_template("check.html",
                          fileinfo = {'ctime':ctime, 
                                      'size':size})

  else: # GET방식이거나 POST요청이 유효하지 않을 경우
    # 업로드 폴더의 파일 정보를 listup
    filelist = os.listdir(UPLOAD_FOLDER) # 해당 폴더의 파일이름 목록
    infos = [] # 파일 정보(파일명, 파일생성시점, 파일최종수정시점, 사이즈) 리스트
    for filename in filelist:
      ctime, mtime, atime, size = info(filename)
      fileinfo = {"name": filename,
                  "ctime":ctime,
                  "mtime":mtime,
                  "size":size}
      infos.append(fileinfo)
    return render_template('home.html', 
                          form=form,
                          infos=infos)

@app.route('/delete/<filename>')
def delete(filename):
  os.remove(UPLOAD_FOLDER + filename) # 파일 삭제
  # return redirect(url_for("index"))
  return redirect("/")

@app.route('/download/<filename>')
def download(filename):
  return send_file(UPLOAD_FOLDER + filename, 
                  as_attachment=True) # 브라우저에서 파일이 열리지 않고 다운로드만 
if __name__ == '__main__':
  app.run(debug=True)