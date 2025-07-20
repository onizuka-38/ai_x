import os
import pymysql
import time
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# DB 정보
user = os.getenv("DB_USER")  # .env 파일에 DB_USER 설정해도 됨
host = os.getenv("DB_HOST")
password = os.getenv("DB_PW")  # DB_pw → 대소문자 주의 (env 키명)
port = int(os.getenv("DB_PORT"))
db = os.getenv("DB_NAME")


def get_connection():
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db,
        port=port,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def test_page():
    return render_template('test_weekly_trade.html')


@app.route('/api/latest_weeks', methods=['GET'])
def get_latest_weeks():
    conn = get_connection()
    query = """
        SELECT DISTINCT weekno FROM fact_trade_weekly
        ORDER BY weekno DESC LIMIT 14
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        weeks = [row['weekno'] for row in cursor.fetchall()]
    conn.close()

    if not weeks:
        return jsonify({'start_week': '', 'end_week': ''})

    return jsonify({'start_week': weeks[-1], 'end_week': weeks[0]})


@app.route('/api/weekly_trade', methods=['GET'])
def get_weekly_trade():
    item_code = request.args.get('item_code')
    crop_full_code = request.args.get('crop_full_code')
    grade = request.args.get('grade')
    sanji_code = request.args.get('sanji_cd')
    start_week = request.args.get('start_week')
    end_week = request.args.get('end_week')

    if not item_code:
        return jsonify({'error': 'item_code is required'}), 400

    # WHERE
    where_clause = "wt.item_code = %s"
    params = [item_code]

    if crop_full_code:
        where_clause += " AND wt.crop_full_code = %s"
        params.append(crop_full_code)
    if grade:
        where_clause += " AND wt.grade_label = %s"
        params.append(grade)
    if sanji_code:
        where_clause += " AND wt.j_sanji_cd = %s"
        params.append(sanji_code)
    if start_week:
        where_clause += " AND wt.weekno >= %s"
        params.append(start_week)
    if end_week:
        where_clause += " AND wt.weekno <= %s"
        params.append(end_week)

    # 기본 SELECT & GROUP BY 구성
    group_by = ['wt.weekno', 'wt.item_code']
    select_parts = [
        'wt.weekno',
        'wt.item_code AS item_code'
    ]

    # Join 대상 구분
    if crop_full_code:
        join_crop = "JOIN master_crop_variety mcv ON wt.crop_full_code = mcv.crop_full_code"
        group_by.append('wt.crop_full_code')
        group_by.append('mcv.gds_sclsf_nm')
        select_parts.append('wt.crop_full_code')
        select_parts.append('MAX(mcv.gds_mclsf_nm) AS gds_mclsf_nm')
        select_parts.append('mcv.gds_sclsf_nm')
    else:
        join_crop = "JOIN vw_crop_item_name mcv ON wt.item_code = mcv.item_code"
        group_by.append('mcv.gds_mclsf_nm')
        select_parts.append('mcv.gds_mclsf_nm')
        select_parts.append("'' AS gds_sclsf_nm")

    # 등급 선택 시
    if grade:
        group_by.append('wt.grade_label')
        select_parts.append('wt.grade_label AS grd_cd')
        select_parts.append('wt.grade_label AS grd_nm')

    # 산지 선택 시
    if sanji_code:
        group_by.append('wt.j_sanji_cd')
        select_parts.append('wt.j_sanji_cd')
        select_parts.append('MAX(mrs.j_sanji_nm) AS j_sanji_nm')

    # 집계 컬럼
    select_parts.append('ROUND(SUM(wt.unit_tot_qty), 0) AS unit_tot_qty')
    select_parts.append('ROUND(AVG(wt.avg_prc), 0) AS avg_price')

    select_sql = ',\n    '.join(select_parts)
    group_by_sql = ', '.join(group_by)

    # 최종 쿼리 조합
    query = f"""
        SELECT
            {select_sql}
        FROM fact_trade_weekly wt
        {join_crop}
        LEFT JOIN (
            SELECT DISTINCT j_sanji_cd, j_sanji_nm
            FROM map_region_weather_station
        ) mrs ON wt.j_sanji_cd = mrs.j_sanji_cd
        WHERE {where_clause}
        GROUP BY {group_by_sql}
        ORDER BY wt.weekno
    """


    # 실행 및 반환
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    conn.close()
    print('--------------------')
    print('실행 쿼리:')
    print(query)
    print('파라미터:', params)
    print('--------------------')
    return jsonify(rows)




@app.route('/api/items', methods=['GET'])
def get_items():
    conn = get_connection()
    query = """
        SELECT DISTINCT item_code, gds_mclsf_nm
        FROM vw_crop_item_name
        ORDER BY item_code
    """
    print('--------------------')
    print('실행 쿼리:')
    print(query)
    print('--------------------')

    with conn.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/api/varieties', methods=['GET'])
def get_varieties():
    item_code = request.args.get('item_code')
    start_week = request.args.get('start_week')
    end_week = request.args.get('end_week')

    if not item_code or not start_week or not end_week:
        return jsonify({'error': 'item_code, start_week, end_week are required'}), 400

    conn = get_connection()
    query = """
        SELECT DISTINCT mcv.crop_full_code, mcv.gds_sclsf_nm
        FROM master_crop_variety mcv
        JOIN fact_trade_weekly wt ON mcv.crop_full_code = wt.crop_full_code
        WHERE mcv.item_code = %s
            AND wt.weekno >= %s
            AND wt.weekno <= %s
        ORDER BY mcv.crop_full_code
    """
    print('--------------------')
    print('실행 쿼리:')
    print(query)
    print('--------------------')

    with conn.cursor() as cursor:
        cursor.execute(query, (item_code, start_week, end_week))
        rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)


@app.route('/api/sanjis', methods=['GET'])
def get_sanjis():
    start = time.time()
    item_code = request.args.get('item_code')
    crop_full_code = request.args.get('crop_full_code')
    start_week = request.args.get('start_week')
    end_week = request.args.get('end_week')
    

    if not item_code or not start_week or not end_week:
        return jsonify({'error': 'item_code, start_week, end_week are required'}), 400
    
    t0 = time.time()
    conn = get_connection()
    print("DB 커넥션 소요:", time.time() - t0)
    if crop_full_code:
        query = """
            SELECT t.j_sanji_cd, s.j_sanji_nm
        FROM (
            SELECT DISTINCT j_sanji_cd
            FROM fact_trade_weekly
            WHERE item_code = %s
                AND weekno >= %s AND weekno <= %s
                AND crop_full_code = %s
                AND j_sanji_cd IS NOT NULL
        ) t
        INNER JOIN vw_map_region_sanji s
            ON s.j_sanji_cd = t.j_sanji_cd
        ORDER BY t.j_sanji_cd
        """
        params = [item_code, start_week, end_week, crop_full_code]
    else:
        query = """
            SELECT t.j_sanji_cd, s.j_sanji_nm
            FROM (
                SELECT DISTINCT j_sanji_cd
                FROM fact_trade_weekly
                WHERE item_code = %s
                AND weekno >= %s AND weekno <= %s
                AND j_sanji_cd IS NOT NULL
            ) t
            INNER JOIN vw_map_region_sanji s
            ON s.j_sanji_cd = t.j_sanji_cd
            ORDER BY t.j_sanji_cd
        """
        params = [item_code, start_week, end_week]


    print('--------------------')
    print('실행 쿼리:')
    print(query)
    print('파라미터:', params)
    print('--------------------')

    with conn.cursor() as cursor:
        t1 = time.time()
        cursor.execute(query, tuple(params))
        print("execute 소요:", time.time() - t1)
        rows = cursor.fetchall()
        print("rows count:", len(rows))
        print("fetchall 소요:", time.time() - t1)
        print(f"/api/sanjis 실행시간: {time.time() - start:.3f}초")
    conn.close()
    return jsonify(rows)


if __name__ == '__main__':
    app.run(debug=True)
