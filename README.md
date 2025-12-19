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


## 폴더 구조 :

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

지금부터 실행 환경은 RA 폴더 아래서
