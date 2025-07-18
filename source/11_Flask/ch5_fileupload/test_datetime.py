# 유닉스 시간 -> dattime 변환
import datetime
now = datetime.datetime.now().timestamp() # 현재의 유닉스 시간(70.1.1부터 현재까지 초수)
print(now)
# 유닉스 시간 -> dattime 변환
now_datetime = datetime.datetime.fromtimestamp(now)
print(now_datetime)
print(type(now_datetime))
# 유닉스 시간 -> dattime 변환
print(now_datetime.strftime("%Y-%m-%d %H:%M:%S"))