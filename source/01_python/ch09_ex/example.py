from customer import load_customers
from functions import fn1_insert_customer_info, fn2_print_customers, fn3_delete_customer, fn4_search_customer
from functions import fn5_save_customer_csv, fn9_save_customer_txt
from functions import fn9_save_customer_txt
# from functions import *


def main():
    global customer_list
    customer_list = load_customers()
    while True:
        print('1:입력 | 2:전체출력 | 3:삭제 | 4:이름검색 | 5:csv내보내기 | 9.종료 ', end='')
        fn = input('메뉴선택 : ')
        if fn =='1':
            customer = fn1_insert_customer_info() #입력받은 내용으로 customer 객체를 반환
            customer_list.append(customer)
#             print('fn_호출한 결과를 customer에 받아 customer_list에 append')
        elif fn=='2':
            fn2_print_customers(customer_list)
#             print('fn2_호출')
        elif fn=='3':
            fn3_delete_customer(customer_list)
#             print('fn3_호출')
        elif fn=='4':
            fn4_search_customer(customer_list)
#             print('fn4_호출')
        elif fn=='5':
            fn5_save_customer_csv(customer_list)
#             print('fn5_호출')
        elif fn=='9':
            fn9_save_customer_txt(customer_list)
#             print('fn9_호출')
            break

if __name__=='__main__':
    main()