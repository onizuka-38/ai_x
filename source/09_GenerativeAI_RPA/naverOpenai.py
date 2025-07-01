import os
import sys
import urllib.request
from dotenv import load_dotenv
import json
import pandas as pd
from openai import OpenAI

def get_naver_api_data(media, word):
  "word에 대해 media 검색한 결과의 str을 return"
  load_dotenv()
  client_id = os.getenv("CLIENT_ID")
  client_secret = os.getenv("CLIENT_SECRET")
  encText = urllib.parse.quote(word)
  url = f"https://openapi.naver.com/v1/search/{media}?sort=date&display=20&query={encText}"

  request = urllib.request.Request(url)
  request.add_header("X-Naver-Client-Id",client_id)
  request.add_header("X-Naver-Client-Secret",client_secret)
  response = urllib.request.urlopen(request)
  rescode = response.getcode()
  if(rescode==200):
      response_body = response.read()
      return response_body.decode('utf-8')
  else:
      print("Error Code:" + rescode)

def str_json_dataframe(str_json_result):
  "json스타일의 문자열을 데이터프레임으로 변환하여 return"
  if isinstance(str_json_result, str):
    json_result = json.loads(str_json_result)
  else:
    json_result = {}
  # 딕셔너리 json_result를 데이터 프레임으로 바꿔서 return
  items = json_result.get('items', [])
  df =pd.DataFrame(items)
  df['순위']=range(1, len(df)+1)
  df.set_index("순위", inplace=True)
  return df

def aiconn(prompt):
  # LLM 요청하여 메세지 받기
  load_dotenv('.env')
  client = OpenAI()
  completion = client.chat.completions.create(
    model="gpt-4.1-nano",
    messages=[{"role":"user", "content":prompt}],
    # max_tokens=300
  )
  # 5. 분석글 return
  return completion.choices[0].message.content

def get_openai_shopping_analysis(wb):
  # 2. prev_list, now_list 시트 전체 내용 불러오기
  prev_sheet = wb.sheets['prev_list']
  now_sheet  = wb.sheets['now_list']
  prev_data = prev_sheet.used_range.value # 사용된 범위의 데이터
  now_data = now_sheet.used_range.value

  # 3. 프롬프트 작성
  prompt = f"""다음 두 목록을 비교분석하여, prev_list목록에서 now_list목록으로
  바뀐 주요 특징을 추출해 줘.
  prev_list 목록 : {prev_data}
  now_list 목록 : {now_data}
  비교 분석 결과를 바탕으로 구체적인 수치, 상품명, 쇼핑몰명 등을 언급하여 
  한글로 200자 이내로 분석글을 작성해 줘."""
  return aiconn(prompt=prompt)

def get_openai_news_summarize(str_news_data):
  # 뉴스 요약 return
  prompt = f"""다음 뉴스 내용을 구체적인 수치, 고유명사를 언급하며 글머리를 활용하여 
  한글 200자 이내로 요약 글을 작성해 줘.
  뉴스 내용 {str_news_data}"""
  return aiconn(prompt=prompt)