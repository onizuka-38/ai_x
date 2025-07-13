from predict import loaded_model, predict_apt_price
import xlwings as xw
def main():
    '엑셀 파일 열고, 데이터 가져와 예측한 결과 저장하기'
    file_path = "../data/ex3_xlwing.xlsx"
    wb = xw.Book(file_path)
    ws = wb.sheets.active
    # 엑셀 데이터 읽어 predict하고 E열에 결과 넣기
    for line in range(2, 5):
        year = ws.range('B'+ str(line)).value
        square = ws.range('C'+str(line)).value
        floor  = ws.range('D'+str(line)).value
        pred = predict_apt_price(year, square, floor)
        ws.range('E'+str(line)).value = pred
    wb.save(file_path)
    wb.close()

if __name__=="__main__":
    main()