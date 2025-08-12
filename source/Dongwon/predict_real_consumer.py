import os
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any
import random

# ❗ API 사용을 위한 라이브러리.
try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    import openai
    from dotenv import load_dotenv
except ImportError:
    retry = None; openai = None; wait_exponential = None; stop_after_attempt = None; load_dotenv = None

# =========================
# 1. 환경설정 및 상수 (v12.2)
# =========================
if load_dotenv:
    load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
MONTH_COLS = [f"months_since_launch_{i}" for i in range(1, 13)]
DAMPING_FACTOR = 0.5
USE_LLM = bool(API_KEY) and (openai is not None) and (retry is not None)

# ==================================
# 1-1. [v12.2] 실측 데이터 보정 '매출액' 앵커 (월별 기준)
# ==================================
CALIBRATED_REVENUE_ANCHORS = {
    "덴마크 하이그릭": 333_000_000,
    "동원맛참": 1_450_000_000,
    "동원참치액": 600_000_000,
    "리챔 오믈레햄": 275_000_000,
    "소잘라떼": 116_000_000,
}
PRODUCT_LINE_DATA = {
    "덴마크 하이그릭요거트 400g": {"line": "덴마크 하이그릭", "line_share": 1.0},
    "동원맛참 고소참기름 135g": {"line": "동원맛참", "line_share": 0.40},
    "동원맛참 고소참기름 90g": {"line": "동원맛참", "line_share": 0.15},
    "동원맛참 매콤참기름 135g": {"line": "동원맛참", "line_share": 0.30},
    "동원맛참 매콤참기름 90g": {"line": "동원맛참", "line_share": 0.15},
    "동원참치액 순 500g": {"line": "동원참치액", "line_share": 0.25},
    "동원참치액 순 900g": {"line": "동원참치액", "line_share": 0.15},
    "동원참치액 진 500g": {"line": "동원참치액", "line_share": 0.25},
    "동원참치액 진 900g": {"line": "동원참치액", "line_share": 0.15},
    "프리미엄 동원참치액 500g": {"line": "동원참치액", "line_share": 0.15},
    "프리미엄 동원참치액 900g": {"line": "동원참치액", "line_share": 0.05},
    "리챔 오믈레햄 200g": {"line": "리챔 오믈레햄", "line_share": 0.6},
    "리챔 오믈레햄 340g": {"line": "리챔 오믈레햄", "line_share": 0.4},
    "소화가 잘되는 우유로 만든 카페라떼 250mL": {"line": "소잘라떼", "line_share": 0.6},
    "소화가 잘되는 우유로 만든 바닐라라떼 250mL": {"line": "소잘라떼", "line_share": 0.4},
}
LINE_CATEGORY_MAP = {
    "덴마크 하이그릭": {"category": "발효유", "adoption_speed": "fast"},
    "동원맛참": {"category": "참치", "adoption_speed": "very_fast"},
    "동원참치액": {"category": "조미소스", "adoption_speed": "medium"},
    "리챔 오믈레햄": {"category": "축산캔", "adoption_speed": "slow"},
    "소잘라떼": {"category": "가공우유", "adoption_speed": "medium"}
}

# ========================================
# 1-2. [v12.2] 기타 계수
# ========================================
EVENT_FACTORS = {"참치": {9: 1.8, 1: 1.5, 2: 1.5, 10: 1.2}, "축산캔": {9: 2.5, 1: 2.0, 2: 2.0}, "발효유": {7: 1.3, 8: 1.3, 9: 1.1}, "가공우유": {7: 1.4, 8: 1.5, 9: 1.2}}
ADOPTION_CURVES = {
    "very_fast": [1.2, 1.3, 1.1, 1.0, 1.0, 0.95, 0.95, 0.9, 0.9, 0.9, 0.9, 0.9],
    "fast": [1.1, 1.2, 1.1, 1.0, 1.0, 1.0, 0.95, 0.95, 0.95, 0.9, 0.9, 0.9],
    "medium": [1.0, 1.1, 1.1, 1.05, 1.0, 1.0, 0.95, 0.95, 0.95, 0.95, 0.9, 0.9],
    "slow": [0.8, 0.9, 1.0, 1.05, 1.05, 1.0, 1.0, 1.0, 0.95, 0.95, 0.95, 0.9],
}
MARKETING_MIX = {"TV": 1.2, "Youtube": 1.15, "SNS": 1.1, "엘리베이터": 1.1, "바이럴": 1.1}
INCOME_QUINTILES_BY_AGE = {
    "39세 이하": ["150만원 이하", "150-300만원", "300-500만원", "500-700만원", "700만원 이상"],
    "40대": ["200만원 이하", "200-400만원", "400-600만원", "600-800만원", "800만원 이상"],
    "50대": ["200만원 이하", "200-400만원", "400-650만원", "650-900만원", "900만원 이상"],
    "60세 이상": ["100만원 이하", "100-250만원", "250-400만원", "400-600만원", "600만원 이상"]
}

# =========================
# 2. 데이터 로더 및 LLM 클라이언트
# =========================
CLIENT = None
if USE_LLM:
    try:
        CLIENT = openai.OpenAI(api_key=API_KEY)
    except Exception as e:
        logging.error(f"OpenAI 클라이언트 생성 실패: {e}"); USE_LLM = False

def load_consumer_data() -> pd.DataFrame | None:
    try:
        df = pd.read_csv("survey_string.csv", low_memory=False, dtype=str).fillna('정보 없음')
        logging.info("✅ 'survey_string.csv' 로드 성공. 확정된 컬럼명으로 데이터를 처리합니다.")
        column_map = {
            'SQ1_op': 'age', 'DQ1': 'gender', 'DQ4A1': 'income', 'A1': 'purchase_place',
            'A2_1': 'purchase_consideration', 'A11A1': '참치_freq', 'A11A2': '축산캔_freq',
            'A11A12': '발효유_freq', 'A11A10': '가공우유_freq', 'A11A5': '조미소스_freq'
        }
        existing_cols = {k: v for k, v in column_map.items() if k in df.columns}
        if not existing_cols:
            logging.error("CSV 파일에서 어떠한 유효한 컬럼도 찾지 못했습니다. 헤더를 확인해주세요.")
            return None
        df_persona = df[list(existing_cols.keys())].rename(columns=existing_cols)
        for col in df_persona.columns:
            df_persona[col] = df_persona[col].str.strip().replace('nan', '정보 없음')
        return df_persona
    except FileNotFoundError:
        logging.error("'survey_string.csv' 파일을 찾을 수 없어 페르소나 생성을 건너<binary data, 2 bytes><binary data, 2 bytes>니다.")
        return None
    except Exception as e:
        logging.error(f"소비자 데이터 처리 중 오류 발생: {e}")
        return None

# =========================
# 3. 핵심 예측 함수 (v12.2)
# =========================
def get_age_group_for_income(age_str: str) -> str:
    try:
        age = int(age_str)
        if age < 40: return "39세 이하"
        if age < 50: return "40대"
        if age < 60: return "50대"
        return "60세 이상"
    except (ValueError, TypeError):
        return "39세 이하"

def generate_persona_from_real_data(df_consumer: pd.DataFrame, category: str) -> List[Dict[str, str]]:
    personas = []
    cat_keyword_map = {"참치": "참치", "축산캔": "축산캔", "발효유": "발효유", "가공우유": "가공우유", "조미소스": "조미소스"}
    cat_keyword = cat_keyword_map.get(category, "")
    freq_col = f"{cat_keyword}_freq"
    
    if freq_col in df_consumer.columns:
        likely_buyers = df_consumer[df_consumer[freq_col].str.contains('일|주|달', na=False)]
        sample_consumers = likely_buyers.sample(n=3, replace=True) if len(likely_buyers) < 3 else likely_buyers.sample(n=3)
    else:
        sample_consumers = df_consumer.sample(n=3, replace=True)

    for _, row in sample_consumers.iterrows():
        age_str = str(row.get('age', '정보 없음'))
        if not age_str.isdigit(): age_str = '정보 없음'
        
        gender_str = str(row.get('gender', ''))
        if '남' not in gender_str and '여' not in gender_str: gender_str = ''

        income_str = str(row.get('income', '정보 없음'))
        if '정보 없음' in income_str or '모름' in income_str or not any(char.isdigit() for char in income_str):
            age_group = get_age_group_for_income(age_str)
            estimated_income_range = random.choice(INCOME_QUINTILES_BY_AGE.get(age_group, ["300-500만원"]))
            income_str = f"{estimated_income_range} (통계 기반)"

        name = f"{age_str}세 {gender_str} 소비자".strip() if age_str != '정보 없음' else f"{gender_str} 소비자".strip()
        desc = (f"나는 {age_str}세 {gender_str}이며, 가구 소득은 월 {income_str} 수준입니다. "
                f"주로 {row.get('purchase_place', '대형마트')}에서 장을 보고, "
                f"식품을 살 때 가장 중요하게 생각하는 것은 '{row.get('purchase_consideration', '맛')}' 입니다.")
        personas.append({"name": name, "description": desc})
    return personas


def get_baseline_units(product_info: dict) -> int:
    try:
        product_name = product_info['product_name']
        price_str = str(product_info.get('1개 가격', '0')).replace('원', '').replace(',', '')
        price = int(price_str) if price_str.isdigit() else 0
        if price == 0:
             logging.warning(f"'{product_name}'의 가격 정보가 유효하지 않아 기본값을 반환합니다.")
             return 1000

        line_data = PRODUCT_LINE_DATA[product_name]
        line_name = line_data['line']
        
        line_revenue_anchor = CALIBRATED_REVENUE_ANCHORS[line_name]
        product_revenue = line_revenue_anchor * line_data['line_share']
        product_baseline_units = product_revenue / price
        
        return int(product_baseline_units)
    except (KeyError, ValueError, ZeroDivisionError) as e:
        logging.warning(f"'{product_info.get('product_name')}' 기준 판매량 계산 실패({e}). 기본값을 반환합니다.")
        return 1000

def get_event_adjusted_baseline(product_name: str, baseline_units: int, month: int, ad_info: str) -> int:
    try:
        line_name = PRODUCT_LINE_DATA[product_name]['line']
        line_info = LINE_CATEGORY_MAP[line_name]
        category = line_info['category']
        adoption_speed = line_info.get('adoption_speed', 'medium')
    except KeyError:
        # Fallback
        if '요거트' in product_name: category = '발효유'
        elif '참치' in product_name: category = '참치'
        elif '햄' in product_name: category = '축산캔'
        elif '라떼' in product_name: category = '가공우유'
        else: category = '조미소스'
        adoption_speed = "medium"

    adjusted_baseline = float(baseline_units) * ADOPTION_CURVES[adoption_speed][month - 1]
    calendar_month = (7 + month - 2) % 12 + 1
    adjusted_baseline *= EVENT_FACTORS.get(category, {}).get(calendar_month, 1.0)
    
    ad_factor = 1.0
    ad_months = []
    month_ranges = re.findall(r'(\d+)-(\d+)월', ad_info)
    for start, end in month_ranges:
        ad_months.extend(range(int(start), int(end) + 1))
    single_months = re.findall(r'(?<!-)(\d+)월', ad_info)
    ad_months.extend([int(m) for m in single_months])
    
    if calendar_month in list(set(ad_months)):
        for channel, factor in MARKETING_MIX.items():
            if channel in ad_info:
                ad_factor = max(ad_factor, factor)
    
    adjusted_baseline *= ad_factor
    return int(adjusted_baseline)

if retry:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def llm_api_call(client, system_prompt, user_prompt):
        logging.info(f"--- OpenAI API 요청 --- \n[프롬프트]:\n{user_prompt}\n--------------------------")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError: return {}
        else:
            num_match = re.search(r'\d+', content)
            if num_match: return {"predicted_sales": int(num_match.group(0))}
        return {}
else:
    def llm_api_call(*args, **kwargs): raise ImportError("LLM-related modules not found.")

def predict_sales_for_month(persona, market_info, event_adjusted_baseline, month_context):
    system_prompt = "당신은 주어진 프로필의 대한민국 소비자입니다. 다른 설명 없이, 반드시 다음 JSON 형식 하나만 반환해주세요: {\"predicted_sales\": <구매할 개수>}"
    price_info = market_info.get('1개 가격', '미정')
    user_prompt = (f"- **당신 정보**: {persona['description']}\n"
                   f"- **신제품 정보**: {market_info['product_name']} (가격: {price_info}, 특징: {market_info['product_feature']})\n"
                   f"- **이번 달 상황**: {month_context}\n\n"
                   f"위 정보를 바탕으로, 이번 달에 이 신제품을 몇 개나 구매하시겠습니까? (숫자만)")
    return llm_api_call(CLIENT, system_prompt, user_prompt)

def run_simulation(persona_bundle: list, product_info: dict, baseline_sales: int):
    monthly_sales = []
    ad_info = product_info.get('product_feature', '')
    prod_name = product_info['product_name']
    for month in range(1, 13):
        event_adjusted_baseline = get_event_adjusted_baseline(prod_name, baseline_sales, month, ad_info)
        if USE_LLM and CLIENT and persona_bundle:
            try:
                # [v12.2] BUG FIX: 정확한 카테고리명('발효유' 등)을 참조하도록 수정
                line_name = PRODUCT_LINE_DATA[prod_name]['line']
                category = LINE_CATEGORY_MAP[line_name]['category']
                
                calendar_month = (7 + month - 2) % 12 + 1
                seasonal_factor = EVENT_FACTORS.get(category, {}).get(calendar_month, 1.0)
                month_context = f"출시 {month}개월차 ({calendar_month}월)"
                if seasonal_factor > 1.2: month_context += ", 특별한 시즌(명절, 휴가철)입니다."
                
                ad_months = []
                month_ranges = re.findall(r'(\d+)-(\d+)월', ad_info)
                for start, end in month_ranges: ad_months.extend(range(int(start), int(end) + 1))
                single_months = re.findall(r'(?<!-)(\d+)월', ad_info)
                ad_months.extend([int(m) for m in single_months])
                if calendar_month in list(set(ad_months)):
                    month_context += " 이번 달은 신제품 광고가 집행되는 기간입니다."

                persona_predictions = [predict_sales_for_month(p, product_info, event_adjusted_baseline, month_context).get("predicted_sales", event_adjusted_baseline) for p in persona_bundle]
                llm_predicted_sales = sum(persona_predictions) / len(persona_predictions)
                final_sales = int(event_adjusted_baseline * (1 - DAMPING_FACTOR) + llm_predicted_sales * DAMPING_FACTOR)
                monthly_sales.append(final_sales)
            except Exception as e:
                logging.warning(f"Month {month} LLM 예측 실패: {e}. 데이터 기반 예측값을 사용합니다.")
                monthly_sales.append(event_adjusted_baseline)
        else:
            monthly_sales.append(event_adjusted_baseline)
    return monthly_sales

# =========================
# 4. Main 실행 로직 (v12.2)
# =========================
def main():
    df_consumer = load_consumer_data()
    try:
        df_info = pd.read_csv("product_info.csv")
        df_sample = pd.read_csv("sample_submission.csv")
    except FileNotFoundError as e:
        logging.error(f"오류: 필수 파일이 없습니다. ({e.filename})")
        return

    products = df_info.to_dict('records')
    outputs = []
    for prod in products:
        prod_name = prod.get("product_name")
        if not prod_name or pd.isna(prod_name): continue
        
        try:
            line_name = PRODUCT_LINE_DATA[prod_name]['line']
            # [v12.2] BUG FIX: 정확한 카테고리명('발효유' 등)을 참조하도록 수정
            category = LINE_CATEGORY_MAP[line_name]['category']
        except KeyError:
            category = "기타"
            
        logging.info(f"--- '{prod_name}' 판매 '개수' 예측 시작 ---")
        baseline_sales_units = get_baseline_units(prod)
        if USE_LLM and CLIENT and (df_consumer is not None):
            try:
                persona_bundle = generate_persona_from_real_data(df_consumer, category)
                logging.info(f"샘플링된 실제 소비자 페르소나: {[p['name'] for p in persona_bundle]}")
                monthly_sales_units = run_simulation(persona_bundle, prod, baseline_sales_units)
            except Exception as e:
                logging.error(f"페르소나 생성/시뮬레이션 전체 실패: {e}. 데이터 기반 예측으로 전환합니다.")
                monthly_sales_units = run_simulation([], prod, baseline_sales_units)
        else:
            monthly_sales_units = run_simulation([], prod, baseline_sales_units)
        outputs.append({"product_name": prod_name, **{MONTH_COLS[i]: s for i, s in enumerate(monthly_sales_units)}})
        logging.info(f"--- '{prod_name}' 예측 완료: 월평균 {sum(monthly_sales_units)//12 if sum(monthly_sales_units) > 0 else 0:,} 개 ---")

    df_sub = pd.DataFrame(outputs)
    final_cols = df_sample.columns
    for col in final_cols:
        if col not in df_sub.columns: df_sub[col] = 0
    df_sub = df_sub[final_cols]
    output_filename = "submission_final_v12_2.csv"
    df_sub.to_csv(output_filename, index=False, encoding='utf-8')
    logging.info(f"✅ 최종 예측 파일 저장 완료: {output_filename}")
    print("\n--- 최종 예측 결과 (상위 5개) ---")
    print(df_sub.head())

if __name__ == "__main__":
    print("🚀 V12.2 예측 모델('버그 수정' 최종 버전)을 실행합니다...")
    if USE_LLM:
        print("✅ OpenAI API 키가 확인되었습니다. 실제 소비자 데이터 기반 페르소나 시뮬레이션을 실행합니다.")
    else:
        print("⚠️ API 키가 없어 LLM 시뮬레이션 없이, 데이터 기반으로만 예측을 수행합니다.")
    main()