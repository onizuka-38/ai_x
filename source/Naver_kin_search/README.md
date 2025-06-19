# 🧠 네이버 지식인 워드클라우드 Flask 앱

이 프로젝트는 네이버 지식인 검색 결과를 수집한 후,
형태소 분석(Kkma)을 통해 명사를 추출하고,
워드클라우드와 Word2Vec 유사 단어 분석 결과를 웹 페이지에서 시각화합니다.

---

## 📁 프로젝트 구조

```
project/
├── app.py                # Flask 애플리케이션 메인 코드
├── requirements.txt      # 필요한 패키지 목록
├── .env.example          # 환경 변수 예시 파일
├── templates/
│   └── index.html        # HTML 템플릿
└── static/
    └── wordcloud.png     # 생성된 워드클라우드 이미지
```

---

## ✅ 설치 방법

### 1. 프로젝트 클론
```bash
git clone https://github.com/yourusername/yourproject.git
cd yourproject
```

### 2. 가상환경 생성 및 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 파일 설정
`.env.example` 파일을 `.env`로 복사하고, 네이버 Open API 키를 입력합니다:

```
Client_ID=YOUR_NAVER_CLIENT_ID
Client_Secret=YOUR_NAVER_CLIENT_SECRET
```

---

## 🚀 실행 방법

```bash
python app.py
```

브라우저에서 아래 주소로 접속:

```
http://127.0.0.1:5000
```

---

## 🧩 주요 기능

- ✅ 네이버 지식인 검색 API 사용 (최대 500개까지 수집)
- ✅ Kkma를 활용한 명사 추출
- ✅ 단어 빈도 분석 + 워드클라우드 시각화
- ✅ Word2Vec 유사 단어 추천 결과 출력
- ✅ Flask 웹 서비스 인터페이스

---

## 💡 참고

- API 키는 네이버 개발자센터에서 [https://developers.naver.com](https://developers.naver.com) 신청 가능
- konlpy 사용 시 Java 설치 필요

---

## 📸 미리보기

워드클라우드 / 상위 단어 / 유사 단어 분석 결과가 웹으로 출력됩니다.
(스크린샷은 `static/wordcloud.png` 참고)

---

## 📄 라이선스

MIT License
