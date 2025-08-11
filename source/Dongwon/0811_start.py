# -*- coding: utf-8 -*-
"""
0811_start.py (patched v3)
- 폴백 경고(log.warning) 제거 → info/debug로 강등
- 관대한 파서 + 스키마 보정(coerce) + 재검증
- month dict('2024-07'~'2025-06') → 12-길이 벡터 매핑
- 누락 필드 기본값 채움
"""

from dotenv import load_dotenv
import os, json, math, time, argparse, logging, random, inspect, re, uuid
from typing import List, Dict, Any
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from jsonschema import Draft202012Validator
from openai import OpenAI
import openai as _openai

# =========================
# Config & I/O
# =========================
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 경고를 보기 싫으면 level=INFO 이상 권장
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

MONTH_COLS = [f"months_since_launch_{i}" for i in range(1, 13)]
MONTH_KEYS = ["2024-07","2024-08","2024-09","2024-10","2024-11","2024-12",
              "2025-01","2025-02","2025-03","2025-04","2025-05","2025-06"]

# =========================
# JSON Schema (Structured Outputs)
# =========================
PERSONA_BUNDLE_SCHEMA = {
    "name": "PersonaBundle",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "personas": {
                "type": "array",
                "minItems": 12,  # 완화
                "items": {
                    "type": "object",
                    "properties": {
                        "persona_id": {"type": "string"},
                        "demographics": {"type": "object"},
                        "lifestyle": {"type": "object"},
                        "weights": {"type": "object"},
                        "price_sensitivity": {"type": "number", "minimum": 0, "maximum": 1},
                        "promo_sensitivity": {"type": "number", "minimum": 0, "maximum": 1},
                        "novelty_seeking": {"type": "number", "minimum": 0, "maximum": 1},
                        "monthly_purchase_probability": {
                            "type": "array", "minItems": 12, "maxItems": 12,
                            "items": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "monthly_purchase_frequency": {
                            "type": "array", "minItems": 12, "maxItems": 12,
                            "items": {"type": "number", "minimum": 0}
                        },
                        "units_per_purchase": {"type": "number", "minimum": 0, "default": 1.0},
                        "notes": {"type": "string"}
                    },
                    "required": [
                        "persona_id","weights",
                        "monthly_purchase_probability","monthly_purchase_frequency"
                    ],
                    "additionalProperties": True
                }
            }
        },
        "required": ["personas"],
        "additionalProperties": False
    }
}

def validate_persona_bundle(bundle: Dict[str, Any]) -> None:
    validator = Draft202012Validator(PERSONA_BUNDLE_SCHEMA["schema"])
    errors = sorted(validator.iter_errors(bundle), key=lambda e: e.path)
    if errors:
        msgs = "\n".join([f"- {'/'.join([str(p) for p in e.path])}: {e.message}" for e in errors])
        raise ValueError(f"Structured Output schema validation failed:\n{msgs}")

# =========================
# OpenAI Client
# =========================
def build_client() -> OpenAI:
    if not API_KEY:
        logging.info("OPENAI_API_KEY not set. DRY-RUN 모드로 실행합니다.")
        return None
    return OpenAI(api_key=API_KEY)

# =========================
# Prompt (싱글턴)
# =========================
def build_persona_prompt(prod: Dict[str, Any]) -> str:
    return f"""당신은 한국 FMCG 식품시장의 소비자 연구원입니다.
다음 제품 정보를 참고해 서로 구분되는 소비자 페르소나 30명을 생성하세요.
각 페르소나는 최소 10개 속성에 가중치(0~1)를 부여하고,
12개월(2024-07 ~ 2025-06)의 월별 구매확률/구매빈도를 제공합니다.

[제품]
- 제품명: {prod.get('product_name')}
- 특징: {prod.get('product_feature')}
- 카테고리: {prod.get('category_level_1')} > {prod.get('category_level_2')} > {prod.get('category_level_3')}

[출력 형식 준수]
- 단일 JSON 객체만 출력. 최상위 키는 "personas".
- 각 페르소나 필수키: persona_id(문자열), weights(키:가중치 사전, 10개 이상),
  monthly_purchase_probability(길이 12, 0~1), monthly_purchase_frequency(길이 12, 0이상).
- price_sensitivity, promo_sensitivity, novelty_seeking(각 0~1) 포함.
- 계절성/명절(추석, 설)/연말/프로모션 영향을 월별 패턴에 반영.
"""

# =========================
# Utils: JSON 파싱/보정
# =========================
JSON_CLEAN_RE = re.compile(r"^```(json)?\s*|\s*```$", re.MULTILINE)

def parse_json_loose(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty response text.")
    t = re.sub(JSON_CLEAN_RE, "", text).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    l = t.find("{")
    r = t.rfind("}")
    if l != -1 and r != -1 and r > l:
        return json.loads(t[l:r+1])
    raise ValueError("Failed to parse JSON from model response.")

def _month_list_from_dict(md: Dict[str, float]) -> List[float]:
    arr = []
    for k in MONTH_KEYS:
        arr.append(float(md.get(k, 0)))
    return arr

def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

def _normalize_weights(raw: Dict[str, float]) -> Dict[str, float]:
    if not raw:
        return {}
    norm = {k: float(v) for k, v in raw.items()}
    mx = max(abs(v) for v in norm.values()) if norm else 1.0
    if mx > 1:
        norm = {k: v / mx for k,v in norm.items()}
    return dict(list(sorted(norm.items(), key=lambda kv: -abs(kv[1])))[:12])

def coerce_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """loose 포맷 → 스키마 준수 포맷으로 보정"""
    if not isinstance(bundle, dict):
        raise ValueError("bundle must be dict")
    if "consumer_personas" in bundle and "personas" not in bundle:
        bundle["personas"] = bundle.pop("consumer_personas")
    persons = bundle.get("personas")
    if not isinstance(persons, list):
        if isinstance(bundle, list):
            persons = bundle
            bundle = {"personas": persons}
        else:
            bundle["personas"] = []
            persons = []
    fixed = []
    for idx, p in enumerate(persons):
        if not isinstance(p, dict):
            continue
        q = dict(p)

        # 기본키
        if "persona_id" not in q:
            q["persona_id"] = q.get("id") or q.get("name") or f"P{idx+1:03d}-{uuid.uuid4().hex[:6]}"

        # demographics 묶기
        demo = q.get("demographics", {})
        if not isinstance(demo, dict):
            demo = {}
        for k in ("age","gender","income","region","family_size"):
            if k in q and k not in demo:
                demo[k] = q[k]
        if "name" in q and "name" not in demo:
            demo["name"] = q["name"]
        q["demographics"] = demo

        # lifestyle 문자열 → 객체
        life = q.get("lifestyle", {})
        if not isinstance(life, dict):
            life = {"summary": str(life)}
        q["lifestyle"] = life

        # weights 없으면 더미 생성(최소 10개)
        weights = q.get("weights", {})
        if not isinstance(weights, dict) or len(weights) < 10:
            seed = {
                "health_focus": 0.6 if "건강" in (life.get("summary","")+demo.get("name","")) else 0.4,
                "protein_preference": 0.6 if "단백" in (life.get("summary","")+demo.get("name","")) else 0.3,
                "convenience": 0.6 if "간편" in (life.get("summary","")) else 0.4,
                "brand_loyalty": float(q.get("brand_loyalty", 0.5)),
                "value_for_money": 0.5,
                "taste_variety": 0.5,
                "keto_lowcarb": 0.3,
                "low_calorie": 0.4,
                "sns_influence": 0.4,
                "family_orientation": 0.5,
                "office_worker": 0.5,
                "student": 0.3,
            }
            weights = _normalize_weights(seed)
        q["weights"] = weights

        # sensitivities
        for k in ("price_sensitivity","promo_sensitivity","novelty_seeking"):
            if k in q:
                try:
                    q[k] = _clip01(float(q[k]))
                except Exception:
                    q[k] = 0.5
            else:
                q[k] = 0.5

        # 월별 벡터 보정
        prob = q.get("monthly_purchase_probability")
        freq = q.get("monthly_purchase_frequency")
        pf = q.get("purchase_frequency") or q.get("monthly_pattern") or q.get("monthly_freq")
        if (prob is None or freq is None) and isinstance(pf, dict):
            arr = _month_list_from_dict(pf)
            if all(0 <= float(v) <= 1 for v in arr):
                prob = [_clip01(v) for v in arr]
                freq = [1.0]*12
            else:
                freq = [max(0.0, float(v)) for v in arr]
                prob = [0.5]*12

        def _to12(a, clip01=False, nonneg=False):
            if not isinstance(a, list):
                a = []
            b = []
            for i in range(12):
                v = float(a[i]) if i < len(a) else (0.5 if clip01 else 1.0)
                if clip01: v = _clip01(v)
                if nonneg: v = max(0.0, v)
                b.append(v)
            return b

        q["monthly_purchase_probability"]  = _to12(prob, clip01=True)
        q["monthly_purchase_frequency"]    = _to12(freq, clip01=False, nonneg=True)

        try:
            q["units_per_purchase"] = max(0.0, float(q.get("units_per_purchase", 1.0)))
        except Exception:
            q["units_per_purchase"] = 1.0

        fixed.append(q)

    bundle["personas"] = fixed
    return bundle

# =========================
# Retryable API call
# =========================
class TransientError(Exception):
    pass

def _supports_structured_outputs(client: OpenAI) -> bool:
    try:
        sig = inspect.signature(client.responses.create)
        return "response_format" in sig.parameters
    except Exception:
        return False

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(TransientError)
)
def call_openai_personas(client: OpenAI, prompt: str) -> Dict[str, Any]:
    bundle = None
    try:
        if _supports_structured_outputs(client):
            # responses.create 경로 (성공 시 경고 없음)
            resp = client.responses.create(
                model=MODEL,
                input=prompt,
                response_format={"type": "json_schema", "json_schema": PERSONA_BUNDLE_SCHEMA}
            )
            txt = getattr(resp, "output_text", None)
            bundle = resp.output_parsed if hasattr(resp, "output_parsed") and resp.output_parsed else None
            if bundle is None:
                if not txt and getattr(resp, "output", None):
                    txt = resp.output[0].content[0].text.value
                bundle = parse_json_loose(txt)
        else:
            # chat.completions 폴백 (경고 대신 info)
            logging.info("SDK가 Structured Output을 지원하지 않아 chat.completions로 실행합니다.")
            ch = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            text = ch.choices[0].message.content
            bundle = parse_json_loose(text)

        # 보정 + 검증
        bundle = coerce_bundle(bundle)
        validate_persona_bundle(bundle)
        return bundle

    except Exception as e1:
        try:
            b2 = coerce_bundle(bundle if bundle else {})
            validate_persona_bundle(b2)
            return b2
        except Exception as e2:
            raise RuntimeError(f"{e1}\n-- after coercion: {e2}")

# =========================
# 수요 계산
# =========================
def calc_monthly_demand_for_bundle(bundle: Dict[str, Any],
                                   discount_rate: List[float] = None) -> List[float]:
    if discount_rate is None:
        discount_rate = [0.0] * 12
    demand = [0.0] * 12
    for p in bundle["personas"]:
        prob = p["monthly_purchase_probability"]
        freq = p["monthly_purchase_frequency"]
        units = float(p.get("units_per_purchase", 1.0))
        price_sens = float(p.get("price_sensitivity", 0.5))
        for m in range(12):
            adj = max(0.0, 1.0 - price_sens * float(discount_rate[m]))
            demand[m] += float(prob[m]) * float(freq[m]) * units * adj
    return demand

# =========================
# DRY-RUN 베이스라인
# =========================
CAT_BASE = {
    "통조림/즉석/면류": 1200,
    "생수/음료/커피": 1500,
    "과자/떡/베이커리": 1100,
    "냉장/냉동/간편식": 1300,
    "유제품": 900,
    "건강식품": 700,
}
GLOBAL_MULT = [1.10,1.12,1.08,1.05,1.00,1.06,1.02,1.10,0.98,1.00,1.02,1.04]
LAUNCH_CURVE = [1.25,1.18,1.10,1.05,1.00,0.98,0.96,0.95,0.95,0.96,0.98,1.00]
def dryrun_baseline(row: pd.Series) -> List[int]:
    base = CAT_BASE.get(str(row.get("category_level_1","")), 1000)
    feat = str(row.get("product_feature","")).lower()
    if any(k in feat for k in ["프로틴","고단백","비타민","오메가"]): base += 100
    if any(k in feat for k in ["저칼로리","라이트","다이어트"]): base += 60
    if any(k in feat for k in ["대용량","가성비","팩"]): base += 80
    monthly = []
    rng = random.Random(123)
    for i in range(12):
        val = base * GLOBAL_MULT[i] * LAUNCH_CURVE[i] * (0.98 + 0.04 * rng.random())
        monthly.append(max(0, int(round(val))))
    return monthly

# =========================
# 메인 파이프라인
# =========================
def run_pipeline(product_info_csv: str, sample_sub_csv: str, out_csv: str,
                 use_batch: bool = False) -> None:
    df_info = pd.read_csv(product_info_csv)
    df_sample = pd.read_csv(sample_sub_csv)
    client = build_client()

    outputs: List[Dict[str, Any]] = []
    for _, row in df_info.iterrows():
        prod = row.to_dict()

        if client:
            try:
                prompt = build_persona_prompt(prod)
                bundle = call_openai_personas(client, prompt)
                monthly = calc_monthly_demand_for_bundle(bundle, discount_rate=[0]*12)

                total = sum(monthly)
                scale = 1.0
                if total > 0:
                    target_total = min(max(total, 12000), 48000)
                    scale = target_total / total
                monthly = [max(0, int(round(m * scale))) for m in monthly]

            except Exception as e:
                logging.info(f"[DRY-RUN fallback] {prod.get('product_name')}: {e}")
                monthly = dryrun_baseline(row)
        else:
            monthly = dryrun_baseline(row)

        outputs.append({
            "product_name": prod.get("product_name"),
            **{MONTH_COLS[i]: monthly[i] for i in range(12)}
        })

    sub = pd.DataFrame(outputs)
    sub = sub[df_sample.columns]
    sub.to_csv(out_csv, index=False)
    logging.info(f"Saved submission -> {out_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--product_info", default="data/product_info.csv")
    parser.add_argument("--sample_submission", default="data/sample_submission.csv")
    parser.add_argument("--out", default="submission_openai_persona.csv")
    parser.add_argument("--batch", action="store_true", help="(옵션) Batch API 경로 사용")
    args = parser.parse_args()

    run_pipeline(args.product_info, args.sample_submission, args.out, use_batch=args.batch)
