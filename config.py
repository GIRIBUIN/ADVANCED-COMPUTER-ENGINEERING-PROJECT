# RA/config.py

"""
Flask 애플리케이션의 모든 설정을 관리하는 파일입니다.
DB 접속 정보, API 키 등 민감한 정보가 포함될 수 있습니다.

[보안 경고]
이 파일에 실제 비밀번호나 API 키를 저장한 상태로
GitHub와 같은 공개된 장소에 절대로 올리면 안 됩니다.
운영 환경에서는 환경 변수(Environment Variables)를 사용하는 것이 가장 안전합니다.
"""

import os

# --- Flask 애플리케이션 설정 ---
SECRET_KEY = os.urandom(24)


# --- 데이터베이스 연결 설정 ---
# Windows 앱 서버에서 DB 서버(reviewanalyzer-db)를 바라보는 설정입니다.
# DB_HOST = '사설IP'  # 가상 인스턴스에서는 사설 IP
DB_HOST = '133.186.251.70' # Local 환경에서는 공인 IP
DB_PORT = 3306
DB_USER = 'user'
DB_PASSWORD = 'password123!'
DB_NAME = 'review_analyzer_db'


# --- 외부 API 키 설정 ---

GOOGLE_API_KEY = 'AIzaSyCPYmo90hQsCZ5iSrqu6tzmu6m4ecqDACo'
