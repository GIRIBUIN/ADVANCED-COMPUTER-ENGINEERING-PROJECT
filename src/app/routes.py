# src/app/routes.py

from flask import Blueprint, render_template, jsonify 

# '블루프린트 객체 이름은 main
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """ 메인 페이지를 보여주는 함수 """
    return render_template('hello.html')

# --- 라우트별 구현  ---

# @bp.route('/analyze', methods=['POST'])
# def analyze_reviews():

#     pass

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