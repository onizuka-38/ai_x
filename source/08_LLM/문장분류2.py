import os
import pandas as pd
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY"),
)

# ------------------------------------------------------------------
# [중요] 대회에 제출할 시스템 프롬프트를 이 곳에 작성하고 테스트하세요.
# ------------------------------------------------------------------
SYSTEM_PROMPT = """
[역할]
당신은 주어진 문장들을 '최우선 규칙'과 '세부 분류 기준'에 따라 기계적으로 분류하고, 지정된 '출력 형식'을 완벽하게 따르는 문장 분석 AI입니다.

[출력 형식]
- 입력된 문장 번호를 그대로 사용하여 한 줄에 하나씩 순서대로 출력합니다.
- 형식: `번호.유형,극성,시제,확실성`
- 쉼표(,) 앞뒤에 공백 없이, 주어진 한글 라벨만 정확히 사용합니다.
- 어떤 추가 설명이나 부가 기호도 절대 포함하지 마십시오.

[최우선 규칙 (가장 먼저, 반드시 적용할 것)]
- **극성 판단**: 문장에 `없다`, `않다`, `못하다` 라는 명시적, 문법적 부정어가 없으면, 문장의 내용이 아무리 부정적(예: 불만, 침해, 공황)이더라도 무조건 `긍정`으로 분류합니다. `없다` 가 있으면 `부정`입니다.
- **인용문 유형**: `"...라고 말했다"`, `"...라고 밝혔다"`, `"...라고 전했다"` 등으로 끝나면 유형은 `사실형`입니다.

[세부 분류 기준]
- **유형**
  - **사실형**: 객관적 사건, 정보, 현황, 인용 보도. '~라는 분석이다', '~라고 회고한다', '반응을 보였다' 처럼 분석이나 반응의 '전달'에 초점을 맞춘 문장.
  - **추론형**: 사실에 대한 해석, 평가, 의견, 주장(`~해야 한다`). 누군가의 감정(`기뻐했다`), 주관적 상태(`~는 위험하다`)를 서술.
  - **예측형**: 미래의 계획, 전망(`~할 것이다`, `~전망이다`).
  - **대화형**: 물음표(`?`)로 끝나거나, 직접 대화 형식(`~말입니다`).
- **시제**
  - **과거**: 명백한 과거 사건. `~해왔다`도 과거로 분류합니다.
  - **현재**: 현재 상태, 일반적인 사실.
  - **미래**: 아직 일어나지 않은 사건이나 행사 일정(`~하며 ~된다`)을 설명.
- **확실성**
  - **확실**: 확정된 사실.
  - **불확실**: 추측, 가정, 계획, 전망, 가능성(`~수 있다`).
- **특수 구문**: `~는 미지수다` 라는 문장은 `사실형,미정,미래,불확실`로 분류합니다.

[핵심 예시]
- **극성 규칙 예시**: `온라인 상에서도 소음과 교통 체증으로 인한 불만을 토로하는 게시글들이 잇따라 게재됐다.` → `사실형,긍정,과거,확실` (내용은 '불만'이지만, '없다'가 없으므로 '긍정')
- **극성 규칙 예시 2**: `비중 축소(Underweight)나 매도(Sell)를 제시한 애널리스트는 없다.` → `사실형,부정,현재,확실` ('없다'가 있으므로 '부정')
- **유형 규칙 예시**: `이에 효종은 ... 기뻐했다.` → `추론형,긍정,과거,확실` (감정 서술은 '추론형')
- **유형 규칙 예시 2**: `중국 정부의 ... 가능성이 높다는 분석이다.` → `사실형,긍정,현재,확실` ('분석이다'라는 분석 결과 전달은 '사실형')
- **시제 규칙 예시**: `9일 오후부터 ... 개발사가 선정된다.` → `사실형,긍정,미래,확실` (미래 행사 일정이므로 '미래')
"""
# ------------------------------------------------------------------

try:
    df = pd.read_csv("data/samples.csv")
except FileNotFoundError:
    print("❌ 오류: 'data/samples.csv' 파일을 찾을 수 없습니다. 스크립트와 같은 폴더에 'data' 폴더를 만들고 그 안에 'samples.csv'를 넣어주세요.")
    exit()

TEST_COUNT = 20
success = 0

# 1. 테스트 케이스 준비
test_indices = [random.randrange(len(df)) for _ in range(TEST_COUNT)]
prompts = [df.iloc[i]['user_prompt'] for i in test_indices]
answers = [f"{row['type']},{row['judgment']},{row['time']},{row['truth']}" for index, row in df.iloc[test_indices].iterrows()]

# 2. 하나의 입력으로 합치기
input_batch = "\n".join([f"{i+1}. {prompt}" for i, prompt in enumerate(prompts)])

print("--- AI에게 보낼 입력 (User Prompt) ---")
print(input_batch)
print("-------------------------------------\n")

# 3. AI에게 요청
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": input_batch}
    ],
    temperature=0.4
)

gpt_outputs = response.choices[0].message.content.strip().split('\n')

print("--- AI의 답변 ---")
print(response.choices[0].message.content)
print("-----------------\n")

# 4. 수정된 채점 로직
for i in range(TEST_COUNT):
    try:
        # [수정된 부분] 점(.)을 기준으로 나누도록 변경하여 공백 유무에 상관없이 작동합니다.
        gpt_answer = gpt_outputs[i].split('.', 1)[1].strip() # .strip()으로 만약의 공백도 제거
        correct_answer = answers[i]

        if gpt_answer == correct_answer:
            success += 1
        else:
            print(f"▼ {i+1}번 오답")
            print(f"  입력: {prompts[i]}")
            print(f"  정답: {correct_answer}")
            print(f"  AI답: {gpt_answer}\n")

    except IndexError:
        print(f"▼ {i+1}번 형식 오류 (AI가 답변을 생성하지 않았거나 형식이 다릅니다)")
        print(f"  AI가 출력한 줄: {gpt_outputs[i] if i < len(gpt_outputs) else '없음'}\n")

print(f"정답률: {success / TEST_COUNT * 100}% ({success}/{TEST_COUNT})")