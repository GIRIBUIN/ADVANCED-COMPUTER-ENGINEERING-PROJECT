# 가상 인스턴스에 올릴 파일 구조입니다. 이거 기반으로 코드 작성해주세요.

최대한 옮기긴 했는데, 최신화 코드 맞는 지 확인한 번 해주세요.
.env 지우고 config에서 관리하도록 수정했습니다.
접근 차단되는 문제 있는데 해결 부탁드려요.

## 폴더 구조

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

지금부터 실행 환경은 RA 폴더 아래서 python run.py 하여 flask 구동 시킨 뒤 로컬에서 테스트해주세요.(윈도우 서버라서 똑같습니다.)
