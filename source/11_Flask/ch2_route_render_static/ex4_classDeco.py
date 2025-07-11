class SampleFlask:
    def __init__(self, arg=""):
        pass
    def route(self, func):
        def wrapper():
            print(func.__name__, '함수 전처리')
            func()
            print(func.__name__, '함수 후처리')
        return wrapper
app = SampleFlask(__name__)
@app.route
def hello():
    print('Hello')
if __name__=="__main__":
    hello()