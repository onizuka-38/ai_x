import pandas as pd
import io
import sys

# Set stdout to utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

file_path = r'C:\ai_x\source\JikFam\data\배추_이상치제거_주간기준_등급코드.csv'
df = pd.read_csv(file_path, encoding='cp949')

print("--- 기초 통계량 ---")
print(df.describe())
print("\n--- 데이터 정보 ---")
# df.info() prints to stdout, so we capture it
string_buffer = io.StringIO()
df.info(buf=string_buffer)
print(string_buffer.getvalue())