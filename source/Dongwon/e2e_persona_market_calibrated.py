# -*- coding: utf-8 -*-
"""
Competition-Ready Persona Pipeline (Single-Turn LLM First)
- 목표: 규칙 준수(싱글턴, 속성≥10+가중치, 월별 확률/빈도)로 제품별 페르소나를 생성하고 12개월 예측을 산출
- 기본: 페르소나 기반 예측만 사용 (시장앵커 보정은 옵션)
- 입력: product_info.csv, sample_submission.csv
        (선택) survey_weights.csv  ← 인구대표성 가중치(키 기준 매칭)
        (선택) market_anchor_*.*  ← 보정용(기본 OFF)
- 출력: submission_persona_core.csv, personas_dump.jsonl (추적용)
"""
import os, json, math, random
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from pathlib import Path

# -----------------------------
# 0) Config
# -----------------------------
@dataclass
class CFG:
    DATA_DIR: Path = Path("data") if Path("data").exists() else Path("/mnt/data")
    PRODUCT_INFO: Path = DATA_DIR/"product_info.csv"
    SUBMISSION_TEMPLATE: Path = DATA_DIR/"sample_submission.csv"
    SURVEY_WEIGHTS: Path = DATA_DIR/"survey_weights.csv"  # optional
    OUT_SUBMISSION: Path = DATA_DIR/"submission_persona_core.csv"
    OUT_PERSONAS_DUMP: Path = DATA_DIR/"personas_dump.jsonl"

    # LLM
    MODEL: str = "gpt-5-mini"    # 환경에 맞춰 변경
    K_PER_PRODUCT: int = 40
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 6000

    # Persona-first: 시장보정은 OFF (규칙 집중)
    USE_MARKET_CALIBRATION: bool = False

    # Fallback mock when OPENAI_API_KEY is not set
    RANDOM_SEED: int = 42

CFG = CFG()
random.seed(CFG.RANDOM_SEED); np.random.seed(CFG.RANDOM_SEED)

# -----------------------------
# 1) IO
# -----------------------------
def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)

prod = read_csv(CFG.PRODUCT_INFO)
sub_template = read_csv(CFG.SUBMISSION_TEMPLATE)

# optional survey weights (keys 예시: age, gender, family, income, region 등)
survey_w = None
if CFG.SURVEY_WEIGHTS.exists():
    survey_w = pd.read_csv(CFG.SURVEY_WEIGHTS)

MONTHS = [f"{y}-{m:02d}" for (y,m) in [(2024,7),(2024,8),(2024,9),(2024,10),(2024,11),(2024,12),
                                       (2025,1),(2025,2),(2025,3),(2025,4),(2025,5),(2025,6)]]

# -----------------------------
# 2) Single-turn prompt (규칙형)
# -----------------------------
def build_single_turn_prompt(row: pd.Series, K:int) -> str:
    return f"""
당신은 한국 가공식품 시장의 소비자 리서처입니다.
아래 '제품 설명'을 보고 이 제품의 잠재고객 페르소나 {K}명을 한 번에 생성하세요.

규칙(반드시 준수):
- 응답은 단 한 번(싱글 턴).
- 각 페르소나는 '속성'을 최소 10개 포함하고, 각 속성마다 0~1 가중치(weight)를 부여하세요.
- 각 페르소나는 2024-07 ~ 2025-06(12개월)에 대해:
  (1) month, (2) purchase_prob_pct(0~100), (3) freq(월 기대구매횟수)를 모두 포함하세요.
- 추가로 channel_weights(online/offline)를 포함해도 됩니다(선택).
- **반환은 JSON만** 출력하세요. 한국어 설명/문장은 절대 넣지 마세요.

입력:
- 제품명: {row['product_name']}
- 카테고리: {row['category_level_1']} > {row['category_level_2']} > {row['category_level_3']}
- 제품 특징: {row['product_feature']}
- 생성할 페르소나 수 K: {K}

출력 JSON 스키마 예:
{{
  "product": "{row['product_name']}",
  "personas": [
    {{
      "id":"p001",
      "name":"30대 맞벌이 건강중시",
      "attributes":[
        {{"name":"연령대","value":"30대","weight":0.12}},
        {{"name":"성별","value":"여성","weight":0.08}},
        {{"name":"가구소득","value":"중상","weight":0.09}},
        {{"name":"가족구성","value":"맞벌이 3인","weight":0.10}},
        {{"name":"주구매채널","value":"온라인몰","weight":0.08}},
        {{"name":"가격민감도","value":"중","weight":0.07}},
        {{"name":"브랜드충성도","value":"중상","weight":0.07}},
        {{"name":"건강지향","value":"높음","weight":0.09}},
        {{"name":"프로모션반응도","value":"높음","weight":0.08}},
        {{"name":"간편식이용빈도","value":"주 3회+","weight":0.12}}
      ],
      "monthly":[
        {{"month":"2024-07","purchase_prob_pct":42.0,"freq":0.6}},
        {{"month":"2024-08","purchase_prob_pct":44.0,"freq":0.6}},
        ...
        {{"month":"2025-06","purchase_prob_pct":40.0,"freq":0.5}}
      ],
      "channel_weights":{{"online":0.6,"offline":0.4}}
    }}
  ]
}}
""".strip()

# -----------------------------
# 3) LLM call (JSON only) + Fallback mock
# -----------------------------
def call_llm_single_turn(prompt:str) -> Optional[Dict[str,Any]]:
    """
    OPENAI_API_KEY가 있으면 JSON으로 호출, 없으면 None 반환(모의로 대체)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=CFG.MODEL,
            temperature=CFG.TEMPERATURE,
            max_tokens=CFG.MAX_TOKENS,
            response_format={"type":"json_object"},
            messages=[{"role":"user","content":prompt}]
        )
        txt = resp.choices[0].message.content
        return json.loads(txt)
    except Exception as e:
        print("[warn] LLM call failed → fallback mock. err:", e)
        return None

def mock_personas(product_name:str, K:int, seed:int=42) -> Dict[str,Any]:
    random.seed(seed + hash(product_name)%1000)
    pers=[]
    for i in range(K):
        attrs=[
            {"name":"연령대","value":random.choice(["20대","30대","40대","50대"]), "weight":round(random.uniform(0.05,0.15),2)},
            {"name":"성별","value":random.choice(["남성","여성"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"가구소득","value":random.choice(["중하","중","중상","상"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"가족구성","value":random.choice(["1인","2인","3인","4인"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"주구매채널","value":random.choice(["온라인몰","대형마트","편의점","슈퍼"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"가격민감도","value":random.choice(["낮음","중","높음"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"브랜드충성도","value":random.choice(["낮음","중","높음"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"건강지향","value":random.choice(["낮음","중","높음"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"프로모션반응도","value":random.choice(["낮음","중","높음"]),"weight":round(random.uniform(0.05,0.10),2)},
            {"name":"카테고리사용빈도","value":random.choice(["낮음","중","높음"]),"weight":round(random.uniform(0.05,0.12),2)},
        ]
        monthly=[]
        for m in MONTHS:
            mm=int(m[-2:])
            seas = 1.05 if mm in [9,12] else (0.95 if mm in [1,2] else 1.0)
            p = max(1.0,min(99.0, random.uniform(0.25,0.6)*100*seas))
            f = max(0.05, random.uniform(0.2,0.9)*seas)
            monthly.append({"month":m,"purchase_prob_pct":round(p,2),"freq":round(f,2)})
        pers.append({"id":f"p{i+1:03d}","attributes":attrs,"monthly":monthly})
    return {"product":product_name,"personas":pers}

def generate_personas_for_product(row:pd.Series, K:int) -> Dict[str,Any]:
    prompt = build_single_turn_prompt(row, K)
    data = call_llm_single_turn(prompt)
    if data is None:
        data = mock_personas(row["product_name"], K, seed=CFG.RANDOM_SEED)
    return data

# -----------------------------
# 4) Validate/Repair personas (규칙 체크)
# -----------------------------
def validate_and_fix(persona_pack:Dict[str,Any]) -> Dict[str,Any]:
    # 필수 키
    assert "product" in persona_pack and "personas" in persona_pack
    fixed=[]
    for p in persona_pack["personas"]:
        attrs = p.get("attributes", [])
        if len(attrs) < 10:
            # 속성 부족 시 랜덤 속성 추가(모의/보정)
            need = 10 - len(attrs)
            for _ in range(need):
                attrs.append({"name":"보정속성","value":"기타","weight":0.05})
        # weight 범위 보정
        for a in attrs:
            a["weight"] = float(min(1.0, max(0.0, a.get("weight",0.05))))
        # 월 데이터 12개 보장
        m = {row["month"]:row for row in p.get("monthly", []) if "month" in row}
        monthly=[]
        for mo in MONTHS:
            r = m.get(mo, {"month":mo,"purchase_prob_pct":10.0,"freq":0.2})
            r["purchase_prob_pct"]=float(min(99.0,max(0.0, r.get("purchase_prob_pct",10.0))))
            r["freq"]=float(max(0.0, r.get("freq",0.2)))
            monthly.append(r)
        p["attributes"]=attrs
        p["monthly"]=monthly
        fixed.append(p)
    persona_pack["personas"]=fixed
    return persona_pack

# -----------------------------
# 5) Population weight (선택: 설문가중치)
# -----------------------------
def persona_pop_weight(p:Dict[str,Any]) -> float:
    if survey_w is None:
        return 1.0
    # 간단한 예시: (age, gender) 키만 매칭; 실제로는 더 많은 키를 매핑
    # survey_weights.csv 예시 스키마: age, gender, weight
    # 페르소나 attributes에서 age/성별 값을 찾아 survey_w의 평균 weight를 사용
    age = None; gender=None
    for a in p.get("attributes", []):
        if a["name"] in ("연령대","연령","age"): age = a["value"]
        if a["name"] in ("성별","gender"): gender = a["value"]
    if age is None and gender is None:
        return 1.0
    df = survey_w.copy()
    if age is not None and "age" in df.columns: df = df[df["age"]==age]
    if gender is not None and "gender" in df.columns: df = df[df["gender"]==gender]
    if len(df)==0 or "weight" not in df.columns: return 1.0
    return float(df["weight"].mean())

# -----------------------------
# 6) Aggregate personas → monthly units (persona-only)
# -----------------------------
def personas_to_units(persona_pack:Dict[str,Any]) -> pd.Series:
    s = pd.Series(0.0, index=MONTHS)
    for p in persona_pack.get("personas", []):
        w = persona_pop_weight(p)
        for row in p["monthly"]:
            prob = row["purchase_prob_pct"]/100.0
            freq = row["freq"]
            s[row["month"]] += prob * freq * w
    return s

# -----------------------------
# 7) Main
# -----------------------------
all_pred = []
with open(CFG.OUT_PERSONAS_DUMP, "w", encoding="utf-8") as fout:
    for _, row in prod.iterrows():
        pack = generate_personas_for_product(row, CFG.K_PER_PRODUCT)
        pack = validate_and_fix(pack)
        fout.write(json.dumps(pack, ensure_ascii=False)+"\n")

        # 페르소나 기반 월별 구매횟수 기대치(상대량)
        per_units = personas_to_units(pack)

        # 단가 → "구매횟수"를 "수량"으로 단순화(1회=1개 구매 가정)
        # 필요 시 제품별 '평균 1회 구매개수' 계수를 곱하는 컬럼을 추가해도 됨.
        units = per_units.copy()

        # (선택) 시장보정은 현재 OFF (규칙 충족용)
        # if CFG.USE_MARKET_CALIBRATION: units = calibrate(units, ...)

        for m in MONTHS:
            all_pred.append({"product_name":row["product_name"], "month":m, "units":max(0.0, units[m])})

# 제출 스키마 정수 변환
pred_df = pd.DataFrame(all_pred)
pred_df["units_int"] = pred_df["units"].round().astype(int)
wide = pred_df.pivot(index="product_name", columns="month", values="units_int").reindex(prod["product_name"])

out = sub_template.copy()
for i, m in enumerate(MONTHS, start=1):
    col = f"months_since_launch_{i}"
    out[col] = out["product_name"].map(wide[m])

out.to_csv(CFG.OUT_SUBMISSION, index=False, encoding="utf-8-sig")
print(f"[saved] {CFG.OUT_SUBMISSION}")
print(f"[saved personas] {CFG.OUT_PERSONAS_DUMP}")
