# app.py
from flask import Flask, request, render_template
import requests
import os
import pandas as pd
from dotenv import load_dotenv
from konlpy.tag import Kkma
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from gensim.models import Word2Vec
import time

app = Flask(__name__)
load_dotenv()

def get_naver_kin(keyword, total_cnt=500):
    client_id = os.getenv("Client_ID")
    client_secret = os.getenv("Client_Secret")

    items_list = []
    for start in range(1, total_cnt + 1, 100):
        display = min(100, total_cnt - start + 1)
        url = f"https://openapi.naver.com/v1/search/kin.json?query={keyword}&display={display}&start={start}"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Error {res.status_code} at start={start}")
            continue
        items = res.json().get("items", [])
        for item in items:
            items_list.append(
                item.get('title', '').replace('<b>', '').replace('</b>', '') + ' ' +
                item.get('description', '').replace('<b>', '').replace('</b>', '')
            )
        time.sleep(0.5)

    return items_list

# === 형태소 분석 + 빈도 분석 + 워드클라우드 + Word2Vec ===
def analyze_texts(texts):
    kkma = Kkma()
    noun_lists = [[word for word, tag in kkma.pos(text) if tag.startswith('N') and len(word) > 1] for text in texts]
    word_list = [noun for sublist in noun_lists for noun in sublist]

    # 빈도 분석
    df = pd.DataFrame({'word': word_list})
    freq = df['word'].value_counts().reset_index().rename(columns={'index': 'word', 'word': 'freq'})

    # 워드클라우드 생성
    wordcloud = WordCloud(font_path='c:/Windows/Fonts/malgun.ttf', background_color='white', width=800, height=400)
    wordcloud.generate(' '.join(word_list))
    wordcloud.to_file('./static/wordcloud.png')

    # Word2Vec 학습
    model = Word2Vec(sentences=noun_lists, vector_size=100, window=5, min_count=2, workers=1)

    # 유사 단어 추출
    similar_words = []
    if len(freq) > 0 and freq['word'][0] in model.wv:
        similar_words = model.wv.most_similar(freq['word'][0])

    return freq.head(10).values.tolist(), similar_words

@app.route('/', methods=['GET', 'POST'])
def index():
    result = []
    sim_words = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        count = int(request.form.get('count', 500))
        texts = get_naver_kin(keyword, count)
        result, sim_words = analyze_texts(texts)
    return render_template('index.html', top_words=result, sim_words=sim_words)

if __name__ == '__main__':
    app.run(debug=True)
