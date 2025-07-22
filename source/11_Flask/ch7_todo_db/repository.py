import cx_Oracle
conn = cx_Oracle.connect('scott', 
                        'tiger', 
                        '210.121.189.12:1521/xe')

from models import TodoRequest
from typing import List # 타입체크

def get_todos(order) -> List[dict]:
  cursor = conn.cursor()
  if order == 'asc':
    sql = "SELECT * FROM TODO ORDER BY ID"
  else:
    sql = "SELECT * FROM TODO ORDER BY ID DESC"
  cursor.execute(sql)
  result = cursor.fetchall() # 튜플 리스트
  # keys = [desc[0] for desc in cursor.description] # ['id','content','is_done']
  # todos = [dict(zip(keys, row)) for row in result]
  cursor.close()
  todos = []
  for row in result:
    todos.append({'id': row[0], 'content': row[1], 'is_done': row[2]})
  return todos

def get_next_id() -> int:
  cursor = conn.cursor()
  sql = "SELECT NVL(MAX(ID), 0)+1 FROM TODO"
  cursor.execute(sql)
  result = cursor.fetchone() # 튜플 (4,)
  cursor.close()
  return result[0]


if __name__ == '__main__':
  print('/todos : ',get_todos('asc'))
  print('next_id : ', get_next_id())
  