from flask import Flask, render_template, jsonify


def create_app():
    ''' Flask 애플리케이션을 생성하는 함수 '''
    app = Flask(__name__)

    @app.route('/')
    def index():
        # templates 폴더에 있는 hello.html
        return render_template('hello.html')

    return app

    # keyword, url 입력 + 버튼 동작 시 링크
    #   keyword만 입력 -> url 입력 요구
    #   url만 입력 -> 기본 키워드로 분석

    # 분석 후 결과 페이지 로드


    # 라이브러리 버튼 클릭 시 링크
    #   유저 로그인 인증
    #   인증 성공 시 목록 타이틀 제공
    #   타이틀 클릭 시 해당 내용 제공