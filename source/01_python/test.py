# word image 100개 검색한 데이터는 csv파일로, 이미지는 ch14_image폴더에 저장되는 함수

def get_naver_save_image(word):
    import requests
    import pandas as pd
    from dotenv import load_dotenv
    import os
    load_dotenv() 
    client_id = os.getenv('Client_ID')
    client_secret = os.getenv('Client_Secret')
    url = f'https://openapi.naver.com/v1/search/image?query={word}&display=100'
    headers = {'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret':client_secret}
    response = requests.get(url, headers=headers)
    items = response.json()['items'] # 방법1에서만 가능한 함수
    items_list = []
    for idx, item in enumerate(items):
        title = item.get('title')
        link = item.get('link')
        thumbnail = item.get('thumbnail')
        sizeheight = item.get('sizeheight')
        sizewidth = item.get('sizewidth')
        items_list.append({
            'no': idx+1,
            'title': title,
            'link' : link,
            'thumbnail' : thumbnail,
            'sizeheight':sizeheight,
            'sizewidth' :sizewidth
        })
        # link와 thumbnail을 저장
        save_img('메인', idx+1, word, link)
        save_img('썸네일', idx+1, word, thumbnail)
        # 20% 40% 60% 80% 지점에서 message 출력
        if idx/20 == round(idx/20):
            print(f'= = = {idx}% 진행 중입니다 = = =')
        
    df = pd.DataFrame(items_list)
    df.to_csv(f'ch14_image/{word}.csv', encoding='cp949', index=False)
    print('~ ~ ~ 이미지 및 csv 파일 저장 완료 ~ ~ ~')
    
import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_yes24_bestseller():
    url = 'http://www.yes24.com/24/Category/BestSeller?CategoryNumber=001'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')
    books = soup.select('table.list tr')

    items_list = []

    for idx, book in enumerate(books, 1):
        title_tag = book.select_one('p.copy a')
        author_tag = book.select_one('p.auth')
        pub_tag = book.select_one('p.pub')
        price_tag = book.select_one('p.price strong')

        if not (title_tag and author_tag and pub_tag and price_tag):
            continue

        items_list.append({
            '순위': idx,
            '책이름': title_tag.text.strip(),
            '저자': author_tag.text.strip(),
            '출판사': pub_tag.text.strip(),
            '가격': price_tag.text.strip()
        })

        if idx >= 48:  # 48위까지
            break

    # CSV 저장
    df = pd.DataFrame(items_list)
    df.to_csv('ch14_yes24.csv', index=False, encoding='utf-8-sig')

    # TXT 저장
    with open('ch14_yes24.txt', 'w', encoding='utf-8') as f:
        for item in items_list:
            line = f"{item['순위']}. {item['책이름']}, {item['저자']}, {item['출판사']}, {item['가격']}"
            f.write(line + '\n')

    print("✅ ch14_yes24.csv / ch14_yes24.txt 저장 완료!")

# 실행
get_yes24_bestseller()
