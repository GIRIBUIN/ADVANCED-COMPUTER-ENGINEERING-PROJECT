# 1. 베이스 이미지 설정
FROM python:3.13-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 4. requirements.txt 복사 및 라이브러리 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 5. 앱 폴더 복사
COPY . .

# 6. Flask 실행 환경 변수 설정
ENV FLASK_APP="app:create_app()"
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0

# 7. 컨테이너가 시작될 때 "flask run" 명령어를 실행
CMD ["flask", "run"]