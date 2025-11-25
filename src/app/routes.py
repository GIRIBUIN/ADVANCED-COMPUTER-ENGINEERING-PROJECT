# src/app/routes.py
from . import auth

from .db import db
from flask import Blueprint, render_template, jsonify, request, session, current_app

# '블루프린트 객체 이름은 main
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """ 메인 페이지를 보여주는 함수 """
    return render_template('index.html')

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


# --- test db ---
@bp.route('/test_db')
def test_db_connection():
    """ DB 연결 테스트 """
    try:
        conn = db.get_db()

        if conn:
            return jsonify({"status": "success", "message": "Database connection successful!"})
        else:
            return jsonify({"status": "error", "message": "Failed to get DB connection object."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- test 검색 ---
@bp.route('/test_category')
def test_category():
    category_id_1 = db.find_or_create_category('노트북')
    category_id_2 = db.find_or_create_category('노트북')
    category_id_3 = db.find_or_create_category('스마트폰')

    return jsonify({
        "first_call_notebook": category_id_1,
        "second_call_notebook": category_id_2,
        "first_call_smartphone": category_id_3
    })

@bp.route('/test_keywords')
def test_keywords():
    list1 = ['색감', '가성비', '맛있는']
    list2 = ['싼', '고급모델']
    keywords_1 = db.find_or_create_keywords(list1)
    keywords_2 = db.find_or_create_keywords(list2)

    return jsonify({
        "fisrt": keywords_1,
        "second": keywords_2,
    })


# --- test 저장 ---
@bp.route('/test_save')
def test_save_to_library():

    # test 내용 실제로는 받아와야 함
    test_analysis_id = 'test01'
    test_url = 'http://test.com'
    test_text = 'test text.'
    test_category_name = '노트북'
    test_keywords = ['싼', '고급 모델']
    test_user_name = 'tester'

    with current_app.test_request_context():
        
        test_user = db.find_user_by_name(test_user_name)
        if not test_user:
            return jsonify({"status": "error", "message": f"'{test_user_name}' is not logined."})
        session['user_id'] = test_user['user_id']
        db_conn = db.get_db()
        current_user_id = session.get('user_id')

        try:
            
            existing_analysis = db.isitem_from_library(test_analysis_id)

            if not existing_analysis:
                category_id = db.find_or_create_category(test_category_name)
                keyword_ids = db.find_or_create_keywords(test_keywords)
                
                db.save_analysis(test_analysis_id, test_url, test_text, category_id)
                db.link_analysis_to_keywords(test_analysis_id, keyword_ids)

            if not db.find_library_item(current_user_id, test_analysis_id):
                db.add_to_library(current_user_id, test_analysis_id)
            
            db_conn.commit()
            
            return jsonify({
                "status": "success", 
                "message": "transaction: analysis + library save"
            })

        except Exception as e:
            db_conn.rollback()
            return jsonify({"status": "error", "message": str(e)})
        

# --- test library ---
# 조회
@bp.route('/test_library')
def test_library():
    test_user_name = 'tester' # test name

    with current_app.test_request_context():
        test_user = db.find_user_by_name(test_user_name)
        if not test_user:
            return jsonify({
                "status": "error", 
                "message": f"테스트를 위해 먼저 '{test_user_name}' 유저를 생성하고, "
                           f"해당 유저로 분석 결과를 1개 이상 저장해주세요."
            })
        
        session['user_id'] = test_user['user_id']
        
        try:
            
            # 로그인한 사용자 세션 가져오기
            current_user_id = session.get('user_id')
            if not current_user_id:
                return jsonify({"status": "error", "message": "no user_id in session"}), 401

            # User가 저장한 분석 결과에 대한 analysis_id 리스트
            analysis_ids = db.get_library_by_user_id(current_user_id)
            
            if not analysis_ids:
                return jsonify({
                    "status": "success", 
                    "message": "empty library",
                    "data": []
                })

            # analysis_id 리스트를 통해 상세 정보들 가져오기
            library_items = db.get_analyses_by_ids(analysis_ids)
            
            return jsonify({
                "status": "success",
                "user_id": current_user_id,
                "count": len(library_items),
                "data": library_items
            })

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

# 삭제
@bp.route('/test_library_delete')
def test_library_delete():
    # test 데이터
    test_user_name = 'tester'
    test_analysis_id = 'test01'

    with current_app.test_request_context():
        test_user = db.find_user_by_name(test_user_name)
        if not test_user:
            return jsonify({"status": "error", "message": f"'{test_user_name}' is not logined"})
        
        session['user_id'] = test_user['user_id']
        current_user_id = session.get('user_id')

        db_conn = db.get_db()
        try:
            if not db.find_library_item(current_user_id, test_analysis_id):
                db.add_to_library(current_user_id, test_analysis_id)
                db_conn.commit()
        except Exception:
            return jsonify({"status": "error", "message": f"'{test_analysis_id}' : ANALYSIS is empty table."})

        item_before_delete = db.find_library_item(current_user_id, test_analysis_id)
        if not item_before_delete:
            return jsonify({"status": "error", "message": "삭제할 아이템을 저장하는 데 실패했습니다."})

        rows_deleted = db.delete_from_library(current_user_id, test_analysis_id)

        item_after_delete = db.find_library_item(current_user_id, test_analysis_id)

        return jsonify({
            "status": "success",
            "test_scenario": f"User {current_user_id} deletes item {test_analysis_id}",
            "item_existed_before_delete": item_before_delete is not None,
            "rows_deleted_by_function": rows_deleted,
            "item_exists_after_delete": item_after_delete is not None
        })