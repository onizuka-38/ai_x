#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Final Forecast Runner
- Runs with no CLI args: `python run_forecast_final.py`
- Features:
  * Interview-style deterministic engine (persona × product)
  * Cooking-Need gating for 조미/참치액 계열
  * Seasonality (엑셀, 7→6월)
  * Advertising month mapping
  * Category market-share trend (2019.12~2025.03, 이미지값) -> 월별 shape 보정(평균=1 정규화)
  * Optional: market anchors & Dongwon share (market_anchors.xlsx)
  * Optional: segment×category single-turn OpenAI calibration (OPENAI_API_KEY)
"""

import os, re, json, math
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as np
import pandas as pd

# --------------------------- Paths (defaults) ---------------------------
ROOT = Path(__file__).resolve().parent
PRODUCT_INFO = ROOT / "product_info.csv"  # EUC-KR, TSV
WEIGHTS_XLSX = ROOT / "월별판매량가중치(7월부터 시작).xlsx"
PERSONAS_JSON = ROOT / "persona_core.json"
MARKET_ANCHORS = ROOT / "market_anchors_sample.xlsx"  # optional; if missing, skipped
COOKING_OVERRIDES = ROOT / "cooking_propensity_overrides_sample.csv"  # optional

OUT_CSV = ROOT / "forecast_final.csv"
OUT_LOG = ROOT / "forecast_final_logs.jsonl"

# --------------------------- Time axis ---------------------------
START = datetime(2024,7,1)
MONTHS = [START + relativedelta(months=i) for i in range(12)]
MONTH_KEYS = [(d.year, d.month) for d in MONTHS]
MONTH_COLS = [f"months_since_launch_{i+1}" for i in range(12)]

# --------------------------- IO ---------------------------
def read_product_info(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="euc-kr", sep="\t", engine="python")

def read_weights(path: Path) -> dict:
    xlsx = pd.ExcelFile(path)
    weights = {}
    for sheet in xlsx.sheet_names:
        df = xlsx.parse(sheet, header=None).dropna(how="all").reset_index(drop=True)
        if df.empty:
            continue
        df[0] = df[0].astype(str)
        mask = df[0].str.contains(r"20\d{2}")
        df = df[mask].copy()
        months = df.loc[:, 1:12].apply(pd.to_numeric, errors="coerce")
        vec = months.mean(axis=0).values
        vec = vec / np.nanmean(vec)  # 12개월 평균=1
        weights[sheet] = vec
    return weights

def read_personas(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --------------------------- Mapping ---------------------------
def map_product_to_sheet(row: pd.Series) -> str:
    name = str(row.get("product_name",""))
    c1 = str(row.get("category_level_1",""))
    c2 = str(row.get("category_level_2",""))
    c3 = str(row.get("category_level_3",""))
    if any(k in name for k in ["라떼","우유","RTD","카페"]):
        return "덴마크"
    if "참치" in name or "참치" in c2 or "참치" in c3:
        if "액" in name or "액상" in c3 or "액" in c3:
            return "참치액"
        return "참치캔"
    if "식육" in c1 or any(k in name for k in ["햄","리챔"]):
        return "식육가공품"
    if any(k in [c1,c2,c3] for k in ["발효유","유제품"]) or any(k in name for k in ["요거트","덴마크"]):
        return "덴마크"
    if "조미" in c1 or "조미" in c2 or "조미" in c3:
        return "참치액"
    return "참치캔"

FEATURE_KEYWORDS = {
    "premium": ["프리미엄","고급","유기농"],
    "health": ["건강","고단백","단백","저당","저지방","고칼슘"],
    "convenience": ["간편","즉석","간단","편의"],
    "value": ["가성비","대용량","할인"],
    "spicy": ["매콤","매운"],
    "savory": ["고소"],
}

def has_kw(txt: str, key: str) -> int:
    if not isinstance(txt, str):
        return 0
    return int(any(k in txt for k in FEATURE_KEYWORDS.get(key, [])))

# --------------------------- Parsers ---------------------------
def parse_ad_period(s: str):
    if not isinstance(s, str):
        return set(), None
    s = s.strip()
    if "광고" not in s and "바이럴" not in s:
        return set(), None
    active = set()
    m = re.search(r"(20\d{2})년\s*(\d{1,2})\s*-\s*(\d{1,2})\s*월", s)
    if m:
        y = int(m.group(1)); m1 = int(m.group(2)); m2 = int(m.group(3))
        for mm in range(m1, m2+1):
            active.add((y,mm))
    else:
        m2 = re.search(r"(20\d{2})년\s*(\d{1,2})\s*월", s)
        if m2:
            active.add((int(m2.group(1)), int(m2.group(2))))
    ad_type = "연예인" if "연예인" in s else ("바이럴" if "바이럴" in s else "광고")
    return active, ad_type

def monthly_ad_uplift_vector(persona: dict, s: str) -> np.ndarray:
    active, ad_type = parse_ad_period(s)
    base = np.ones(12, dtype=float)
    if not active:
        return base
    ori = persona.get("orientations", {})
    brand = ori.get("brand_loyalty", 5) / 10.0
    var = ori.get("variety_seeking", 5) / 10.0
    ad_sensitivity = 0.10 + 0.15 * brand + 0.05 * var   # 0.10 ~ 0.30
    type_mult = 1.2 if ad_type == "연예인" else (1.0 if ad_type == "바이럴" else 0.8)
    uplift = ad_sensitivity * type_mult  # ~0.08~0.36
    for i, (y,m) in enumerate(MONTH_KEYS):
        if (y,m) in active:
            base[i] *= (1.0 + uplift)
    return base

def monthly_freq_from_text(txt: str) -> float:
    if not isinstance(txt, str) or not txt.strip():
        return 2.0
    t = txt.strip()
    m = re.search(r"월\s*(\d+(?:\.\d+)?)\s*회", t)
    if m: return float(m.group(1))
    m = re.search(r"주\s*(\d+(?:\.\d+)?)\s*회", t)
    if m: return float(m.group(1)) * 4.345
    m = re.search(r"(\d+(?:\.\d+)?)\s*주일에\s*1회", t)
    if m: return 4.345 / float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*주에\s*1회", t)
    if m: return 4.345 / float(m.group(1))
    if "격주" in t: return 4.345 / 2.0
    m = re.search(r"주\s*(\d+)\s*[-~]\s*(\d+)\s*회", t)
    if m:
        lo, hi = map(float, m.groups())
        return ((lo + hi) / 2.0) * 4.345
    return 2.0

# --------------------------- Cooking-Need ---------------------------
def default_cooking_propensity(persona: dict) -> float:
    score = 0.5
    dem = persona.get("demographics", {})
    age = dem.get("age")
    hh = dem.get("household", "")
    try:
        age = int(age)
        if age >= 50: score += 0.05
        if 25 <= age <= 34: score -= 0.05
    except Exception:
        pass
    if isinstance(hh, str):
        if "1인" in hh: score -= 0.05
        if "3" in hh or "4" in hh: score += 0.05
    return float(np.clip(score, 0.0, 1.0))

def load_cooking_overrides_map(path: Path) -> dict:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    m = {}
    for _, r in df.iterrows():
        try:
            m[int(r["persona_id"])] = float(np.clip(float(r["cooking_propensity"]), 0.0, 1.0))
        except Exception:
            continue
    return m

# --------------------------- Market Share Trend (from image) ---------------------------
SHARE_SERIES = {
    "참치캔": {"2019-12":80.1,"2020-12":80.4,"2021-12":81.3,"2022-12":82.5,"2023-12":81.7,"2024-12":81.4,"2025-03":81.9},
    "캔햄": {"2019-12":18.1,"2020-12":20.0,"2021-12":19.3,"2022-12":19.0,"2023-12":19.2,"2024-12":19.9,"2025-03":18.5},
    "발효유": {"2019-12":14.1,"2020-12":12.2,"2021-12":13.3,"2022-12":12.2,"2023-12":11.5,"2024-12":12.4,"2025-03":11.8},
}
CAT_TO_SHARE_ROW = {"참치캔":"참치캔","식육가공품":"캔햄","덴마크":"발효유"}

def share_multiplier_vector(cat: str) -> np.ndarray:
    row = CAT_TO_SHARE_ROW.get(cat)
    if not row or row not in SHARE_SERIES:
        return np.ones(12, dtype=float)
    pts = SHARE_SERIES[row]
    def to_ord(ym):
        y, m = map(int, ym.split("-"))
        return y*12 + m
    keys = sorted(pts.keys())
    ords = np.array([to_ord(k) for k in keys], dtype=int)
    vals = np.array([pts[k] for k in keys], dtype=float)
    fk = np.array([to_ord(f"{y}-{m:02d}") for (y,m) in MONTH_KEYS], dtype=int)
    out = np.interp(fk, ords, vals, left=vals[0], right=vals[-1])
    return (out / out.mean()).astype(float)

# --------------------------- Core math ---------------------------
def category_affinity(persona: dict, row: pd.Series) -> float:
    top = " ".join(persona.get("shopping_profile", {}).get("top_categories", []))
    cat = " ".join([str(row.get("category_level_1","")), str(row.get("category_level_2","")), str(row.get("category_level_3","")), str(row.get("product_name",""))])
    score = 0.0
    score += 1.0 if ("참치" in top and "참치" in cat) else 0.0
    score += 1.0 if (any(k in top for k in ["발효유","요거트","유제품"]) and any(k in cat for k in ["요거트","발효유"])) else 0.0
    score += 1.0 if (any(k in top for k in ["조미","소스"]) and any(k in cat for k in ["조미","액상"])) else 0.0
    score += 1.0 if (any(k in top for k in ["식육","햄","축산"]) and any(k in cat for k in ["햄","식육","축산"])) else 0.0
    return score / 4.0

def persona_elasticity(persona: dict) -> float:
    ori = persona.get("orientations", {})
    ps = ori.get("price_sensitivity", 5) / 10.0
    pr = ori.get("premium", 5) / 10.0
    e = 0.2 + 1.2 * ps - 0.5 * pr
    return float(np.clip(e, 0.1, 1.2))

def interview_det(persona: dict, row: pd.Series, weights: dict, cat_median_price: dict, cooking_over_map: dict) -> tuple:
    ori = persona.get("orientations", {})
    pf = str(row.get("product_feature", ""))
    cat = row["seasonality_sheet"]

    P = ori.get("premium",5)/10.0
    H = ori.get("health",5)/10.0
    C = ori.get("convenience",5)/10.0
    V = max(0, 1 - ori.get("price_sensitivity",5)/10.0)
    Var = ori.get("variety_seeking",5)/10.0
    spicy = has_kw(pf, "spicy")
    savory = has_kw(pf, "savory")
    premium = has_kw(pf, "premium")
    health = has_kw(pf, "health")
    value = has_kw(pf, "value")
    conv = has_kw(pf, "convenience")
    taste_align = 0.15*Var*spicy + 0.12*H*health + 0.12*P*premium + 0.15*C*conv + 0.12*V*value + 0.08*savory
    taste_align = float(np.clip(taste_align, 0, 1))

    cat_aff = category_affinity(persona, row)

    persona_id = persona.get("persona_id")
    cook_prop = cooking_over_map.get(persona_id, default_cooking_propensity(persona))
    cook_gate = 1.0
    if cat in {"참치액"}:
        cook_gate = 0.2 + 0.8 * cook_prop

    base_prob = 0.12 + 0.45*cat_aff + 0.40*taste_align + 0.22*(ori.get("brand_loyalty",5)/10.0)
    base_prob *= cook_gate
    base_prob = float(np.clip(base_prob, 0, 0.95))

    month_freq = monthly_freq_from_text(persona.get("shopping_profile",{}).get("purchase_cycle",""))

    price = float(row.get("price", math.nan))
    med = float(cat_median_price.get(cat, price if not (price!=price) else 1.0))
    price_index = (price/med) if (price and med>0) else 1.0
    e = persona_elasticity(persona)
    price_mult = price_index ** (-e)

    ad_vec = monthly_ad_uplift_vector(persona, str(row.get("advertising","")))

    w = weights.get(cat, np.ones(12))
    w = w / np.mean(w)
    share_vec = share_multiplier_vector(cat)

    monthly_units = month_freq * base_prob * price_mult * ad_vec * w * share_vec

    answers = {
        "cat_affinity": round(cat_aff,3),
        "taste_alignment": round(taste_align,3),
        "cook_propensity": round(cook_prop,3),
        "cook_gate": round(cook_gate,3),
        "price_index": round(price_index,3),
        "elasticity": round(e,3),
        "base_prob": round(base_prob,3),
        "monthly_freq": round(month_freq,3),
        "ad_months": [i+1 for i,(y,m) in enumerate(MONTH_KEYS) if ad_vec[i]>1.0],
        "share_row": {"참치캔":"참치캔","식육가공품":"캔햄","덴마크":"발효유"}.get(cat)
    }
    return answers, monthly_units

# --------------------------- LLM calibration (optional) ---------------------------
def llm_calibrate_segments(personas, product_df, use_llm=False, model="gpt-4o-mini"):
    if not use_llm:
        return {}
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[WARN] OPENAI_API_KEY not set; skipping LLM calibration.")
        return {}
    try:
        from openai import OpenAI
    except Exception:
        print("[WARN] openai package not available; `pip install openai` to enable. Skipping LLM.")
        return {}
    client = OpenAI(api_key=api_key)

    product_df["seasonality_sheet"] = product_df["seasonality_sheet"].astype(str)
    cats = sorted(product_df["seasonality_sheet"].unique().tolist())
    segs = sorted({int(p.get("segment_id", -1)) for p in personas if "segment_id" in p})

    seg_profiles = {}
    for sid in segs:
        group = [p for p in personas if p.get("segment_id")==sid]
        if not group: continue
        keys = ["health","price_sensitivity","hmr","brand_loyalty","premium","convenience","variety_seeking"]
        avg = {k: float(np.nanmean([g.get("orientations",{}).get(k, np.nan) for g in group])) for k in keys}
        seg_profiles[sid] = {"size": len(group), "avg_orientations": avg}

    results = {}
    for sid in segs:
        prof = seg_profiles.get(sid)
        if not prof: continue
        for cat in cats:
            system = "You are a Korean CPG demand researcher. Return ONLY a compact JSON with numeric multipliers in [0,2]. No prose."
            user = {
                "segment_id": sid,
                "segment_size": prof["size"],
                "avg_orientations": prof["avg_orientations"],
                "category": cat,
                "months": [f"{y}-{m:02d}" for (y,m) in MONTH_KEYS],
                "required_keys": ["cook_need_multiplier","category_affinity_multiplier",
                                  "ad_sensitivity_multiplier","price_elasticity_multiplier","base_prob_multiplier"]
            }
            prompt = json.dumps(user, ensure_ascii=False)
            try:
                resp = client.chat.completions.create(
                    model=model, temperature=0.2,
                    messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
                    response_format={"type":"json_object"}
                )
                obj = json.loads(resp.choices[0].message.content)
            except Exception as e:
                print(f"[LLM WARN] sid={sid}, cat={cat}: {e}")
                obj = {}
            def mul(k, d):
                try: return float(np.clip(float(obj.get(k,d)), 0.0, 2.0))
                except: return d
            results[(sid,cat)] = {
                "cook_need_multiplier": mul("cook_need_multiplier", 1.0),
                "category_affinity_multiplier": mul("category_affinity_multiplier", 1.0),
                "ad_sensitivity_multiplier": mul("ad_sensitivity_multiplier", 1.0),
                "price_elasticity_multiplier": mul("price_elasticity_multiplier", 1.0),
                "base_prob_multiplier": mul("base_prob_multiplier", 1.0),
            }
    return results

# --------------------------- Anchors (optional) ---------------------------
def apply_market_anchors(acc: dict, product_df: pd.DataFrame, anchors_path: Path):
    if not anchors_path.exists():
        return acc
    anchors = pd.read_excel(anchors_path)
    anchors.columns = [str(c) for c in anchors.columns]
    cat_targets = {}
    for _, r in anchors.iterrows():
        cat = str(r["category"])
        tgt = np.array([float(r[c]) for c in MONTH_COLS], dtype=float)  # assumed already 'market × dongwon_share'
        cat_targets[cat] = tgt

    product_df["_idx"] = range(len(product_df))
    for cat, g in product_df.groupby("seasonality_sheet"):
        names = g["product_name"].tolist()
        mat = np.stack([acc[n] for n in names])  # n x 12
        if cat not in cat_targets:
            continue
        col_sums = mat.sum(axis=0)
        tgt = cat_targets[cat]
        scale = np.ones(12, dtype=float)
        nonzero = col_sums > 0
        scale[nonzero] = np.divide(tgt[nonzero], col_sums[nonzero], out=np.ones_like(tgt[nonzero]), where=nonzero[nonzero])
        mat_scaled = mat * scale
        for i, n in enumerate(names):
            acc[n] = mat_scaled[i]
    return acc

# --------------------------- Main ---------------------------
def main():
    product_df = read_product_info(PRODUCT_INFO).copy()
    weights = read_weights(WEIGHTS_XLSX)
    personas = read_personas(PERSONAS_JSON)
    product_df["seasonality_sheet"] = product_df.apply(map_product_to_sheet, axis=1)

    cooking_over_map = load_cooking_overrides_map(COOKING_OVERRIDES) if COOKING_OVERRIDES.exists() else {}

    product_df["price"] = pd.to_numeric(product_df["price"], errors="coerce")
    cat_median_price = product_df.groupby("seasonality_sheet")["price"].median().to_dict()

    use_llm = bool(os.getenv("USE_LLM", "").strip())
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    seg_cat_muls = llm_calibrate_segments(personas, product_df, use_llm=use_llm, model=model)

    acc = {name: np.zeros(12, dtype=float) for name in product_df["product_name"]}
    with open(OUT_LOG, "w", encoding="utf-8") as fo:
        for persona in personas:
            sid = int(persona.get("segment_id", -1))
            for _, row in product_df.iterrows():
                answers, monthly_units = interview_det(persona, row, weights, cat_median_price, cooking_over_map)

                muls = seg_cat_muls.get((sid, row["seasonality_sheet"]), None)
                if muls:
                    monthly_units = monthly_units * float(muls.get("cook_need_multiplier", 1.0))
                    monthly_units = monthly_units * float(muls.get("category_affinity_multiplier", 1.0))
                    monthly_units = monthly_units * float(muls.get("base_prob_multiplier", 1.0))
                    ad_months = answers.get("ad_months", [])
                    if ad_months:
                        factor = float(muls.get("ad_sensitivity_multiplier", 1.0))
                        adj = np.ones(12, dtype=float)
                        for i in [m-1 for m in ad_months]: adj[i] *= factor
                        monthly_units = monthly_units * adj
                    pe_mul = float(muls.get("price_elasticity_multiplier", 1.0))
                    monthly_units = monthly_units ** (1.0 / max(1e-6, pe_mul))

                acc[row["product_name"]] += monthly_units

                fo.write(json.dumps({
                    "persona_id": persona.get("persona_id"),
                    "segment_id": sid,
                    "product_name": row["product_name"],
                    "seasonality_sheet": row["seasonality_sheet"],
                    "answers": answers,
                    "monthly_units": [round(float(x),6) for x in monthly_units.tolist()],
                }, ensure_ascii=False) + "\n")

    if MARKET_ANCHORS.exists():
        acc = apply_market_anchors(acc, product_df, MARKET_ANCHORS)

    rows = []
    for name in product_df["product_name"]:
        vec = acc[name]
        rows.append({"product_name": name, **{MONTH_COLS[i]: int(round(vec[i])) for i in range(12)}})
    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"[OK] Wrote: {OUT_CSV.name}")
    print(f"[LOG] Interview logs: {OUT_LOG.name}")
    print("[TIP] To enable LLM segment calibration, set USE_LLM=1 and OPENAI_API_KEY env vars.")

if __name__ == "__main__":
    main()
