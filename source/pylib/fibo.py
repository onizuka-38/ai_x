def fibonacci_print(n):
    '''
    매개변수로 들어온 n값 미만의 피보나치 수열을 출력
    ex. n=10 이면 0 1 1 2 3 5 8 을 출력
    '''    
    a, b = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a+b
    print()  # 개행
    
def fibonacci_return(n):
    result=[]
    a, b = 0, 1
    while a < n:
        result.append(a)
        a, b = b, a+b
    return result  # 개행
    '''
    매개변수로 들어온 n값 미만의 피보나치 수열을 리스트로 return
    ex. n=10 이면 [0 1 1 2 3 5 8] 을 return
    ''' 
    '테스트 : python fibo.py / python fibo.py 100'
if __name__=="__main__":
    import sys
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
        print('1, print test : ', end='')
        fibonacci_print(n)
        print('2, return test : ', fibonacci_return(n))
    else :
        print('1, print test : ', end='')
        fibonacci_print(100)
        print('2, return test : ', fibonacci_return(100))