# src/app.py

from app import create_app

app = create_app()

# 실행할 때만 서버를 가동
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)