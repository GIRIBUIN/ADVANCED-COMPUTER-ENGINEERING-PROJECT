# 사용자 인증 모듈

from .db import db


def register_user(user_name):
    """ 회원가입: 사용자 등록 """
    existing_user = db.find_user_by_name(user_name)
    if existing_user:
        return {"status" : "error", "message" : "이미 등록된 사용자입니다. 다른 ID를 입력해주세요."}
    
    db.add_user(user_name)
    return{"status" : "success", "message" : "회원가입을 성공했습니다."}

def login_user(user_name):
    """ 로그인: 사용자 로그인 """
    existing_user = db.find_user_by_name(user_name)
    if existing_user:
        return {"status" : "success", "message" : "로그인을 성공했습니다.", "user_id" : existing_user['user_id']}
    else:
        return {"status" : "error", "message" : "존재하지 않는 사용자입니다."}