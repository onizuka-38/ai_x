import os
import json
import logging
import argparse
import pandas as pd
from dotenv import load_dotenv
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from jsonschema import Draft202012Validator
from openai import OpenAI
import openai as _openai

# =========================
# 1. 최종 환경설정 및 상수
# =========================
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o") # 고성능 모델 사용 권장
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
MONTH_COLS = [f"months_since_launch_{i}" for i in range(1, 13)]
DAMPING_FACTOR = 0.5  # LLM 예측 변동성 제어 계수

# [최종 수정] 실제 시장 규모 비율을 반영한 기준 판매량
ANCHOR_MARKET_DATA = {
    # 8,000억 시장의 압도적 1위. 기준점을 대폭 상향.
    "참치":     {"baseline_monthly_sales": 45000}, 
    # 참치/축산캔 다음가는 규모와 명절 특수 반영.
    "축산캔":   {"baseline_monthly_sales": 32000},
    # 1,000억 규모 시장에서의 경쟁 구도 반영.
    "우유류":   {"baseline_monthly_sales": 9500},
    # 1,136억 시장. 요거트와 유사하거나 약간 낮은 수준.
    "조미소스": {"baseline_monthly_sales": 9000},
    "기타":     {"baseline_monthly_sales": 7500},
}

# =========================
# 2. [최종] 지능형 프롬프트 생성
# =========================
PERSONA_SCHEMA = {
    "type": "object",
    "properties": {
        "product_specific_scaling_factor": {"type": "number", "description": "이 특정 제품이 카테고리 평균(1.0) 대비 얼마나 더 팔릴지(1.2) 또는 덜 팔릴지(0.8)에 대한 예측 계수."},
        "personas": {"type": "array", "items": {"type": "object", "properties": {"persona_name": {"type": "string"},"description": {"type": "string"},"population_segment_percentage": {"type": "number"},"attributes": {"type": "object", "properties": {"age": {"type": "string"},"gender": {"type": "string"},"occupation": {"type": "string"}}, "required": ["age", "gender", "occupation"]}, "base_purchase_rate": {"type": "number", "description": "해당 페르소나 그룹의 1인당 연간 평균 구매 개수 추정치"}, "dynamic_factors": {"type": "object", "properties": {"advertising_sensitivity": {"type": "number", "description": "광고에 얼마나 민감하게 반응하는지 (0~1)"},"event_sensitivity": {"type": "number", "description": "이벤트/프로모션에 얼마나 민감하게 반응하는지 (0~1)"}},"required": ["advertising_sensitivity", "event_sensitivity"]}}, "required": ["persona_name", "description", "population_segment_percentage", "attributes", "base_purchase_rate", "dynamic_factors"]}}
    },
    "required": ["product_specific_scaling_factor", "personas"]
}

def get_market_context(product: Dict[str, Any], market_data_summary: str) -> str:
    # [데이터 기반] 최종 컨텍스트
    context = f"""
[공통 시장 배경] KREI '2024 식품소비행태조사'에 따르면, 고물가로 인한 '가성비' 소비와 건강을 중시하는 '헬시플레저' 트렌드가 공존. 1인 가구 비중이 늘고, 간편식(HMR) 소비가 증가하는 추세.
[해당 제품 카테고리 실제 데이터 요약]
{market_data_summary}
[카테고리별 심층 분석]
"""
    cat1 = product.get('category_level_1', '')
    name = product.get('product_name', '')
    
    if '우유류' in cat1:
        if '요거트' in name: context += "[그릭요거트 시장] 2024년 기준 약 1,000억 원 규모의 고성장 시장. 풀무원, 매일 등과 경쟁이 치열하며, 20-30대 여성이 주 소비층. 고단백, 꾸덕한 질감이 중요. 1월과 6-8월에 수요 집중."
        if '라떼' in name: context += "[RTD 커피 시장] 롯데칠성, 동서식품 등이 주도하는 경쟁 포화 시장. '락토프리'는 유당불내증을 겪는 소비자를 타겟으로 한 명확한 차별점. 여름철에 판매량 증가."
    elif '참치' in cat1: context += "[참치캔 시장] 동원이 70% 이상을 차지하는 압도적 1위 시장. '동원맛참'은 기존 참치에 맛을 더한 차세대 제품. 명절(추석, 설) 선물세트 판매량이 연매출의 큰 비중을 차지하여 해당 월에 판매량 급증."
    elif '조미소스' in cat1: context += "[액상 조미료 시장] 집밥 트렌드로 빠르게 성장하는 시장. CJ, 샘표 '연두' 등과 경쟁. '참치액'은 감칠맛을 내는 용도로 다양한 요리에 활용됨. 명절 시즌에 수요 소폭 증가."
    elif '축산캔' in cat1: context += "[캔햄 시장] CJ스팸이 1위, 동원 리챔이 2위인 성숙한 시장. 저염 등 건강을 강조하는 것이 특징. 참치캔과 마찬가지로 명절 선물세트가 매출의 절대적인 비중을 차지함."
    return context

def create_user_prompt(product: Dict[str, Any], market_data_summary: str) -> str:
    return f"""당신은 대한민국 최고의 CPG 시장 분석가입니다. 주어진 제품 정보와 실제 시장 데이터를 바탕으로, 소비자 페르소나를 생성하고 향후 12개월간의 월별 판매량을 예측해주세요.
**[출력 규칙]**
- 반드시 아래 JSON 스키마를 100% 준수하는 단일 JSON 객체만 출력하십시오. 설명은 절대 추가하지 마세요.
- `base_purchase_rate`는 페르소나 그룹 1인당 연간 구매량입니다.
- `dynamic_factors`의 `sensitivity`는 0(반응 없음)에서 1(매우 민감) 사이의 값입니다.
- `product_specific_scaling_factor`는 반드시 0.7에서 1.5 사이의 값이어야 합니다.
**[JSON 스키마]**
{json.dumps(PERSONA_SCHEMA, indent=2, ensure_ascii=False)}
**[제품 정보]**
- 제품명: {product.get('product_name')} / 카테고리: {product.get('category_level_1', '')} / 특징: {product.get('product_feature')}
**[실제 시장 데이터 및 분석]**
{get_market_context(product, market_data_summary)}
이제, 위 정보를 바탕으로 JSON을 생성해주십시오."""

# =========================
# 3. LLM 호출 및 파싱
# =========================
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type((_openai.APIError, _openai.Timeout, _openai.RateLimitError)))
def call_openai_personas(client: OpenAI, product: Dict[str, Any], market_data_summary: str) -> Dict[str, Any]:
    user_prompt = create_user_prompt(product, market_data_summary)
    logging.info(f"Generating personas for: {product.get('product_name')}")
    response = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": user_prompt}], response_format={"type": "json_object"}, temperature=0.4)
    content = response.choices[0].message.content
    return json.loads(content)

# =========================
# 4. [최종] 시뮬레이션 및 스케일링
# =========================
def get_baseline_sales(product: Dict[str, Any]) -> float:
    cat1 = product.get('category_level_1', '')
    return ANCHOR_MARKET_DATA.get(cat1, ANCHOR_MARKET_DATA["기타"])['baseline_monthly_sales']

def run_simulation(persona_bundle: Dict[str, Any], market_info: pd.DataFrame, baseline_sales: float) -> List[int]:
    monthly_sales = [0.0] * 12
    if 'personas' not in persona_bundle or not persona_bundle['personas']: return [int(baseline_sales)] * 12

    product_scale = persona_bundle.get('product_specific_scaling_factor', 1.0)

    for i in range(12):
        month_data = market_info.iloc[i]
        total_persona_driven_sales = 0

        for persona in persona_bundle.get('personas', []):
            try:
                pop_percent = persona.get('population_segment_percentage', 0) / 100.0
                base_rate_monthly = persona.get('base_purchase_rate', 0) / 12.0
                
                dyn_factors = persona.get('dynamic_factors', {})
                ad_sens = dyn_factors.get('advertising_sensitivity', 0)
                evt_sens = dyn_factors.get('event_sensitivity', 0)

                # 페르소나 기본 구매량
                persona_base_sale = base_rate_monthly * pop_percent
                
                # 페르소나 동적 구매량 (광고/이벤트 민감도 반영)
                ad_effect = ad_sens if month_data['ad_campaign'] == '진행중' else 0
                evt_effect = evt_sens if month_data['event'] != '없음' else 0
                
                persona_dynamic_sale = persona_base_sale * (ad_effect + evt_effect) * DAMPING_FACTOR
                
                total_persona_driven_sales += (persona_base_sale + persona_dynamic_sale)

            except (TypeError, KeyError) as e:
                logging.warning(f"Skipping persona due to data issue: {e}")
                continue
        
        # 데이터 기반 외부 효과 적용
        seasonality_factor = month_data['seasonality_index']
        
        # 월별 최종 판매량 계산
        final_month_sale = baseline_sales * product_scale * seasonality_factor * total_persona_driven_sales
        monthly_sales[i] = final_month_sale

    return [max(0, int(round(m))) for m in monthly_sales]


# =========================
# 5. 메인 실행 로직
# =========================
def main(in_csv: str, out_csv: str, sample_csv: str, market_csv: str, dry_run: bool = False):
    client = OpenAI(api_key=API_KEY) if not dry_run else None
    
    try:
        df_prod, df_sample, df_market = pd.read_csv(in_csv), pd.read_csv(sample_csv), pd.read_csv(market_csv)
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}"); return

    outputs = []
    for _, row in df_prod.iterrows():
        prod = row.to_dict()
        cat1 = prod.get('category_level_1')
        
        market_info_for_product = df_market[df_market['category'] == cat1].reset_index(drop=True)
        if market_info_for_product.empty:
            logging.warning(f"No market data for category: {cat1}. Skipping product: {prod.get('product_name')}")
            continue

        if not dry_run:
            try:
                persona_bundle = call_openai_personas(client, prod, market_info_for_product.to_string())
                baseline_sales = get_baseline_sales(prod)
                monthly_sales = run_simulation(persona_bundle, market_info_for_product, baseline_sales)
            except Exception as e:
                logging.error(f"Run failed for {prod.get('product_name')}: {e}. Check API key or connection.")
                monthly_sales = [int(get_baseline_sales(prod))] * 12
        else:
             monthly_sales = [int(get_baseline_sales(prod))] * 12

        outputs.append({"product_name": prod.get("product_name"), **{MONTH_COLS[i]: monthly_sales[i] for i in range(12)}})

    df_sub = pd.DataFrame(outputs)[df_sample.columns]
    df_sub.to_csv(out_csv, index=False, encoding='utf-8')
    logging.info(f"✅ Submission file saved to -> {out_csv}")
    print("\n--- 최종 예측 결과 (상위 5개) ---"); print(df_sub.head())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data-Driven Product Demand Forecaster")
    parser.add_argument("--product_info", default="data/product_info.csv")
    parser.add_argument("--sample_submission", default="data/sample_submission.csv")
    parser.add_argument("--market_data", default="data/market_data.csv")
    parser.add_argument("--output", default="submission_final.csv")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    main(in_csv=args.product_info, out_csv=args.output, sample_csv=args.sample_submission, market_csv=args.market_data, dry_run=args.dry_run)