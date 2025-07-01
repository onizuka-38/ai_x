import os
import xlwings as xw
# 1. 파일 경로 설정(현재)
file_name = "1-1_xlwings_test.xlsx"
file_path = os.path.join(os.getcwd(),
                         file_name)
print(file_path)

# 2. 액셀 열기
wb = xw.Book(file_path)

# 3. 시트 선택
sheet = wb.sheets.active

# 4. 연산
print('데이터 가져와 연산 수행')
b1 = sheet.range('B1').value
b2 = sheet.range('B2').value
# b1-b2값을 'B3'셀에 넣기
sheet.range('B3').value = b1-b2
print('연산 결과 쓰기 완료')

# 저장 및 닫기
wb.save()
wb.close()