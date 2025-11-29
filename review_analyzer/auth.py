# RA/review_analyzer/auth.py

"""
사용자 인증 관련 비즈니스 로직을 처리하는 모듈입니다.
회원가입, 로그인 등의 실제 로직을 수행합니다.
"""

from .db import db


def register_user(user_name):
    """
    신규 사용자를 등록합니다.
    이미 존재하는 사용자인지 확인 후 DB에 추가합니다.
    """
    existing_user = db.find_user_by_name(user_name)
    if existing_user:
        return {"status": "error", "message": "이미 등록된 사용자입니다. 다른 ID를 입력해주세요."}
    
    db.add_user(user_name)
    return {"status": "success", "message": "회원가입을 성공했습니다."}


def login_user(user_name):
    """
    사용자 로그인을 처리합니다.
    DB에서 사용자를 찾아 사용자 ID를 반환합니다.
    """
    existing_user = db.find_user_by_name(user_name)
    if existing_user:
        return {"status": "success", "message": "로그인을 성공했습니다.", "user_id": existing_user['user_id']}
    else:
        return {"status": "error", "message": "존재하지 않는 사용자입니다."}