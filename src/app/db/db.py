import pymysql
from flask import current_app, g

def get_db():
    """
    한 번의 요청 안에서는 동일한 DB 연결.
    """
    if 'db' not in g:
        # g 보관함에 db 연결이 없으면, 새로 하나 만듭니다.
        app_config = current_app.config
        g.db = pymysql.connect(
            host=app_config['DB_HOST'],
            user=app_config['DB_USER'],
            password=app_config['DB_PASSWORD'],
            database=app_config['DB_NAME'],
            port=app_config.get('DB_PORT', 3306), # 포트 정보 추가
            cursorclass=pymysql.cursors.DictCursor
        )

    # g 저장된 db 연결 반환.
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)

# --- CRUD 함수 ---

# =============================
# USER 관련 
# USERS (user_id, user_name)
# =============================

def add_user(user_name):
    """ 회원가입 : 닉네임으로 user 추가 """
    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO USERS (user_name) VALUES (%s)"
    cursor.execute(sql, (user_name,))
    db.commit() # 회원가입 : 단일 작업이어서 commit 여기다 둠

def find_user_by_name(user_name):
    """ 로그인 : 닉네임으로 user 찾기 """
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT * FROM USERS WHERE user_name = %s"
    cursor.execute(sql,(user_name,))
    user = cursor.fetchone()
    return user

def find_user_by_id(user_id):
    """로그인 : id로 user 찾기"""
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT * FROM USERS WHERE user_id = %s"
    cursor.execute(sql,(user_id,))
    user = cursor.fetchone()
    return user

# =============================
# 저장, 라이브러리 관련 
# ANALYSES (analysis_id, url, analysis_text, category_id)
# ANALYSIS_KEYWORDS (analysis_id, keyword_id)
# CATEGORIES (category_id, category_name)
# KEYWORDS (keyword_id, keyword)
# LIBRARY (user_id, analysis_id)
# =============================

def save_analysis(analysis_id, url, analysis_text, category_id):
    """저장: 분석 결과를 ANALYSES 테이블에 저장 """
    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO ANALYSES (analysis_id, url, analysis_text, category_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (analysis_id, url, analysis_text, category_id))

def link_analysis_to_keywords(analysis_id, keyword_ids):
    """ analysis_id와 keyword_id들을 ANALYSIS_KEYWORDS 테이블에 연결 """
    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO ANALYSIS_KEYWORDS (analysis_id, keyword_id) VALUES (%s, %s)"
    data_tuples = [(analysis_id, keyword_id) for keyword_id in keyword_ids]
    cursor.executemany(sql, data_tuples)

def find_or_create_category(category_name):
    """
    category_name으로 category_id select
    """
    db = get_db()
    cursor = db.cursor()
    
    sql_find = "SELECT category_id FROM CATEGORIES WHERE category_name = %s"
    cursor.execute(sql_find, (category_name,))
    result = cursor.fetchone()

    if result:
        return result['category_id']
    else:
        sql_insert = "INSERT INTO CATEGORIES (category_name) VALUES (%s)"
        cursor.execute(sql_insert, (category_name,))
        return cursor.lastrowid


def find_or_create_keywords(keyword_list):
    """ 키워드 리스트로 키워드가 들어오면, keyword_id 반환(생성) """
    db = get_db()
    cursor = db.cursor()
    keyword_ids = []

    for keyword in keyword_list:
        sql_find = "SELECT keyword_id FROM KEYWORDS WHERE keyword = %s"
        cursor.execute(sql_find, (keyword,))
        result = cursor.fetchone()
        
        if result:
            keyword_ids.append(result['keyword_id'])
        else:
            sql_insert = "INSERT INTO KEYWORDS (keyword) VALUES (%s)"
            cursor.execute(sql_insert, (keyword,))
            keyword_ids.append(cursor.lastrowid)
            
    return keyword_ids

def add_to_library(user_id, analysis_id):
    """
    라이브러리 : user_id와 analysis_id만 저장
    #! caller에서 transaction 처리
    """

    db = get_db()
    cursor = db.cursor()
    
    sql = "INSERT INTO LIBRARY (user_id, analysis_id) VALUES (%s, %s)"
    
    try:
        cursor.execute(sql, (user_id, analysis_id))
        print(f"Successfully prepared to insert into LIBRARY: user_id={user_id}, analysis_id={analysis_id}")
    except Exception as e:
        print(f"Error adding to library: {e}")
        raise e
    
def find_library_item(user_id, analysis_id):
    """
    LIBRARY 테이블에 user_id, analysis_id가 매칭되는 아이템이 있는지
    """
    db = get_db()
    cursor = db.cursor()
    
    sql = "SELECT * FROM LIBRARY WHERE user_id = %s AND analysis_id = %s"
    
    cursor.execute(sql, (user_id, analysis_id))
    
    item = cursor.fetchone()
    
    return item

def get_library_by_user_id(user_id):
    """
    user_id가 저장한 라이브러리 목록 추출할 때 사용
    모든 analysis_id 리스트 반환
    """
    db = get_db()
    cursor = db.cursor()
    
    sql = "SELECT analysis_id FROM LIBRARY WHERE user_id = %s ORDER BY saved_at DESC"
    
    cursor.execute(sql, (user_id,))
    
    items = cursor.fetchall()
    
    analysis_ids = [item['analysis_id'] for item in items]
    
    return analysis_ids

def get_analyses_by_ids(analysis_id_list):
    """
    analysis_id_list를 받아서 상세 분석 정보들 반환
    """
    if not analysis_id_list:
        return [] # 빈 리스트 반환

    db = get_db()
    cursor = db.cursor()
    
    placeholders = ', '.join(['%s'] * len(analysis_id_list))
    sql = f"SELECT * FROM ANALYSES WHERE analysis_id IN ({placeholders})"
    
    cursor.execute(sql, tuple(analysis_id_list))
    
    analyses = cursor.fetchall()
    
    return analyses

def delete_from_library(user_id, analysis_id):
    """ 라이브러리 목록 삭제 """
    db = get_db()
    cursor = db.cursor()
    sql = "DELETE FROM LIBRARY WHERE user_id = %s AND analysis_id = %s"
    cursor.execute(sql, (user_id, analysis_id))
    db.commit()

def isitem_from_library(analysis_id):
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT analysis_id FROM ANALYSES WHERE analysis_id = %s"
    cursor.execute(sql, (analysis_id,))
    existing_analysis = cursor.fetchone()

    return existing_analysis