# 파일 백업 후, now_list시트를 prev_list로 하고, now_list에 네이버 쇼핑목록 업데이트
from naverOpenai import get_naver_api_data, str_json_dataframe
import xlwings as xw
import handle_sheet as hs

def main():
  # 1. genai_rap.xls 파일 열기
  file_path = "genai_rpa.xlsx"
  wb = xw.Book(file_path)

  # 2~4
  hs.handle_init_sheet(file_path=file_path, wb=wb)
  
  # 5. 네이버 api 쇼핑목록 데이터 출력(json형태str->dict->dataframe)
  str_data = get_naver_api_data("shop", "포켄스")
  df_shopping = str_json_dataframe(str_data)
  
  # 6. 'now_list'시트의 모든 내용을 클리어하고, df_shopping내용('A1'셀)을 업데이트
  hs.update_now_list(wb, df_shopping)

  # 7. 파일 저장 및 닫기
  hs.save_close_file(file_path, wb)

if __name__=='__main__':
  main()