import streamlit as st
import openai
import os
import requests
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_description_and_keyword(question):
    system_prompt = """
    사용자의 질문에 대해 친절한 설명을 제공하고,
    그 질문에서 핵심 이미지를 대표할 수 있는 단어 하나만 골라주세요.

    아래 형식으로 출력해주세요:
    설명: ...
    키워드: ...
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content
    lines = content.strip().split('\n')
    설명 = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("설명:")), "")
    키워드 = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("키워드:")), "")
    return 설명, 키워드

# 🎨 이미지 생성 (OpenAI >= 1.0 방식)
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_image_from_keyword(keyword):
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"Realistic image of {keyword}",
        size="512x512",
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    return image_url

# 🚀 Streamlit 앱 시작
st.set_page_config(page_title="GPT 이미지 생성기")
st.title("🧠 질문하면 이미지와 설명을 보여드려요!")
st.markdown("예: `사과란 무엇인가요?`, `고양이에 대해 알려줘`")

user_question = st.text_input("질문을 입력하세요:")

if st.button("생성하기") and user_question:
    with st.spinner("GPT가 생각 중..."):
        설명, 키워드 = get_description_and_keyword(user_question)
        image_url = get_image_from_keyword(keyword=키워드)

    st.subheader("📘 GPT 설명")
    st.write(설명)

    st.subheader(f"🖼️ 생성된 이미지: {키워드}")
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    st.image(img, caption=f"{keyword} 이미지", use_column_width=True)
