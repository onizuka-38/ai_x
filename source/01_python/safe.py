import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_yes24_bestseller():
    url = 'https://www.yes24.com/product/category/bestseller?categoryNumber=001'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    books = soup.select('ol#yesBestList > li')
    items_list = []

    for idx, book in enumerate(books, 1):
        try:
            rank = book.select_one('div.item_img > div.img_canvas > div > em').text.strip()
            title = book.select_one('div.item_info > div.info_row.info_name > a.gd_name').text.strip()
            author = book.select_one('div.item_info > div.info_row.info_pubGrp > span.authPub.info_auth > a').text.strip()
            publisher = book.select_one('div.item_info > div.info_row.info_pubGrp > span.authPub.info_pub > a').text.strip()
            price = book.select_one('div.item_info > div.info_row.info_price > strong > em').text.strip()

            items_list.append({
                '순위': rank,
                '제목': title,
                '저자': author,
                '출판사': publisher,
                '가격': price + '원'
            })

            if idx >= 48:
                break
        except Exception as e:
            print(f'❌ {idx}번째 항목에서 오류 발생: {e}')
            continue

    df = pd.DataFrame(items_list)
    df.to_csv('ch14_yes24.csv', index=False, encoding='utf-8-sig')
    print("✅ ch14_yes24.csv 저장 완료!")

# 실행
get_yes24_bestseller()
