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
당신은 주어진 문장들을 '최우선 절대 법칙'과 '세부 분류 기준'에 따라 기계적으로 분류하고, 지정된 '출력 형식'을 완벽하게 따르는 문장 분석 AI입니다. 일반적인 언어 상식보다 아래 규칙을 최우선으로 적용해야 합니다.

[출력 형식]
- 입력된 문장 번호를 그대로 사용하여 한 줄에 하나씩 순서대로 출력합니다.
- 형식: `번호.유형,극성,시제,확실성`
- 쉼표(,) 앞뒤에 공백 없이, 주어진 한글 라벨만 정확히 사용합니다.
- 어떤 추가 설명이나 부가 기호도 절대 포함하지 마십시오.

[최우선 절대 법칙 (Golden Rules)]
1.  **극성 판단이 모든 것에 우선한다**: 문장에 `없다`, `않다`, `못하다`, `못했다`, `거부했다` 라는 명시적, 문법적 부정어가 있으면 **무조건 `부정`**입니다. 여기에 해당하지 않으면 대부분 `긍정`입니다.
2.  **유형과 시제는 '마지막 동사'가 기준이다**: 문장 전체의 가장 마지막 서술어(main verb)를 기준으로 유형과 시제를 판단합니다. 인용문이나 부속절의 내용에 절대 현혹되지 마십시오.

[세부 분류 기준]
- **유형**
  - **사실형**: 객관적 사건, 정보, 현황, 인용 보도.
  - **추론형**: 사실에 대한 해석, 평가, 의견, 주장(`~해야 한다`). 정부나 기관의 내부적 과정(`고심 중이다`)을 서술하는 경우.
- **시제**
  - **과거**: 명백한 과거 사건.
  - **현재**: 현재 상태, 일반적인 사실. 과거 사건이라도 마지막 동사가 현재형(`~파면당한다`)이면 `현재`입니다.
  - **미래**: 아직 일어나지 않은 사건. `~할 수 있다`(가능성), `~를 앞두고 있다`(임박) 구문은 `미래`로 판단합니다.
- **확실성**
  - **확실**: 확정된 사실.
  - **불확실**: 추측, 가정, 계획, 전망. 과거에 대한 추측(`~했을 것`)도 `불확실`에 포함됩니다.

[핵심 예시 (틀리기 쉬운 유형)]
- **극성 규칙 예시**: `도사견 같은 맹견이나 ... 암컷은 태울 수 없다.` → `사실형,부정,현재,확실` ('없다'가 있으므로 최우선 규칙에 따라 '부정')
- **시제 규칙 예시 (미래)**: `...글로벌 파이널 초대 우승자의 덱들을 만날 수 있다.` → `사실형,긍정,미래,확실` ('~할 수 있다'는 미래의 가능성이므로 '미래')
- **시제 규칙 예시 (현재)**: `...다시 메디치 가문의 일당독재가 시작되면서 마키아벨리는 파면당한다.` → `사실형,긍정,현재,확실` (과거 사건이지만, 마지막 동사가 현재형이므로 '현재')
- **확실성 규칙 예시**: `...목숨을 부지하기 힘들었을 것이기 때문이다.` → `추론형,긍정,과거,불확실` ('~했을 것'은 과거에 대한 추측이므로 '불확실')
- **유형 규칙 예시**: `...정부는 고심 중이다.` → `추론형,긍정,현재,확실` (정부의 내부적 과정을 서술하므로 '추론형')
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