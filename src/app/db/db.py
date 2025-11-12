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

def add_user(user_name):
    """ 회원가입 : 닉네임으로 user 추가 """
    db = get_db()
    cursor = db.cursor()
    sql = "INSERT INTO USERS (user_name) VALUES (%s)"
    cursor.execute(sql, (user_name,))
    db.commit()

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
    sql = "SELECT * FROM USERS WHERE user_id = %d"
    cursor.execute(sql,(user_id,))
    user = cursor.fetchone()
    return user

