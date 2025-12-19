# 딸깍 리뷰 (ReviewAnalyzer)

사용자가 제공하는 제품 링크와 키워드를 기반으로, 리뷰를 AI로 분석 및 요약하여 맞춤형 추천을 제공하는 웹 서비스입니다.

## 프로젝트 개요

- **프로젝트 목표:** 불필요한 정보 탐색 시간을 줄이고, 사용자에게 객관적이고 핵심적인 제품 정보를 제공합니다.
- **핵심 기능:** 키워드 기반 리뷰 분석, 지능형 DB 캐싱, AI 맞춤형 추천, 개인 라이브러리
- **팀원:**
  - `최정길`: 202110542
  - `이의빈`: 202114228
  - `이유환`: 202111343

---

## 기술 스택

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **Infrastructure:** Docker

---

## 폴더 구조 : venv는 RA 밑에서 하시길

```
📦RA
┣ 📂review_analyzer
┃ ┣ 📂ai
┃ ┃ ┣ 📜analyzer.py
┃ ┃ ┣ 📜chatbot.py
┃ ┃ ┗ 📜__init__.py
┃ ┣ 📂crawling
┃ ┃ ┣ 📜Crapping_module_ver1.py
┃ ┃ ┣ 📜Recommend_Product.py
┃ ┃ ┗ 📜__init__.py
┃ ┣ 📂db
┃ ┃ ┣ 📜db.py
┃ ┃ ┣ 📜schema.sql
┃ ┃ ┗ 📜__init__.py
┃ ┣ 📂static
┃ ┃ ┣ 📂css
┃ ┃ ┗ 📂js
┃ ┃ ┃ ┗ 📜main.js
┃ ┣ 📂templates
┃ ┃ ┗ 📜index.html
┃ ┣ 📜auth.py
┃ ┣ 📜facade.py
┃ ┣ 📜routes.py
┃ ┣ 📜test_routes.py
┃ ┗ 📜__init__.py
┣ 📜config.py
┗ 📜run.py
```

## 개발 환경 설정

이 프로젝트는 Docker 기반으로 동작하므로, 모든 팀원은 아래 절차에 따라 환경을 설정해야 합니다.

1.  프로그램
- git + sourcetree: 깃허브 유용성 관련
- Docker Desktop: 필수 설치. 설치 후 실행한 상태에서 진행해야 합니다!
- VS code: Code Editor

2.  프로젝트 가져오기
- 자신이 원하는 위치에 git clone 받고 진행합니다.(ReviewAnalyzer라는 폴더에 클론을 받았다고 생각하고 진행)
-  VS code에서 ReviewAnalyzer 폴더 열고, Terminal을 엽니다.
```
# Python 가상 환경 생성(한 번만 하면 됩니다!)
pytohn -m venv venv

# 가상 환경 활성화(터미널을 새로 열 때마다 실행하면 됩니다)
# python 터미널을 cmd로 바꿔서 하면 됩니다.
.\venv\Scripts\Activate
# 성공하면 터미널 프롬프트 앞에 (venv)가 표시됩니다.
```

3. Docker 컨테이너 실행  
- src 폴더 안에서 명령어를 실행해야 함(cd 명령어로 이동)
```VS code terminal
(venv) ReviewAnalyzer>src> docker compose up --build
# web-1, db-1의 로그에서 오류가 없는지 확인
# http://localhost:5000에 접속하여 화면이 나타나면 정상입니다.
```

4.  그 외
- 컨테이너 삭제하고 싶으면 'docker compose down' 실행하면 됩니다.
