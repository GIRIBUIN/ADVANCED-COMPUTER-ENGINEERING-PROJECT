# RA/review_analyzer/__init__.py

"""
Flask 애플리케이션 팩토리(Application Factory)가 있는 패키지 초기화 파일입니다.
"""

from flask import Flask

def create_app():

    # Flask 애플리케이션 객체 생성
    # instance_relative_config=True : config.py를 인스턴스 폴더 기준으로 찾도록 설정
    app = Flask(__name__, instance_relative_config=False)

    # --- 설정 불러오기 ---
    # 프로젝트 루트에 있는 config.py 파일로부터 설정을 로드합니다.
    # from_pyfile('../config.py') 대신 from_object('config')
    try:
        app.config.from_pyfile('../config.py')
    except FileNotFoundError:
        # config.py 파일이 없을 경우를 대비한 예외 처리
        print("경고: config.py 파일을 찾을 수 없습니다. 기본 설정으로 실행됩니다.")
        # 기본 SECRET_KEY라도 설정해주는 것이 좋습니다.
        app.config.setdefault('SECRET_KEY', 'a_default_secret_key_for_development')


    # --- 데이터베이스 초기화 ---
    # db 모듈을 임포트하고, init_app 함수를 호출하여 Flask 앱에 DB를 연결합니다.
    from .db import db
    db.init_app(app)


    # --- 블루프린트(Blueprint) 등록 ---
    # 각 기능별로 분리된 라우트 파일을 앱에 등록합니다.
    from . import routes
    app.register_blueprint(routes.bp)
    
    # test_routes.py는 개발 환경에서만 로드되도록 분기 처리
    if app.config.get('DEBUG'):
        try:
            from . import test_routes
            app.register_blueprint(test_routes.bp)
        except ImportError:
            print("정보: test_routes.py 모듈을 찾을 수 없습니다.")

    # 생성 및 구성이 완료된 앱 객체를 반환합니다.
    return app
