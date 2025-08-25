from datetime import datetime
def myproject(request):
    return {
        'now':datetime.now().strftime("%y-%m-%d %p %I:%M:%S"),
    }