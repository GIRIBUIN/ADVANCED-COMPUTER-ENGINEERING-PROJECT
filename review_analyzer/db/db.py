# RA/review_analyzer/db/db.py

"""
데이터베이스 연결 및 모든 CRUD(Create, Read, Update, Delete) 작업을 처리하는 모듈입니다.
이 파일의 함수들은 애플리케이션의 다른 부분(facade, auth 등)에서 호출되어 사용됩니다.
"""

import pymysql
from flask import current_app, g

def get_db():
    """
    Flask 애플리케이션 컨텍스트(g)를 사용하여 현재 요청 내에서 DB 연결을 가져오거나 생성합니다.
    한 번의 요청(request) 동안에는 동일한 DB 연결 객체가 재사용됩니다.
    """
    if 'db' not in g:
        # g 객체에 'db' 연결이 없으면, config.py의 설정으로 새로 생성합니다.
        app_config = current_app.config
        g.db = pymysql.connect(
            host=app_config['DB_HOST'],
            user=app_config['DB_USER'],
            password=app_config['DB_PASSWORD'],
            database=app_config['DB_NAME'],
            port=app_config.get('DB_PORT', 3306),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor # 결과를 딕셔너리 형태로 받기 위함
        )
    return g.db


def close_db(e=None):
    """
    요청이 끝나면(teardown) g 객체에서 DB 연결을 찾아 닫습니다.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    """
    Flask 앱 팩토리(create_app)에서 호출될 초기화 함수입니다.
    애플리케이션 컨텍스트가 종료될 때마다 close_db가 호출되도록 등록합니다.
    """
    app.teardown_appcontext(close_db)


# ======================================================================
#                            USER 테이블 관련 함수
# ======================================================================

def add_user(user_name):
    """ 회원가입: 새로운 사용자를 USERS 테이블에 추가합니다. """
    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO USERS (user_name) VALUES (%s)"
    cursor.execute(sql, (user_name,))
    db.commit()


def find_user_by_name(user_name):
    """ 사용자 이름으로 USERS 테이블에서 사용자를 찾습니다. """
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT * FROM USERS WHERE user_name = %s"
    cursor.execute(sql, (user_name,))
    return cursor.fetchone()


def find_user_by_id(user_id):
    """ 사용자 ID로 USERS 테이블에서 사용자를 찾습니다. """
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT * FROM USERS WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    return cursor.fetchone()


def delete_user(user_id):
    """ 회원 탈퇴: 사용자 ID로 USERS 테이블에서 사용자를 삭제합니다. """
    db = get_db()
    cursor = db.cursor()
    sql = "DELETE FROM USERS WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    db.commit()
    return cursor.rowcount


# ======================================================================
#                  ANALYSIS 및 LIBRARY 관련 함수
# ======================================================================

def save_analysis(analysis_id, url, analysis_text, category_id, recommended_info=None):
    """ 
    분석 결과와 (선택적으로) 추천 상품 정보를 ANALYSES 테이블에 저장합니다.
    """
    db = get_db()
    cursor = db.cursor()
    recommended_info_json = json.dumps(recommended_info, ensure_ascii=False) if recommended_info else None
    sql = """
        INSERT INTO ANALYSES (analysis_id, url, analysis_text, category_id, recommended_info) 
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (analysis_id, url, analysis_text, category_id, recommended_info_json))

def link_analysis_to_keywords(analysis_id, keyword_ids):
    """ 분석 ID와 키워드 ID들을 ANALYSIS_KEYWORDS 테이블에 연결합니다. """
    # [!] 이 함수는 commit을 하지 않습니다. 호출한 쪽(facade)에서 트랜잭션을 관리합니다.
    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO ANALYSIS_KEYWORDS (analysis_id, keyword_id) VALUES (%s, %s)"
    data_tuples = [(analysis_id, keyword_id) for keyword_id in keyword_ids]
    cursor.executemany(sql, data_tuples)


def find_or_create_category(category_name):
    """ 카테고리 이름으로 ID를 찾고, 없으면 새로 생성 후 ID를 반환합니다. """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT category_id FROM CATEGORIES WHERE category_name = %s", (category_name,))
    result = cursor.fetchone()

    if result:
        return result['category_id']
    else:
        cursor.execute("INSERT INTO CATEGORIES (category_name) VALUES (%s)", (category_name,))
        return cursor.lastrowid


def find_or_create_keywords(keyword_list):
    """ 키워드 리스트를 받아 각 키워드의 ID를 찾거나 생성하여 ID 리스트를 반환합니다. """
    db = get_db()
    cursor = db.cursor()
    keyword_ids = []

    for keyword in keyword_list:
        cursor.execute("SELECT keyword_id FROM KEYWORDS WHERE keyword = %s", (keyword,))
        result = cursor.fetchone()
        
        if result:
            keyword_ids.append(result['keyword_id'])
        else:
            cursor.execute("INSERT INTO KEYWORDS (keyword) VALUES (%s)", (keyword,))
            keyword_ids.append(cursor.lastrowid)
            
    return keyword_ids


def add_to_library(user_id, analysis_id):
    """ 사용자와 분석 결과를 LIBRARY 테이블에 연결(저장)합니다. """
    # [!] 이 함수는 commit을 하지 않습니다. 호출한 쪽(facade)에서 트랜잭션을 관리합니다.
    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO LIBRARY (user_id, analysis_id) VALUES (%s, %s)"
    cursor.execute(sql, (user_id, analysis_id))

    
def find_library_item(user_id, analysis_id):
    """ LIBRARY 테이블에서 특정 사용자의 특정 분석 결과 저장 여부를 확인합니다. """
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT * FROM LIBRARY WHERE user_id = %s AND analysis_id = %s"
    cursor.execute(sql, (user_id, analysis_id))
    return cursor.fetchone()


def get_library_by_user_id(user_id):
    """ 특정 사용자의 라이브러리에 저장된 모든 analysis_id 리스트를 반환합니다. """
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT analysis_id FROM LIBRARY WHERE user_id = %s ORDER BY saved_at DESC"
    cursor.execute(sql, (user_id,))
    items = cursor.fetchall()
    return [item['analysis_id'] for item in items]


def get_analyses_by_ids(analysis_id_list):
    """ 
    analysis_id 리스트를 받아 상세 분석 정보를 반환합니다. 
    (recommended_info 포함)
    """
    if not analysis_id_list:
        return []
    db = get_db()
    cursor = db.cursor()
    placeholders = ', '.join(['%s'] * len(analysis_id_list))
    # SELECT 절에 recommended_info 추가
    sql = f"SELECT analysis_id, url, analysis_text, category_id, analyzed_at, recommended_info FROM ANALYSES WHERE analysis_id IN ({placeholders})"
    cursor.execute(sql, tuple(analysis_id_list))
    return cursor.fetchall()


def delete_from_library(user_id, analysis_id):
    """ 
    라이브러리에서 특정 분석 결과를 삭제합니다.
    커밋은 호출자(routes.py)에서 처리합니다.
    
    Args:
        user_id: 사용자 ID
        analysis_id: 분석 결과 ID
        
    Returns:
        int: 삭제된 행의 개수
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        sql = "DELETE FROM LIBRARY WHERE user_id = %s AND analysis_id = %s"
        cursor.execute(sql, (user_id, analysis_id))
        
        rows_deleted = cursor.rowcount
        return rows_deleted
        
    finally:
        cursor.close()


def does_analysis_exist(analysis_id):
    """ ANALYSES 테이블에 특정 분석 결과가 이미 저장되어 있는지 확인합니다. """
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT analysis_id FROM ANALYSES WHERE analysis_id = %s"
    cursor.execute(sql, (analysis_id,))
    return cursor.fetchone()
