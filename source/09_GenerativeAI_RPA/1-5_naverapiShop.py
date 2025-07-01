# 네이버 쇼핑목록 데이터프레임으로 
import os
import sys
import urllib.request
from dotenv import load_dotenv
import json
import pandas as pd

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

def main():
  # 네이버 api 쇼핑목록 데이터 출력(json형태str->dict->dataframe)
  str_data = get_naver_api_data("shop", "포켄스")
  df_shopping = str_json_dataframe(str_data)
  print(df_shopping)

if __name__=='__main__':
  main()