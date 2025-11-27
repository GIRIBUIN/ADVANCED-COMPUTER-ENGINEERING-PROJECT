# src/app/routes.py
from . import auth
from . import facade
from .db import db

from flask import Blueprint, render_template, jsonify, request, session, current_app

# '블루프린트 객체 이름은 main
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """ 메인 페이지를 보여주는 함수 """
    return render_template('index.html')

# =============================================
# 로그인, 회원가입, 회원탈퇴
# =============================================

@bp.route('/api/signup', methods=['POST'])
def signup():
    """ 회원가입 """
    
    user_data = request.get_json()
    user_name = user_data.get('user_name')

    if not user_name:
        return jsonify({"status" : "error", "message" : "user_name 상태 오류"}), 400
    
    res = auth.register_user(user_name)

    if res['status'] == 'error':
        return jsonify(res), 409
    else:
        return jsonify(res), 201

@bp.route('/api/login', methods=['POST'])
def login():
    """ 로그인 """
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
    
@bp.route('/api/logout', methods=['POST'])
def logout():
    """ 로그아웃 """
    session.clear()
    return jsonify({"status": "success", "message": "로그아웃되었습니다."}), 200

@bp.route('/api/check_login', methods=['GET'])
def check_login_status():
    """ 로그인 상태 확인 """
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
    """ 회원 탈퇴 """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "로그인이 필요합니다."}), 401
    
    try:
        db.delete_user(user_id)
        
        session.clear()
        return jsonify({"status": "success", "message": "계정이 성공적으로 삭제되었습니다."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =============================================
# 리뷰 분석 및 저장
# =============================================

@bp.route('/api/analyze', methods=['POST'])
def analyze_endpoint():
    """ 분석만 수행 """
    data = request.get_json()
    link = data.get('link')
    keywords = data.get('keywords') # 리스트 형태 : ['키워드1', '키워드2']

    if not link or not keywords:
        return jsonify({"error": "link와 keywords는 필수 항목입니다."}), 400

    result = facade.analyze_reviews(link, keywords) # facade에서 처리

    if result['status'] == 'error':
        return jsonify(result), 500
    
    return jsonify(result), 200

@bp.route('/api/library', methods=['POST'])
def save_to_library_endpoint():
    """
    '/api/analyze'를 통해 받은 분석 결과를 라이브러리에 저장
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "로그인이 필요합니다."}), 401 

    # 프론트엔드에서 '/api/analyze'를 수행하고 받은 결과 데이터 전체(저장할 데이터)를 다시 보냄
    analysis_data = request.get_json()
    if not analysis_data or 'analysis_id' not in analysis_data:
        return jsonify({"error": "저장할 결과 데이터가 필요합니다."}), 400

    result = facade.save_analysis_to_library(analysis_data, user_id) # facade에서 처리

    if result.get('status') == 'error':
        return jsonify(result), 500
    
    return jsonify(result), 201

# =============================================
# 라이브러리 조회 및 관리
# =============================================

@bp.route('/api/library', methods=['GET'])
def get_my_library():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    try:
        analysis_ids = db.get_library_by_user_id(user_id)
        library_items = db.get_analyses_by_ids(analysis_ids)
        return jsonify({"status": "success", "data": library_items}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/api/library/<string:analysis_id>', methods=['DELETE'])
def delete_from_my_library(analysis_id):
    """ 로그인한 사용자의 라이브러리에서 특정 항목 삭제 """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    
    try:
        rows_deleted = db.delete_from_library(user_id, analysis_id)
        
        if rows_deleted > 0:
            return jsonify({"status": "success", "message": "삭제되었습니다."}), 200
        else:
            return jsonify({"status": "error", "message": "삭제할 항목을 찾지 못했거나 권한이 없습니다."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500