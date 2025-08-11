import os
import json
import math
import time
import argparse
import logging
import random
import inspect
from dotenv import load_dotenv
from typing import List, Dict, Any
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from jsonschema import Draft202012Validator
from openai import OpenAI
import openai as _openai

# =========================
# 환경설정 및 기본 설정
# =========================
# .env 파일에서 환경 변수를 로드합니다.
# from dotenv import load_dotenv
# load_dotenv()

# API 키 및 모델 설정
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# 결과 CSV의 월별 컬럼명
MONTH_COLS = [f"months_since_launch_{i}" for i in range(1, 13)]

# =========================
# 💡 1단계 (전략 수정): 기준점(Anchor) 기반 시장 데이터
# =========================
# 캡틴의 피드백을 반영하여, '10000'을 기준으로 한 월평균 판매량 데이터를 설정합니다.
ANCHOR_MARKET_DATA = {
    "참치캔":   {"baseline_monthly_sales": 12000}, # 시장 지배적 제품, 높은 기준점
    "축산캔":   {"baseline_monthly_sales": 11000}, # 명절 특수가 있어 높은 기준점
    "액상조미료": {"baseline_monthly_sales": 9000},  # 성장 시장이지만 경쟁 치열
    "발효유":   {"baseline_monthly_sales": 8000},  # 트렌디하지만 시장 크기는 상대적으로 작음
    "기타":     {"baseline_monthly_sales": 7500},  # 일반적인 기타 제품군
    "컵커피":   {"baseline_monthly_sales": 7000},  # 경쟁이 매우 치열하여 기준점을 약간 낮춤
}

# =========================
# 💡 2단계: 지능형 프롬프트 생성 (오류 수정 완료)
# =========================

def get_market_context(product: Dict[str, Any]) -> str:
    cat1 = product.get('category_level_1', '')
    name = product.get('product_name', '')
    context = "대한민국 최신 식품 소비 트렌드: 1인 가구 증가, 건강과 편리미엄(건강+프리미엄) 중시, HMR(가정간편식) 시장 급성장, '헬시플레저' 트렌드 확산.\n"
    if '참치' in cat1: context += "참치캔 시장: 동원F&B가 80% 이상의 압도적 점유율. 명절(추석, 설) 선물세트 판매가 연 매출의 20% 이상을 차지. 최근 1인 가구를 겨냥한 소용량, 다양한 맛의 제품이 인기. '동원맛참'은 광고모델 '안유진'을 통해 Z세대에게 어필하며, 오뚜기 등 경쟁사도 유사 제품 출시 예정으로 경쟁 심화 예상."
    if '요거트' in name or '발효유' in cat1: context += "그릭요거트 시장: 건강 및 다이어트 트렌드로 급성장. 풀무원, 후디스 등 경쟁사 다수. 제품의 꾸덕한 질감, 단백질 함량이 주요 구매 결정 요인. 6-8월 여름 시즌과 연초(1월)에 다이어트 수요 증가. 제품 정보에 따르면 6-8월 집중 광고 예정."
    if '참치액' in name: context += "액상 조미료 시장: 요리 인구 증가와 함께 빠르게 성장 중. CJ, 샘표 '연두' 등과 경쟁. '훈연참치' 등 원료의 특별함과 깊은 맛을 소구하는 것이 중요."
    if '리챔' in name: context += "캔햄 시장: 명절 선물세트 수요가 절대적. 저나트륨, 저지방 등 건강을 강조한 제품이 프리미엄 라인으로 인식되며 인기."
    if '소잘' in name: context += "RTD 커피 시장: 경쟁 매우 치열. '락토프리', '저당' 등 건강 기능성을 차별점으로 내세우는 것이 중요. 2-7월 SNS 바이럴 활동이 예측 기간인 7월에 영향을 미칠 수 있음."
    return context

PERSONA_SCHEMA = {
    "type": "object", "properties": {"personas": {"type": "array", "items": {"type": "object", "properties": {"persona_name": {"type": "string"}, "description": {"type": "string"}, "population_segment_percentage": {"type": "number", "minimum": 0, "maximum": 100}, "attributes": {"type": "object", "properties": {"age": {"type": "string"}, "gender": {"type": "string"}, "occupation": {"type": "string"}, "income_level_krw": {"type": "string"}, "household_size": {"type": "string"}, "residence_area": {"type": "string"}, "health_consciousness": {"type": "string", "enum": ["높음", "중간", "낮음"]}, "price_sensitivity": {"type": "string", "enum": ["높음", "중간", "낮음"]}, "convenience_seeking": {"type": "string", "enum": ["높음", "중간", "낮음"]}, "brand_loyalty": {"type": "string", "enum": ["높음", "중간", "낮음"]}, "trend_sensitivity": {"type": "string", "enum": ["혁신수용층", "조기수용층", "후기수용층"]}, "primary_shopping_channel": {"type": "string", "enum": ["대형마트", "온라인", "편의점", "전통시장"]}, "cooking_frequency": {"type": "string", "enum": ["주 5회 이상", "주 2-4회", "주 1회 이하"]}, "sns_usage": {"type": "string", "enum": ["높음", "중간", "낮음"]}}, "required": ["age", "gender", "occupation", "income_level_krw", "household_size", "residence_area", "health_consciousness", "price_sensitivity", "convenience_seeking", "brand_loyalty", "trend_sensitivity", "primary_shopping_channel", "cooking_frequency", "sns_usage"]}, "base_purchase_rate": {"type": "number", "description": "해당 페르소나의 연간 평균 구매 개수 추정치"}, "monthly_adjustment_factors": {"type": "object", "properties": {"seasonality": {"type": "array", "items": {"type": "number"}, "minItems": 12, "maxItems": 12}, "advertising": {"type": "array", "items": {"type": "number"}, "minItems": 12, "maxItems": 12}, "events": {"type": "array", "items": {"type": "number"}, "minItems": 12, "maxItems": 12}}, "required": ["seasonality", "advertising", "events"]}}, "required": ["persona_name", "description", "population_segment_percentage", "attributes", "base_purchase_rate", "monthly_adjustment_factors"]}}}, "required": ["personas"]}

# SyntaxError를 피하기 위해 프롬프트를 여러 부분으로 나누어 생성
schema_as_json_string = json.dumps(PERSONA_SCHEMA, indent=2, ensure_ascii=False)
PROMPT_PART1 = """당신은 대한민국 소비재(CPG/FMCG) 시장을 전문으로 하는 최고의 시장 조사 분석가입니다. 당신의 임무는 주어진 제품 정보와 시장 데이터를 바탕으로, 잠재 소비자 페르소나를 생성하고, 그들의 구매 행동을 시뮬레이션하여 향후 12개월간의 월별 판매량의 '패턴'을 예측하는 것입니다. 절대적인 판매량을 맞출 필요는 없습니다. 월별 상대적인 변화에만 집중하십시오.

**[수행 과제]**
아래 [제품 정보]와 [시장 컨텍스트 및 데이터]를 깊이 분석하여, 이 제품을 구매할 가능성이 있는 **3~5개의 고유한 소비자 페르소나**를 생성해 주십시오.

**[출력 규칙]**
- 출력은 반드시 단일 JSON 객체여야 합니다. JSON 앞뒤로 어떠한 설명이나 추가 텍스트도 포함하지 마십시오.
- 아래에 명시된 JSON 스키마를 100% 준수해야 합니다.
- `monthly_adjustment_factors`는 각 월(2024년 7월 ~ 2025년 6월)의 기본 구매력 대비 변화율을 의미하는 12개의 숫자 배열입니다. 예를 들어, 0.2는 해당 월에 20% 구매가 증가함을, -0.1은 10% 감소함을 의미합니다.
  - `seasonality`: 날씨, 계절(여름, 겨울), 휴가 시즌 등 계절적 요인.
  - `advertising`: 제품 정보에 명시된 광고 캠페인(TV, SNS 등)의 효과.
  - `events`: 명절(추석, 설), 특정 프로모션(블랙프라이데이 등) 이벤트 효과.

**[JSON 스키마]**
```json
"""
PROMPT_PART2 = "\n```"
SYSTEM_PROMPT = PROMPT_PART1 + schema_as_json_string + PROMPT_PART2

def create_user_prompt(product: Dict[str, Any]) -> str:
    return f"""**[제품 정보]**
- 제품명: {product.get('product_name')}
- 제품 카테고리: {product.get('category_level_1', '')} > {product.get('category_level_2', '')} > {product.get('category_level_3', '')}
- 제품 특징: {product.get('product_feature')}

**[시장 컨텍스트 및 데이터]**
{get_market_context(product)}

이제, 위 정보를 바탕으로 페르소나 분석 및 월별 판매량 '패턴' 예측을 위한 JSON을 생성해주십시오."""

# =========================
# 💡 3단계: LLM 호출 및 파싱
# =========================
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type((_openai.APIError, _openai.Timeout, _openai.RateLimitError)))
def call_openai_personas(client: OpenAI, product: Dict[str, Any]) -> Dict[str, Any]:
    user_prompt = create_user_prompt(product)
    logging.info(f"Generating personas for: {product.get('product_name')}")
    response = client.chat.completions.create(model=MODEL, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}], response_format={"type": "json_object"}, temperature=0.5, top_p=0.9)
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        validator = Draft202012Validator(PERSONA_SCHEMA)
        if not validator.is_valid(data):
            logging.warning(f"JSON validation failed for {product.get('product_name')}")
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON for {product.get('product_name')}: {e}\nReceived content: {content}")
        raise ValueError("LLM response is not a valid JSON") from e

# =========================
# 💡 4단계: 시뮬레이션 및 스케일링 (전략 수정 완료)
# =========================
def calculate_relative_pattern(bundle: Dict[str, Any]) -> List[float]:
    if 'personas' not in bundle or not bundle['personas']: return [1.0] * 12
    
    total_monthly_pattern = [0.0] * 12
    for persona in bundle.get('personas', []):
        try:
            base_rate = persona.get('base_purchase_rate', 0) * (persona.get('population_segment_percentage', 0) / 100.0)
            if base_rate == 0: continue
            
            adj = persona.get('monthly_adjustment_factors', {})
            # 오류가 수정된 라인: 리스트 컴프리헨션을 대괄호로 묶어 리스트로 만듭니다.
            s_adj, a_adj, e_adj = [(adj.get(k, [0]*12) + [0]*12)[:12] for k in ['seasonality', 'advertising', 'events']]
            
            for i in range(12):
                total_adjustment = 1.0 + s_adj[i] + a_adj[i] + e_adj[i]
                total_monthly_pattern[i] += base_rate * total_adjustment
        except (TypeError, KeyError) as e:
            logging.warning(f"Skipping persona due to data issue: {persona.get('persona_name')}. Error: {e}")
            continue
            
    return total_monthly_pattern if sum(total_monthly_pattern) > 0 else [1.0] * 12

def get_baseline_sales(product: Dict[str, Any]) -> float:
    cat1, name = product.get('category_level_1', ''), product.get('product_name', '')
    if '참치' in cat1: return ANCHOR_MARKET_DATA["참치캔"]['baseline_monthly_sales']
    if '축산' in cat1: return ANCHOR_MARKET_DATA["축산캔"]['baseline_monthly_sales']
    if '발효유' in cat1: return ANCHOR_MARKET_DATA["발효유"]['baseline_monthly_sales']
    if '조미료' in cat1 or '참치액' in name: return ANCHOR_MARKET_DATA["액상조미료"]['baseline_monthly_sales']
    if '커피' in cat1: return ANCHOR_MARKET_DATA["컵커피"]['baseline_monthly_sales']
    return ANCHOR_MARKET_DATA["기타"]['baseline_monthly_sales']

def dryrun_baseline(product: Dict[str, Any]) -> List[int]:
    logging.warning(f"Executing fallback baseline for: {product.get('product_name')}")
    base = get_baseline_sales(product)
    seasonal_pattern = [base * (1 + 0.3 * math.sin(math.pi * i / 6)) for i in range(12)]
    if '참치' in product.get('category_level_1', '') or '축산' in product.get('category_level_1', ''):
        seasonal_pattern[1] = base * 1.5; seasonal_pattern[6] = base * 1.4
    return [max(0, int(round(val))) for val in seasonal_pattern]

# =========================
# 💡 5단계: 메인 실행 로직 (전략 수정 완료)
# =========================
def run(in_csv: str, out_csv: str, sample_csv: str, dry_run: bool = False):
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        logging.warning("OPENAI_API_KEY is not set. Forcing DRY_RUN.")
        dry_run = True
    client = OpenAI(api_key=API_KEY) if not dry_run else None
    
    try:
        df_prod, df_sample = pd.read_csv(in_csv), pd.read_csv(sample_csv)
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}"); return

    outputs = []
    for _, row in df_prod.iterrows():
        prod = row.to_dict()
        monthly_sales = []
        
        if not dry_run:
            try:
                # 1. LLM 호출하여 페르소나 및 월별 '패턴' 데이터 수집
                persona_bundle = call_openai_personas(client, prod)
                
                # 2. 페르소나 기반 월별 상대적 판매 '패턴' 계산
                relative_pattern = calculate_relative_pattern(persona_bundle)
                
                # 3. 기준 판매량(Anchor) 조회
                baseline_sales = get_baseline_sales(prod)
                
                # 4. (새로운 로직) 패턴의 평균을 기준 판매량에 맞추어 스케일링
                avg_relative_pattern = sum(relative_pattern) / 12 if sum(relative_pattern) > 0 else 1.0
                scaling_factor = baseline_sales / avg_relative_pattern
                
                monthly_sales = [p * scaling_factor for p in relative_pattern]
                
            except Exception as e:
                logging.error(f"[LLM-RUN failed] Product: {prod.get('product_name')}, Error: {e}. Falling back to baseline.")
                monthly_sales = dryrun_baseline(prod)
        else:
            monthly_sales = dryrun_baseline(prod)

        # 결과 저장 (정수로 변환)
        final_sales = [max(0, int(round(m))) for m in monthly_sales]
        outputs.append({"product_name": prod.get("product_name"), **{MONTH_COLS[i]: final_sales[i] for i in range(12)}})

    # 최종 제출 파일 생성 (샘플 양식과 컬럼 순서 일치)
    df_sub = pd.DataFrame(outputs)[df_sample.columns]
    df_sub.to_csv(out_csv, index=False, encoding='utf-8')
    logging.info(f"✅ Submission file saved to -> {out_csv}")
    print("\n--- 최종 예측 결과 (상위 5개) ---"); print(df_sub.head())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM-based Product Demand Forecaster")
    parser.add_argument("--product_info", default="data/product_info.csv", help="Path to the product info CSV file.")
    parser.add_argument("--sample_submission", default="data/sample_submission.csv", help="Path to the sample submission CSV file.")
    parser.add_argument("--output", default="submission_result.csv", help="Path to save the output submission file.")
    parser.add_argument("--dry_run", action="store_true", help="Run without calling OpenAI API, using a baseline logic.")
    args = parser.parse_args()
    run(in_csv=args.product_info, out_csv=args.output, sample_csv=args.sample_submission, dry_run=args.dry_run)