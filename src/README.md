# 현재 파일 구조

'''
src/      <-- 소스코드 폴더
├── app/             <-- 메인 애플리케이션 폴더
│   ├── static/     
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   ├── templates/   <-- HTML 파일
│   │   └── index.html
│   └── __init__.py
│
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
'''

---

## 파일 설명

- ReviewAnalyzer/: 최상위 루트 폴더
- app/: 소스코드
- requirements.txt: 프로젝트에 필요한 Python 라이브러리 목록
- .gitignore: Git 추적하지 않을 파일
- .dockerignore: Docker 빌드 시 제외할 파일/폴더 목록
