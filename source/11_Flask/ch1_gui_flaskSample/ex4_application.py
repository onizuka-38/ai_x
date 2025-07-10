# 플라스크를 사용하기 위한 패키지 설치 : pip install flask
# Flask라는 micro framework를 사용하기 위해
from flask import Flask
from predict import loaded_model, predict_apt_price

application = Flask(__name__) # 웹 어플리케이션 객체 생성

@application.route("/")
def handller_function():
    return "<h1>Hello, Flask!</h1>"
# /apt/2005/106/8
@application.route("/apt/<year>/<square>/<floor>")
def aptPredictHandler(year, square, floor):
    answer = predict_apt_price(year, square, floor)
    return "<h1>예측 금액은 {}입니다</h1>".format(answer)

if __name__=="__main__":
    # debug=True : 코드 수정이 될 때마다 서버가 자동 재시작
    application.run(debug=True)