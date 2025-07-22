# pip install flask
from flask import Flask, render_template
from database.repository import get_emp_list

app = Flask(__name__)

@app.route('/')
def index():
    emp_list = get_emp_list();
    return render_template('index.html', emp_list=emp_list)

if __name__ == '__main__':
    app.run(debug=True)
