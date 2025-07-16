
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 한글 폰트 설정 (Windows 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 파일 경로
file_path = 'C:\\ai_x\\source\\JikFam\\data\\배추_이상치제거_주간기준_등급코드.csv'

# 결과 저장 디렉토리
output_dir = 'C:\\ai_x\\source\\JikFam\\eda_results'
os.makedirs(output_dir, exist_ok=True)

# 데이터 불러오기
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"오류: 파일 '{file_path}'을(를) 찾을 수 없습니다.")
    exit()


# --- 1. 기초 통계 분석 ---
print("--- 기초 통계량 ---")
print(df.describe())
print("\n--- 데이터 정보 ---")
df.info()
print("\n")

# 날짜 데이터를 datetime 형식으로 변환
# '연도'와 '주' 컬럼이 있다고 가정하고 '날짜' 컬럼 생성
if '연도' in df.columns and '주' in df.columns:
    df['날짜'] = pd.to_datetime(df['연도'].astype(str) + df['주'].astype(str).str.zfill(2) + '1', format='%Y%W%w')
    date_col = '날짜'
elif 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])
    date_col = 'date'
else:
    # 날짜로 추정되는 첫 번째 열을 사용
    date_col = df.columns[0]
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except (ValueError, TypeError):
        print(f"'{date_col}' 열을 날짜 형식으로 변환할 수 없습니다. 시계열 그래프를 생성하지 않습니다.")
        date_col = None


# 가격 컬럼 확인 (예: '가격', 'price' 등)
price_col = None
for col in ['가격', 'price', 'avg_price', '평균가격']:
    if col in df.columns:
        price_col = col
        break

if price_col is None:
    # 숫자형 데이터 중 마지막 컬럼을 가격으로 추정
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        price_col = numeric_cols[-1]
        print(f"가격 컬럼을 찾지 못해 숫자형 마지막 컬럼인 '{price_col}'을 가격으로 간주합니다.")
    else:
        print("가격으로 추정할 숫자형 컬럼이 없습니다. 일부 시각화가 제한될 수 있습니다.")


# --- 2. 시각화 ---

# 시계열 그래프 (날짜와 가격 컬럼이 있을 경우)
if date_col and price_col:
    plt.figure(figsize=(15, 7))
    sns.lineplot(data=df, x=date_col, y=price_col)
    plt.title('시간에 따른 가격 변동')
    plt.xlabel('날짜')
    plt.ylabel('가격')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, 'price_timeseries.png'))
    plt.close()
    print("'price_timeseries.png' 저장 완료")

# 가격 분포 (히스토그램 및 박스 플롯)
if price_col:
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    sns.histplot(df[price_col], kde=True)
    plt.title('가격 분포 (히스토그램)')

    plt.subplot(1, 2, 2)
    sns.boxplot(y=df[price_col])
    plt.title('가격 분포 (박스 플롯)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'price_distribution.png'))
    plt.close()
    print("'price_distribution.png' 저장 완료")

# 페어 플롯 (숫자형 변수 간 관계)
numeric_df = df.select_dtypes(include=['number'])
if not numeric_df.empty:
    plt.figure(figsize=(15, 15))
    sns.pairplot(numeric_df.head(1000)) # 데이터가 많을 경우를 대비해 일부만 사용
    plt.suptitle('숫자형 변수 간 산점도 행렬', y=1.02)
    plt.savefig(os.path.join(output_dir, 'pairplot.png'))
    plt.close()
    print("'pairplot.png' 저장 완료")


# --- 3. 상관 관계 분석 ---
if not numeric_df.empty:
    plt.figure(figsize=(12, 10))
    corr_matrix = numeric_df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5)
    plt.title('숫자형 변수 간 상관관계 히트맵')
    plt.savefig(os.path.join(output_dir, 'correlation_heatmap.png'))
    plt.close()
    print("'correlation_heatmap.png' 저장 완료")

print(f"\nEDA 결과가 '{output_dir}' 폴더에 저장되었습니다.")
