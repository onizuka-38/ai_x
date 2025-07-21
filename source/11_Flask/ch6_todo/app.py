from flask import Flask, request, render_template
from flask import redirect, url_for, abort # redirect, 강제로 예외 발생
from flask import session # 로그인/로그아웃
from models import TodoRequest

app = Flask(__name__)
# app.secret_key = '안녕하세요'
app.config['SECRET_KEY'] = 'abc123'

todo_data = {
  1 : {
    'id': 1,
    'content': 'flask 공부',
    'is_done': True,
  },
  2 : {
    'id': 2,
    'content': 'django 공부',
    'is_done': False,
  },
}

@app.route('/')
def index():
  '로그인 성공 로직(세션에 로그인 한 사람의 정보 넣기) 후 /todos로 리다이렉트'
  session["user_id"] = "hong"
  session["user_name"] = "홍길동"
  # return redirect("/todos") # /todos(GET) 요청경로로 
  return redirect(url_for("todos")) # todos 함수로 

@app.route('/logout')
def logout():
  '세션의 값 날리고 /todos로 리다이렉트'
  session.pop("user_id", None)
  session.pop("user_name", None)
  return redirect(url_for("todos")) # /todos 로 리다이렉트

@app.route('/todos') # 전체 목록 보기
def todos():
  'todo_data를 list로 변환하여 렌더링'
  ret = list(todo_data.values()) # 딕셔너리 리스트로 변환
  order = request.args.get('order', 'asc') # 정렬 순서 : asc, desc
  if order == 'desc':
    ret = ret[::-1] #ret.reverse()
  next_id = max(todo_data.keys()) + 1 if len(todo_data) > 0 else 1
  return render_template('todo/todos.html', 
                        todos=ret,
                        next_id = next_id,
                        order=order)

@app.route('/todos/<int:id>') # 해당 id 상세보기
def todo(id):
  '해당 id의 todo_data를 html로 렌더링'
  todo = todo_data.get(id)
  if todo:
    return render_template('todo/todo.html', todo=todo)
  return abort(404, description='해당 id의 할일이 없습니다.')

@app.route('/create', methods=['POST'])
def create():
  '새로운 할일(request.form)을 추가하는 로직'
  # print(request.form.to_dict())
  todo = TodoRequest(**request.form.to_dict())
  todo_data[todo.id] = todo.model_dump() # todo를 dict형태로 변환하여 todo_data에 추가
  return redirect(url_for("todos")) # /todos 로 (GET방식) 리다이렉트

@app.route('/update/<int:id>', methods=['GET']) # 수정할 수 있는 페이지 가기
def update(id):
  return render_template('todo/update.html', todo=todo_data[id])

@app.route('/update/<int:id>/<string:content>/<string:is_done>', methods=['PUT'])
def update(id, content, is_done):
    todo = todo_data.get(id)
    if todo:
        todo['content'] = content
        todo['is_done'] = is_done.lower() == 'true'
        todo_data[id] = todo
        return f'{id}번 할일이 수정되었습니다.'
    return abort(404, description='해당 id의 할일이 없습니다.')

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
  '해당 id의 todo_data를 삭제하는 로직'
  todo = todo_data.get(id)
  if todo:
    del todo_data[id]
    return f'{id}번 할일이 삭제되었습니다.'
  return abort(404, description='해당 id의 할일이 없습니다.')

@app.errorhandler(404)
def not_found(error):
  return render_template('page_not_found.html', error=error), 404


if __name__ == '__main__':  
  app.run(debug=True)