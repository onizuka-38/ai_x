# pip install pydantic
from pydantic import BaseModel
class TodoRequest(BaseModel):
  id : int
  content : str
  is_done : bool | None=False

if __name__ == '__main__':
  todo = TodoRequest(id="1", content='flask 공부', is_done="True")
  # print(todo.dict()) # todo 객체를 dict 형태로 변환
  print(todo.model_dump()) # todo 객체를 dict 형태로 변환
  todo = TodoRequest(id="2", content='django 공부')
  print(todo.model_dump())