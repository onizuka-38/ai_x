import cx_Oracle
conn = cx_Oracle.connect("scott",
                        "tiger",
                        "210.121.189.12:1521/xe") 

def get_emp_list():
    cursor = conn.cursor()
    sql = "SELECT * FROM EMP ORDER BY EMPNO"
    cursor.execute(sql)
    emps = cursor.fetchall()
    keys = [desc[0] for desc in cursor.description]
    emp_list = [dict(zip(keys, emp)) for emp in emps]
    return emp_list