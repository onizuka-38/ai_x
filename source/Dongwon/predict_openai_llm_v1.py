# -*- coding: utf-8 -*-
"""
predict_openai_llm_v1.py  (zero-arg friendly, conservative v15)

그냥 아래만 치면 동작:
    python predict_openai_llm_v1.py

v15 변경점:
- '덴마크 하이그릭' 앵커 3.33억/월 → **1.2억/월**로 하향 (단일 400g SKU 보수화)
- v14의 보수화 로직 유지: 서브라인 시즌 감쇠, 마케팅 승수 캡, LLM lift 0.9~1.1

필요:
- pip install --upgrade openai pandas tenacity python-dotenv
- 환경변수 OPENAI_API_KEY
- product_info.csv, sample_submission.csv (현재 폴더 또는 data/, dataset/)
"""
from __future__ import annotations
import os, sys, json, time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import statistics
import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
# .env 자동 로드 (있으면)
# ──────────────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ──────────────────────────────────────────────────────────────────────────────
# OpenAI client
# ──────────────────────────────────────────────────────────────────────────────
try:
    from openai import OpenAI
    _OPENAI_NEW = True
except Exception:
    _OPENAI_NEW = False
    import openai  # type: ignore

# ──────────────────────────────────────────────────────────────────────────────
# Zero-arg defaults
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_N_SAMPLES = int(os.getenv("N_SAMPLES", "6"))
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", "1.0"))
DEFAULT_MODE = os.getenv("LLM_MODE", "function")  # "function" | "json"

def _resolve_path(cands: list[str]) -> Path | None:
    for c in cands:
        p = Path(c)
        if p.exists():
            return p
    return None

PI_PATH = _resolve_path(["product_info.csv", "data/product_info.csv", "dataset/product_info.csv"])
SS_PATH = _resolve_path(["sample_submission.csv", "data/sample_submission.csv", "dataset/sample_submission.csv"])
OUT_PATH = Path("submission_openai_llm.csv")
DBG_PATH = Path("debug_openai_llm.csv")

# =========================
# 1) Forecast primitives (conservative v15)
# =========================
CALIBRATED_REVENUE_ANCHORS = {
    "덴마크 하이그릭": 270_000_000,   # ↓ 3.33억 → 1.2억 (단일 400g SKU 보수화)
    "동원맛참": 900_000_000,         # v14 유지 (서브라인)
    "동원참치액": 300_000_000,
    "리챔 오믈레햄": 275_000_000,
    "소잘라떼": 140_000_000,
}
PRODUCT_LINE_DATA = {
    "덴마크 하이그릭요거트 400g": {"line": "덴마크 하이그릭", "line_share": 1.0},

    "동원맛참 고소참기름 135g": {"line": "동원맛참", "line_share": 0.30},
    "동원맛참 고소참기름 90g":  {"line": "동원맛참", "line_share": 0.20},
    "동원맛참 매콤참기름 135g": {"line": "동원맛참", "line_share": 0.30},
    "동원맛참 매콤참기름 90g":  {"line": "동원맛참", "line_share": 0.20},

    "동원참치액 순 500g":       {"line": "동원참치액", "line_share": 0.22},
    "동원참치액 순 900g":       {"line": "동원참치액", "line_share": 0.18},
    "동원참치액 진 500g":       {"line": "동원참치액", "line_share": 0.22},
    "동원참치액 진 900g":       {"line": "동원참치액", "line_share": 0.18},
    "프리미엄 동원참치액 500g": {"line": "동원참치액", "line_share": 0.12},
    "프리미엄 동원참치액 900g": {"line": "동원참치액", "line_share": 0.08},

    "리챔 오믈레햄 200g": {"line": "리챔 오믈레햄", "line_share": 0.60},
    "리챔 오믈레햄 340g": {"line": "리챔 오믈레햄", "line_share": 0.40},

    "소화가 잘되는 우유로 만든 바닐라라떼 250mL": {"line": "소잘라떼", "line_share": 0.50},
    "소화가 잘되는 우유로 만든 카페라떼 250mL":   {"line": "소잘라떼", "line_share": 0.50},
}
LINE_CATEGORY_MAP = {
    "덴마크 하이그릭": {"category": "발효유", "adoption_speed": "fast"},
    "동원맛참": {"category": "참치", "adoption_speed": "very_fast"},
    "동원참치액": {"category": "조미소스", "adoption_speed": "medium"},
    "리챔 오믈레햄": {"category": "축산캔", "adoption_speed": "slow"},
    "소잘라떼": {"category": "가공우유", "adoption_speed": "medium"},
}
# 시즌 영향 (v14 유지)
EVENT_FACTORS = {
    "참치":     {1: 1.4, 2: 1.4, 9: 1.5, 10: 1.15},
    "축산캔":   {1: 1.35, 2: 1.35, 9: 1.5, 10: 1.10},
    "조미소스": {1: 1.15, 9: 1.2, 10: 1.08},
    "발효유":   {7: 1.25, 8: 1.25, 9: 1.05},
    "가공우유": {7: 1.30, 8: 1.35, 9: 1.15},
}
ADOPTION_CURVES = {
    "very_fast": [1.25, 1.15, 0.95, 0.90, 0.90, 0.88, 0.88, 0.85, 0.85, 0.85, 0.85, 0.85],
    "fast":      [1.08, 1.12, 1.03, 0.98, 0.98, 0.96, 0.95, 0.95, 0.92, 0.92, 0.90, 0.90],
    "medium":    [0.98, 1.05, 1.05, 1.00, 0.98, 0.98, 0.95, 0.95, 0.92, 0.92, 0.90, 0.90],
    "slow":      [0.75, 0.85, 0.95, 1.00, 1.00, 0.98, 0.98, 0.98, 0.95, 0.92, 0.90, 0.90],
}
SEASON_LINE_SCALER = {"동원맛참": 0.7}  # 서브라인 시즌 감쇠

# 마케팅 승수 캡(보수화)
def get_marketing_multiplier(feature_text: str) -> float:
    if not isinstance(feature_text, str): return 1.0
    ft = feature_text.lower()
    hit = any(k in ft for k in ["tv","youtube","sns","엘리베이터","바이럴","광고모델"])
    return 1.10 if hit else 1.0  # capped

# ──────────────────────────────────────────────────────────────────────────────
# 2) Baseline forecast
# ──────────────────────────────────────────────────────────────────────────────
def parse_unit_price(s: str) -> int | None:
    if not isinstance(s, str): return None
    t = s.replace(",", "").replace("원","").strip()
    return int(t) if t.isdigit() else None

def get_line_and_share(product_name: str):
    info = PRODUCT_LINE_DATA.get(product_name)
    if info: return info["line"], info["line_share"]
    if "맛참" in product_name: return "동원맛참", 0.25
    if "참치액" in product_name: return "동원참치액", 1/6
    if "오믈레햄" in product_name: return "리챔 오믈레햄", 0.5
    if "라떼" in product_name: return "소잘라떼", 0.5
    if ("요거트" in product_name) or ("하이그릭" in product_name): return "덴마크 하이그릭", 1.0
    return None, None

def get_category_and_adoption(line: str):
    m = LINE_CATEGORY_MAP.get(line, {"category": "기타", "adoption_speed": "medium"})
    return m["category"], m["adoption_speed"]

def month_to_calendar(month_since_launch: int, start_month: int = 7) -> int:
    return (start_month + month_since_launch - 2) % 12 + 1

def baseline_forecast_for_product(prod: dict) -> Tuple[List[int], Dict[str, Any]]:
    name = prod["product_name"]
    feature = prod.get("product_feature", "")
    price = parse_unit_price(str(prod.get("1개 가격", ""))) or 2000
    line, share = get_line_and_share(name)
    if not line:
        line, share = "동원참치액", 1/6
    anchor = CALIBRATED_REVENUE_ANCHORS.get(line, 200_000_000)
    category, adoption_speed = get_category_and_adoption(line)
    adoption = ADOPTION_CURVES[adoption_speed]
    mk_mult = get_marketing_multiplier(feature)
    season_scale = SEASON_LINE_SCALER.get(line, 1.0)

    baseline_units = int((anchor * share) / price)
    months = []
    for m in range(1, 13):
        cal_m = month_to_calendar(m, 7)
        seasonal = EVENT_FACTORS.get(category, {}).get(cal_m, 1.0) * season_scale
        units = baseline_units * adoption[m-1] * seasonal * mk_mult
        months.append(max(int(round(units)), 0))
    ctx = {
        "line": line, "share": share, "category": category,
        "adoption_speed": adoption_speed, "baseline_units": baseline_units
    }
    return months, ctx

# ──────────────────────────────────────────────────────────────────────────────
# 3) LLM schema/prompts (lift 0.9~1.1)
# ──────────────────────────────────────────────────────────────────────────────
def _build_lift_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "lifts": {
                "type": "array",
                "minItems": 12, "maxItems": 12,
                "items": {"type": "number", "minimum": 0.9, "maximum": 1.1}
            },
            "notes": {"type": "string"}
        },
        "required": ["lifts"],
        "additionalProperties": False
    }

def _system_prompt() -> str:
    return (
        "You are a conservative Korean FMCG demand forecaster. "
        "Return only JSON and adhere strictly to the given schema. "
        "Bias toward realistic household purchase behavior and seasonality. "
        "Stay within [0.9, 1.1] lift range."
    )

def _user_prompt(product: dict, base_ctx: dict) -> str:
    name = product["product_name"]
    feature = product.get("product_feature", "N/A")
    price = product.get("1개 가격", "미정")
    line = base_ctx["line"]
    category = base_ctx["category"]
    adoption = base_ctx["adoption_speed"]
    return f"""
[Task]
Given the baseline forecast for the product below, output 12 monthly 'lift' multipliers within 0.9~1.1 (months=1..12 starting July). 
If uncertain, use 1.00, and only deviate for plausible events (ad resonance, novelty, school season).

[Product]
- Name: {name}
- Feature: {feature}
- Price(per unit): {price}
- Line: {line}, Category: {category}, Adoption: {adoption}

[Output]
{{"lifts":[n1,n2,...,n12], "notes":"...brief rationale..."}}"""

def _call_openai_for_lifts(model: str, temperature: float, mode: str, product: dict, base_ctx: dict) -> dict:
    schema = _build_lift_schema()
    system = _system_prompt()
    user = _user_prompt(product, base_ctx)
    if _OPENAI_NEW:
        client = OpenAI()
        if mode == "function":
            rsp = client.chat.completions.create(
                model=model, temperature=temperature,
                messages=[{"role":"system","content":system},
                          {"role":"user","content":user}],
                tools=[{"type":"function","function":{"name":"record_lifts","parameters":schema}}],
                tool_choice={"type":"function","function":{"name":"record_lifts"}},
            )
            tc = rsp.choices[0].message.tool_calls[0]
            return json.loads(tc.function.arguments)
        else:
            rsp = client.chat.completions.create(
                model=model, temperature=temperature,
                response_format={"type":"json_object"},
                messages=[{"role":"system","content":system},
                          {"role":"user","content":user}],
            )
            return json.loads(rsp.choices[0].message.content)
    else:
        rsp = openai.ChatCompletion.create(
            model=model, temperature=temperature,
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            functions=[{"name":"record_lifts","parameters":schema}],
            function_call={"name":"record_lifts"} if mode=="function" else "auto"
        )
        msg = rsp["choices"][0]["message"]
        if "function_call" in msg:
            return json.loads(msg["function_call"]["arguments"])
        return json.loads(msg["content"])

def _aggregate_lifts(samples: List[dict]) -> List[float]:
    cols = list(zip(*[s["lifts"] for s in samples if "lifts" in s]))
    return [float(round(statistics.median(col), 3)) for col in cols]

# ──────────────────────────────────────────────────────────────────────────────
# 4) Main
# ──────────────────────────────────────────────────────────────────────────────
def main():
    if PI_PATH is None or SS_PATH is None:
        print("[ERR] product_info.csv / sample_submission.csv 를 찾지 못했습니다. (현재폴더, data/, dataset/ 탐색)")
        sys.exit(1)
    if not os.getenv("OPENAI_API_KEY"):
        print("[ERR] OPENAI_API_KEY 가 설정되지 않았습니다.")
        sys.exit(1)

    print(f"[I] files: {PI_PATH.name}, {SS_PATH.name}")
    print(f"[I] model={DEFAULT_MODEL}, n_samples={DEFAULT_N_SAMPLES}, temp={DEFAULT_TEMPERATURE}, mode={DEFAULT_MODE}")

    pi = pd.read_csv(PI_PATH)
    ss = pd.read_csv(SS_PATH)

    pred_rows, dbg_rows = [], []
    for _, row in pi.iterrows():
        base_months, base_ctx = baseline_forecast_for_product(row.to_dict())
        samples = []
        for _ in range(DEFAULT_N_SAMPLES):
            payload = _call_openai_for_lifts(
                model=DEFAULT_MODEL,
                temperature=DEFAULT_TEMPERATURE,
                mode=DEFAULT_MODE,
                product=row.to_dict(),
                base_ctx=base_ctx
            )
            samples.append(payload)
            time.sleep(0.15)
        lifts = _aggregate_lifts(samples)
        final = [int(round(b*l)) for b, l in zip(base_months, lifts)]
        pred_rows.append({"product_name": row["product_name"], **{f"months_since_launch_{i+1}": v for i, v in enumerate(final)}})
        for mi, (b, lf, fv) in enumerate(zip(base_months, lifts, final), start=1):
            dbg_rows.append({"product_name": row["product_name"], "month_index": mi, "baseline_units": b, "lift_median": lf, "final_units": fv})

    pred_df = pd.DataFrame(pred_rows)
    out = ss[["product_name"]].merge(pred_df, on="product_name", how="left")
    for i in range(1, 13):
        col = f"months_since_launch_{i}"
        out[col] = out[col].fillna(0).astype(int)

    out.to_csv(OUT_PATH, index=False, encoding="utf-8")
    pd.DataFrame(dbg_rows).to_csv(DBG_PATH, index=False, encoding="utf-8")
    print(f"[OK] saved -> {OUT_PATH}")
    print(f"[DBG] saved -> {DBG_PATH}")

if __name__ == "__main__":
    main()
