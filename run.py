# RA/run.py

"""
애플리케이션을 실행하는 진입점(Entry Point) 파일입니다.
터미널에서 'python run.py' 명령으로 Flask 개발 서버를 시작합니다.
"""

from review_analyzer import create_app

app = create_app()

if __name__ == '__main__':
    # host='0.0.0.0' : 모든 IP에서의 접속을 허용 (서버 환경 필수)
    # debug=True : 개발 모드로 실행, 코드 변경 시 자동 재시작 (use_reloader=True일 때)
    # use_reloader=False : 크롤링에 사용되는 multiprocessing과 충돌을 피하기 위해 자동 재시작 기능을 끕니다.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)