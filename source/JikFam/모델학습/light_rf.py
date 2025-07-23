import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import RobustScaler
import category_encoders as ce

# 데이터 불러오기
df = pd.read_csv('../data/포테이토.csv', encoding='cp949')
df_grow = pd.read_csv('../data/factor_external_weekly_ver_0721.csv', encoding='utf-8')

# year, week 파생
def format_week_int(weekno):
    year = weekno // 100
    week = weekno % 100
    return year, week

df_grow[['year', 'week']] = df_grow['weekno'].apply(lambda x: pd.Series(format_week_int(x)))
df_grow.drop(columns='weekno', inplace=True)

# 병합 전 품목코드 추가
df['item_code'] = 501

# 외생변수 병합
df = pd.merge(
    df,
    df_grow[['year', 'week', 'item_code', 'holiday_flag', 'holiday_score', 'grow_score']],
    on=['year', 'week', 'item_code'],
    how='left'
)

# 병합 후 외생변수 컬럼 재정의
for col in ['holiday_flag', 'holiday_score', 'grow_score']:
    if f"{col}_y" in df.columns:
        df[col] = df[f"{col}_y"]
        df.drop(columns=[f"{col}_x", f"{col}_y"], inplace=True)

df.drop(columns='item_code', inplace=True)

# 등급코드 제거
df = df.drop(columns=['등급코드'], errors='ignore')

# y, X 분리
y = df['평균단가(원)']
X = df.drop(columns=['평균단가(원)'])

# 날짜 처리
X['week_start'] = pd.to_datetime(X['week_start'])
X['year'] = X['week_start'].dt.year

# 학습/예측 분리
X_train = X[X['year'] < 2025].drop(columns=['week_start'])
y_train = y[X['year'] < 2025]
X_test = X[X['year'] == 2025].drop(columns=['week_start'])
y_test = y[X['year'] == 2025]

# 타겟 인코딩
encoder = ce.TargetEncoder(cols=['직팜산지코드', '품종코드'])
X_train = encoder.fit_transform(X_train, y_train)
X_test = encoder.transform(X_test)

# 이동평균 및 EMA 파생 변수 생성
def generate_moving_averages(df, target_col='평균단가(원)', group_cols=['직팜산지코드', '품종코드'], windows=[4, 13, 26]):
    df = df.sort_values(group_cols + ['year', 'week']).copy()
    for w in windows:
        df[f'SMA_{w}'] = df.groupby(group_cols)[target_col].transform(lambda x: x.rolling(window=w, min_periods=1).mean())
        df[f'EMA_{w}'] = df.groupby(group_cols)[target_col].transform(lambda x: x.ewm(span=w, adjust=False).mean())
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

df = df.dropna(subset=moving_avg_cols).copy()

# 이동평균 변수 스케일링
scaler = RobustScaler()
X_scaled = scaler.fit_transform(df[moving_avg_cols])
df_scaled = pd.DataFrame(X_scaled, columns=moving_avg_cols, index=df.index)
df.update(df_scaled)

# 모델 학습용 재분리 및 주기형 변수 처리
y = df['평균단가(원)']
X = df.drop(columns=['평균단가(원)'])

X['week_start'] = pd.to_datetime(X['week_start'])
X['year'] = X['week_start'].dt.year
X['week'] = X['week_start'].dt.isocalendar().week.astype(int)

X['week_sin'] = np.sin(2 * np.pi * X['week'] / 52)
X['week_cos'] = np.cos(2 * np.pi * X['week'] / 52)
X = X.drop(columns=['week'])

latest_year = X['year'].max()

X_train = X[X['year'] < 2025].drop(columns=['week_start'])
y_train = y[X['year'] < 2025]
X_test = X[X['year'] == 2025].drop(columns=['week_start'])
y_test = y[X['year'] == 2025]

param_distributions = {
    'n_estimators': [300, 500],
    'max_depth': [10, 20],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 3],
    'max_features': ['sqrt'],  # 고정
}

search = RandomizedSearchCV(
    estimator=RandomForestRegressor(random_state=42, n_jobs=-1),
    param_distributions=param_distributions,
    n_iter=5,       # 줄임
    cv=2,           # 줄임
    verbose=1,
    n_jobs=-1
)

search.fit(X_train, y_train)
model = search.best_estimator_
pred = model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

print("\n🏁 모델 성능 (1회 실행):")
print(f"📉 RMSE: {rmse:.2f}")
print(f"📈 R² : {r2:.4f}")
