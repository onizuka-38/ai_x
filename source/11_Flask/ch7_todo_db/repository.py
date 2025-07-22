import cx_Oracle
conn = cx_Oracle.connect("scott",
                        "tiger",
                        "210.121.189.12:1521/xe")

from models import TodoRequest
from typing import List # 타입체크

def get_todos(order) -> List[dict]:
    cursor = conn.cursor()
    if order == 'asc':
        sql = "SELECT * FROM TODO ORDER BY ID ASC"
    else:
        sql = "SELECT * FROM TODO ORDER BY ID DESC"
    cursor.execute(sql)
    ret = cursor.fetchall()
    return [TodoRequest(**row).model_dump() for row in ret]