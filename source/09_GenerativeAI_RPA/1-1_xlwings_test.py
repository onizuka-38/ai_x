import xlwings as xw

# 현재 열린 엑셀 파일의 활성화된 시트를 가져오기
wb = xw.apps.active.books.active
sheet = wb.sheets.active
print('데이터 가져와 연산 수행')
b1 = sheet.range('B1').value
b2 = sheet.range('B2').value
# b1-b2값을 'B3'셀에 넣기
sheet.range('B3').value = b1-b2
print('연산 결과 쓰기 완료')