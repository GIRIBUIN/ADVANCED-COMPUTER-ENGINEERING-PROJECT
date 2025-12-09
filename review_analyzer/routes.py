# RA/review_analyzer/routes.py

"""
애플리케이션의 메인 API 엔드포인트를 정의하는 파일입니다.
리뷰 분석, 라이브러리 관리, 사용자 인증 상태 확인 등의 라우트를 포함합니다.
"""

from flask import (
    Blueprint, render_template, jsonify, request, session, current_app
)

# 현재 패키지 내의 다른 모듈들을 상대 경로로 임포트합니다.
from . import auth
from . import facade
from .db import db

# Blueprint 객체를 생성합니다.
# 'main'은 이 블루프린트의 별칭이며, url_for 등에서 사용됩니다.
bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """ 메인 페이지 렌더링 """
    return render_template('index.html')


# =============================================
# 리뷰 분석 및 라이브러리
# =============================================

@bp.route('/api/analyze', methods=['POST'])
def analyze_endpoint():
    """ 리뷰 분석 API: 링크와 키워드를 받아 분석 결과만 반환합니다. """
    data = request.get_json()
    link = data.get('link')
    keywords = data.get('keywords')

    if not all([link, keywords]):
        return jsonify({"status": "error", "message": "link와 keywords는 필수 항목입니다."}), 400

    # 핵심 로직은 facade 모듈에 위임합니다.
    result = facade.analyze_reviews(link, keywords)

    if result.get('status') == 'error':
        return jsonify(result), 500
    
    return jsonify(result), 200


@bp.route('/api/library', methods=['POST'])
def save_to_library_endpoint():
    """ 라이브러리 저장 API: 분석 결과를 사용자의 라이브러리에 저장합니다. """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "로그인이 필요합니다."}), 401

    analysis_data = request.get_json()
    if not analysis_data or 'analysis_id' not in analysis_data:
        return jsonify({"status": "error", "message": "저장할 분석 데이터가 필요합니다."}), 400

    result = facade.save_analysis_to_library(analysis_data, user_id)

    if result.get('status') == 'error':
        return jsonify(result), 500
    
    return jsonify(result), 201  # 생성 성공은 201 Created가 더 적합합니다.


@bp.route('/api/library', methods=['GET'])
def get_my_library():
    """ 라이브러리 조회 API: 현재 로그인된 사용자의 라이브러리 목록을 반환합니다. """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "로그인이 필요합니다."}), 401

    try:
        analysis_ids = db.get_library_by_user_id(user_id)
        library_items = db.get_analyses_by_ids(analysis_ids)
        return jsonify({"status": "success", "data": library_items}), 200
    except Exception as e:
        # DB 오류 등 예기치 못한 에러 발생 시
        current_app.logger.error(f"라이브러리 조회 중 오류 발생: {e}")
        return jsonify({"status": "error", "message": "데이터를 조회하는 중 오류가 발생했습니다."}), 500


@bp.route('/api/library/<string:analysis_id>', methods=['DELETE'])
def delete_from_my_library(analysis_id):
    """ 라이브러리 항목 삭제 API """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "로그인이 필요합니다."}), 401
    
    db_conn = None
    try:
        db_conn = db.get_db()
        
        # 삭제 실행
        rows_deleted = db.delete_from_library(user_id, analysis_id)
        
        # 명시적 커밋 (이 시점에 오류가 없으면 확정)
        db_conn.commit()
        
        if rows_deleted > 0:
            return jsonify({"status": "success", "message": "삭제되었습니다."}), 200
        else:
            return jsonify({"status": "error", "message": "삭제할 항목을 찾지 못했거나 권한이 없습니다."}), 404
            
    except Exception as e:
        # 오류 발생 시 롤백
        if db_conn:
            try:
                db_conn.rollback()
            except:
                pass
        
        current_app.logger.error(f"라이브러리 삭제 중 오류 발생: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        return jsonify({"status": "error", "message": "데이터를 삭제하는 중 오류가 발생했습니다."}), 500

# 참고: 사용자 인증 관련 라우트(회원가입, 로그인 등)는 auth.py로 분리하는 것이 좋습니다.
# 만약 auth.py에 라우트가 있다면, 이 파일에서는 해당 코드를 제거해도 됩니다.
# 여기서는 요청하신 대로 원본 코드를 유지하고 정리했습니다.

# =============================================
# 사용자 인증 (auth.py로 분리 권장)
# =============================================

@bp.route('/api/signup', methods=['POST'])
def signup():
    """ 회원가입 API """
    user_data = request.get_json()
    user_name = user_data.get('user_name')

    if not user_name:
        return jsonify({"status": "error", "message": "user_name을 입력해주세요."}), 400
    
    res = auth.register_user(user_name)

    if res['status'] == 'error':
        return jsonify(res), 409  # Conflict: 이미 존재하는 사용자
    else:
        return jsonify(res), 201  # Created


@bp.route('/api/login', methods=['POST'])
def login():
    """ 로그인 API """
    if "user_id" in session:
        user = db.find_user_by_id(session['user_id'])
        if user:
            return jsonify({"status": "success", "message": "이미 로그인되어 있습니다."}), 200
        else:
            session.clear()

    user_data = request.get_json()
    user_name = user_data.get('user_name')

    if not user_name:
        return jsonify({"status": "error", "message": "user_name을 입력해주세요."}), 400
    
    res = auth.login_user(user_name)

    if res['status'] == 'error':
        return jsonify(res), 401  # Unauthorized
    else:
        session['user_id'] = res['user_id']
        session['user_name'] = user_name
        return jsonify(res), 200


@bp.route('/api/logout', methods=['POST'])
def logout():
    """ 로그아웃 API """
    session.clear()
    return jsonify({"status": "success", "message": "로그아웃되었습니다."}), 200


@bp.route('/api/check_login', methods=['GET'])
def check_login_status():
    """ 로그인 상태 확인 API """
    if 'user_id' in session:
        return jsonify({
            "is_logged_in": True,
            "user_id": session['user_id'],
            "user_name": session['user_name']
        }), 200
    else:
        return jsonify({"is_logged_in": False}), 200
    

@bp.route('/api/user', methods=['DELETE'])
def delete_account():
    """ 회원 탈퇴 API """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "로그인이 필요합니다."}), 401
    
    try:
        db.delete_user(user_id)
        session.clear()
        return jsonify({"status": "success", "message": "계정이 성공적으로 삭제되었습니다."}), 200
    except Exception as e:
        current_app.logger.error(f"회원 탈퇴 중 오류 발생: {e}")
        return jsonify({"status": "error", "message": "계정을 삭제하는 중 오류가 발생했습니다."}), 500
