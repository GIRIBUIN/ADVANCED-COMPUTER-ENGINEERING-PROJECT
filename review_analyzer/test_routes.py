# RA/review_analyzer/test_routes.py

"""
개발 및 테스트 목적으로 사용되는 API 엔드포인트를 정의하는 파일입니다.
DEBUG 모드가 True일 때만 활성화됩니다.
"""

from flask import Blueprint, jsonify, session, current_app

# db 모듈을 상대 경로로 임포트합니다.
from .db import db

# Blueprint 객체를 생성합니다. url_prefix를 사용하여 모든 라우트 앞에 '/test'를 붙입니다.
bp = Blueprint('test', __name__, url_prefix='/test')


@bp.route('/db')
def test_db_connection():
    """ DB 연결 상태를 테스트합니다. """
    try:
        conn = db.get_db()
        if conn:
            return jsonify({"status": "success", "message": "데이터베이스 연결에 성공했습니다!"})
        else:
            return jsonify({"status": "error", "message": "DB 연결 객체를 가져오는 데 실패했습니다."}), 500
    except Exception as e:
        current_app.logger.error(f"DB 연결 테스트 중 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route('/category')
def test_category_creation():
    """ 카테고리 생성 및 조회 함수(find_or_create_category)를 테스트합니다. """
    try:
        category_id_1 = db.find_or_create_category('노트북')
        category_id_2 = db.find_or_create_category('노트북') # 동일한 카테고리 호출
        category_id_3 = db.find_or_create_category('스마트폰')
        return jsonify({
            "노트북_첫번째_호출_ID": category_id_1,
            "노트북_두번째_호출_ID": category_id_2,
            "스마트폰_첫번째_호출_ID": category_id_3
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route('/keywords')
def test_keywords_creation():
    """ 키워드 생성 및 조회 함수(find_or_create_keywords)를 테스트합니다. """
    try:
        list1 = ['색감', '가성비', '맛있는']
        list2 = ['싼', '고급모델'] # '싼'은 중복될 수 있음
        keywords_1 = db.find_or_create_keywords(list1)
        keywords_2 = db.find_or_create_keywords(list2)
        return jsonify({
            "키워드_그룹1_ID": keywords_1,
            "키워드_그룹2_ID": keywords_2
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 참고: '/test_save', '/test_library', '/test_library_delete'와 같은
# 복잡한 테스트 로직은 Postman이나 별도의 테스트 스크립트 파일을 통해
# 실제 API를 호출하는 방식으로 검증하는 것이 더 효율적일 수 있습니다.
# 여기서는 요청하신 대로 기존 로직을 유지하고 정리했습니다.

@bp.route('/save_and_library')
def test_save_and_library_flow():
    """ 분석 결과 저장 및 라이브러리 추가의 전체 흐름을 테스트합니다. """
    # 테스트를 위한 고정 데이터
    test_analysis_id = 'test_analysis_01'
    test_url = 'http://test.com/product/01'
    test_text = '이것은 테스트 분석 결과입니다.'
    test_category_name = '키보드'
    test_keywords = ['타건감', '디자인']
    test_user_name = 'tester' # 테스트를 위해 'tester' 사용자가 DB에 존재해야 함

    user = db.find_user_by_name(test_user_name)
    if not user:
        return jsonify({"status": "error", "message": f"테스트를 위해 '{test_user_name}' 사용자를 먼저 생성해주세요."}), 404
    
    user_id = user['user_id']
    db_conn = db.get_db()

    try:
        # 1. 분석 결과 저장 (없을 경우)
        if not db.isitem_from_library(test_analysis_id):
            category_id = db.find_or_create_category(test_category_name)
            keyword_ids = db.find_or_create_keywords(test_keywords)
            db.save_analysis(test_analysis_id, test_url, test_text, category_id)
            db.link_analysis_to_keywords(test_analysis_id, keyword_ids)

        # 2. 라이브러리에 추가 (없을 경우)
        if not db.find_library_item(user_id, test_analysis_id):
            db.add_to_library(user_id, test_analysis_id)
        
        db_conn.commit()
        return jsonify({"status": "success", "message": "테스트 데이터 저장 및 라이브러리 추가 성공"})
    except Exception as e:
        db_conn.rollback()
        current_app.logger.error(f"테스트 저장 중 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500