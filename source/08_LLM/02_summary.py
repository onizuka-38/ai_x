import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

## 웹 예제
def askGpt(prompt):
    "GPT에게 prompt요청 결과 반환"
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role":"system", 
             "content":"당신은 한국어로 된 텍스트를 잘 요약하는 전문 어시스턴트입니다."
            },
            {"role":"user", "content":prompt}
        ]
    )
    return response.choices[0].message.content

# 기능 구현
# def main():
#     result = askGpt("""
#                     아래의 글을 30자 이내로 요약해주세요. 아래 형식으로 출력해주세요:
#                     요약: ...
#                     키워드: ...
#                     텍스트 : 먼게놈 프로젝트로 인간 유전체 염기서열이 지도화된 지 20년이 지났지만
#                     유전체의 상당 부분은 아직도 미스터리로 남아있다.
#                     DNA 염기서열은 약간만 달라져도 유전질환에 걸릴 수도 있고 환경에 대한 적응력도 바뀐다.
#                     DNA 염기서열을 분자 수준에서 정확히 해독하면 유전자에 어떤 변이가 일어났을 때 
#                     어떤 생물학적 변화가 생기는지 이해할 수 있게 된다.  국제학술지 네이처에 따르면 딥마인드는
#                     25일(현지시간) 공식 홈페이지에 염기서열 분석 AI 모델 '알파게놈'을 공개했다.
#                     알파게놈은 DNA 염기서열을 포괄적으로 처리해 총체적으로 이해하는 게 목표다.
#                     """)
#     print(result)
    
def main():
    st.header("요약 프로그램")
    st.markdown("---")
    text = st.text_area("요약할 글을 입력하세요")
    
    if st.button("요약"):
        with st.spinner("GPT가 요약 중..."):
            prompt = f"""your task is to summarize the text sentences in Korean language.
                    Summarize in 3 lines. use the format of a bullet point.
                    text : {text}"""
            result = askGpt(prompt=prompt)
            st.info(result)
    
if __name__ == "__main__":
    main()