import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_csv('../data/포테이토.csv', encoding='cp949')

df_grow = pd.read_csv('../data/factor_external_weekly_ver_0721.csv', encoding='utf-8')

def format_week_int(weekno):
    year = weekno // 100
    week = weekno % 100
    return year, week

# 적용
df_grow[['year', 'week']] = df_grow['weekno'].apply(
    lambda x: pd.Series(format_week_int(x))
)
df_grow.drop(columns='weekno', inplace=True)
             
# 외생변수 재편집
# 품목코드로 매칭필요
df['item_code']= 501
# 기존데이터 삭제 있으면
# df_agg.drop(columns=['holiday_flag', 'holiday_score', 'grow_score'], inplace=True)
# 병합하기
df  = pd.merge( df,
                    df_grow[['year', 'week', 'item_code', 'holiday_flag', 'holiday_score', 'grow_score']],
                    left_on=['year', 'week', 'item_code'],
                    right_on=['year', 'week', 'item_code'],
                    how='left'
                )
# item_code 삭제
df.drop(columns='item_code', inplace=True)
df.head()



# 등급코드 제거
df = df.drop(columns=['등급코드'], errors='ignore')

# y, X 분리
y = df['평균단가(원)']
X = df.drop(columns=['평균단가(원)'])

# 날짜 처리
X['week_start'] = pd.to_datetime(X['week_start'])
X['year'] = X['week_start'].dt.year

# 학습용: 2024년까지
X_train = X[X['year'] < 2025].drop(columns=['week_start'])
y_train = y[X['year'] < 2025]

# 예측용: 2025년
X_test = X[X['year'] == 2025].drop(columns=['week_start'])
y_test = y[X['year'] == 2025]

print(f"학습 데이터 크기: {X_train.shape}")
print(f"예측 데이터 크기: {X_test.shape}")

import category_encoders as ce

# 타겟 인코딩 적용
encoder = ce.TargetEncoder(cols=['직팜산지코드', '품종코드'])  # 필요한 범주형만 선택
X_train = encoder.fit_transform(X_train, y_train)
X_test = encoder.transform(X_test)

# 이동평균 feature 자동 생성 함수
def generate_moving_averages(df, target_col='평균단가(원)', group_cols=['직팜산지코드', '품종코드'], windows=[4, 13, 26]):
    df = df.sort_values(group_cols + ['year', 'week']).copy()

    for w in windows:
        # 단순이동평균 (SMA)
        df[f'SMA_{w}'] = df.groupby(group_cols)[target_col] \
                           .transform(lambda x: x.rolling(window=w, min_periods=1).mean())

        # 지수이동평균 (EMA)
        df[f'EMA_{w}'] = df.groupby(group_cols)[target_col] \
                           .transform(lambda x: x.ewm(span=w, adjust=False).mean())

    # 📌 파생변수 예시: EMA 차이 및 증가율
    df['EMA4_SMA4_diff'] = df['EMA_4'] - df['SMA_4']
    df['EMA13_SMA13_diff'] = df['EMA_13'] - df['SMA_13']
    df['EMA26_SMA26_diff'] = df['EMA_26'] - df['SMA_26']

    df['EMA_4_rate'] = df.groupby(group_cols)['EMA_4'].transform(lambda x: x.pct_change().fillna(0))
    df['EMA_13_rate'] = df.groupby(group_cols)['EMA_13'].transform(lambda x: x.pct_change().fillna(0))
    df['EMA_26_rate'] = df.groupby(group_cols)['EMA_26'].transform(lambda x: x.pct_change().fillna(0))

    return df

df = generate_moving_averages(df)

moving_avg_cols = [
    'SMA_4', 'SMA_13', 'SMA_26',
    'EMA_4', 'EMA_13', 'EMA_26',
    'EMA4_SMA4_diff', 'EMA13_SMA13_diff', 'EMA26_SMA26_diff',
    'EMA_4_rate', 'EMA_13_rate', 'EMA_26_rate'
]

print(df[moving_avg_cols].isnull().sum())

# 결측치 제거 (또는 forward fill 등 선택)
df = df.dropna(subset=moving_avg_cols).copy()

from sklearn.preprocessing import RobustScaler

scaler = RobustScaler()
X_scaled = scaler.fit_transform(df[moving_avg_cols])
# 스케일된 배열을 DataFrame으로 다시 변환
df_scaled = pd.DataFrame(X_scaled, columns=moving_avg_cols, index=df.index)

# 원본 df에 덮어쓰거나 합치고 싶다면:
df.update(df_scaled)  # 원래 컬럼 덮어쓰기

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score

# 등급코드 제거
df = df.drop(columns=['등급코드'], errors='ignore')

# y, X 분리
y = df['평균단가(원)']
X = df.drop(columns=['평균단가(원)'])

X['week_start'] = pd.to_datetime(X['week_start'])
X['year'] = X['week_start'].dt.year
X['week'] = X['week_start'].dt.isocalendar().week.astype(int)

# 주기형 특성 생성
X['week_sin'] = np.sin(2 * np.pi * X['week'] / 52)
X['week_cos'] = np.cos(2 * np.pi * X['week'] / 52)
X = X.drop(columns=['week'])  # 기존 week는 제거

# 최신 연도 자동 분리
latest_year = X['year'].max()
print(f" 예측 연도: {latest_year}")

# 학습용: 2024년까지
X_train = X[X['year'] < 2025].drop(columns=['week_start'])
y_train = y[X['year'] < 2025]

# 예측용: 2025년
X_test = X[X['year'] == 2025].drop(columns=['week_start'])
y_test = y[X['year'] == 2025]


print(f" 학습 데이터: {X_train.shape}, 예측 데이터: {X_test.shape}")

# 실무기준 정밀 하이퍼파라미터 설정
param_distributions = {
    'n_estimators': [500, 800, 1200, 1600],
    'max_depth': [15, 20, 25, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 3, 5],
    'max_features': ['sqrt', 0.2, 0.3],
    'min_impurity_decrease': [0.0, 0.0005, 0.001],
    'bootstrap': [True]
}

# 반복 학습 조건
TARGET_RMSE = 300
MAX_TRIALS = 5

trial = 0
best_score = float('inf')
best_r2 = -1
best_model = None

# 랜덤서치 기반 모델 학습 1회 실행
search = RandomizedSearchCV(
    estimator=RandomForestRegressor(random_state=42, n_jobs=-1),
    param_distributions=param_distributions,
    n_iter=20,
    scoring='neg_root_mean_squared_error',
    cv=3,
    verbose=1,
    random_state=42,
    n_jobs=-1
)

search.fit(X_train, y_train)
model = search.best_estimator_
pred = model.predict(X_test)

# 평가 지표 계산
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

# 출력
print("\n🏁 모델 성능 (1회 실행):")
print(f"📉 RMSE: {rmse:.2f}")
print(f"📈 R² : {r2:.4f}")


