# src/app/routes.py
from . import auth

from .db import db
from flask import Blueprint, render_template, jsonify, request, session

# '블루프린트 객체 이름은 main
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """ 메인 페이지를 보여주는 함수 """
    return render_template('hello.html')

# --- 라우트별 구현  ---

@bp.route('/signup', methods=['POST'])
def signup():
    """ 회원가입 API """
    
    # json 데이터 받음
    user_data = request.get_json()
    user_name = user_data.get('user_name')

    if not user_name:
        return jsonify({"status" : "error", "message" : "user_name 상태 오류"}), 400
    
    res = auth.register_user(user_name)

    if res['status'] == 'error':
        return jsonify(res), 409
    else:
        return jsonify(res), 201

@bp.route('/login', methods=['POST'])
def login():
    
    # db에서 user 삭제했는데 세션 때문에 로그인 성공할 수 도 있음
    if "user_id" in session:
        user = db.find_user_by_id(session['user_id'])
        if user:
            return jsonify({"status" : "success", "message" : "이미 로그인되어 있습니다."}), 200
        else:
            session.clear()


    user_data = request.get_json()
    user_name = user_data.get('user_name')

    if not user_name:
        return jsonify({"status": "error", "message" : "user_name이 없습니다."}), 400
    
    res = auth.login_user(user_name)

    if res['status'] == 'error':
        return jsonify(res), 404
    else:
        session['user_id'] = res['user_id']
        session['user_name'] = user_name
        return jsonify(res), 200

# @bp.route('/library')
# def show_library():

#     pass


# -- test db ---
@bp.route('/test_db')
def test_db_connection():
    """ 데이터베이스 연결을 테스트하는 함수 """
    try:
        from .db import db
        # db 모듈의 get_db() 함수를 호출하여 연결을 시도
        conn = db.get_db()
        # 연결 객체가 정상이면 성공 메시지 반환
        if conn:
            return jsonify({"status": "success", "message": "Database connection successful!"})
        else:
            return jsonify({"status": "error", "message": "Failed to get DB connection object."})
    except Exception as e:
        # 연결 과정에서 오류가 발생하면 에러 메시지 반환
        return jsonify({"status": "error", "message": str(e)})