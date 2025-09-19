# 리뷰 분석 및 요약 서비스 (ReviewAnalyzer)

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

## 폴더 구조

```
ReviewAnalyzer/
├── README.md         # 프로젝트 개요 및 가이드
├── src/              # 소스 코드
├── docs/             # 과제 산출물
│   ├── 01_project_plan/
│   ├── 02_requirements/
│   ├── 03_design/
│   ├── 04_final_report/
│   └── meeting_logs/
├── archive/          # 참고용 비공식 자료 (초기 아이디어 등)
└── .gitignore        # Git 추적 제외 목록
```

---

## Git 브랜치 전략 및 협업 워크플로우

`main` 브랜치의 안정성을 유지하기 위해서 **Pull Request 기반의 워크플로우**를 따릅니다.

### 협업 절차 (매우 중요!)

**Step 1: 작업 시작 전, `main`의 최신 내용을 내 브랜치로 가져오기**

```bash
# 1. 내 개인 브랜치로 이동
git checkout branchname

# 2. main 브랜치의 최신 내용을 내 브랜치로 pull
git pull origin main
```

**Step 2:내 브랜치에 Push**

- 각자 맡은 기능을 자유롭게 개발하고, 작업 단위로 커밋(Commit).
- 작업이 완료되면, 자신의 원격 브랜치에 푸시(Push).

```bash
# 예시
git add .
git commit -m "feat: 크롤링 기능 구현"
git push origin branchname
```

**Step 3: Pull Request (PR) 생성**

- 기능 개발이 완료되어 `main` 브랜치에 합치고 싶을 때, GitHub에서 **Pull Request**를 생성합니다.
- **Base Branch: `main` <- Compare Branch: `branchname`** (내 브랜치 -> main)
- 어떤 작업을 했는지 다른 팀원들이 이해하기 쉽도록 제목과 설명을 상세히 작성합니다.

**Step 4: 코드 리뷰 및 Merge**

- PR이 생성되면 **카카오톡/디코로 팀원들에게 리뷰를 요청**합니다.
- 모든 팀원은 PR에 올라온 코드를 확인하고 의견을 제시합니다.
- **최소 1명 이상의 팀원에게 `Approve`(승인)를 받은 후**, PR을 생성한 사람이 `Merge` 버튼을 눌러 `main` 브랜치에 코드를 반영합니다.

---

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

# 가상 환경 활성화(터미널을 새로 열 때마다 실행하면 됩니다) cmd에서하면 됩니다.
.\venv\Scripts\Activate
# 성공하면 터미널 프롬프트 앞에 (venv)가 표시됩니다.
```

3. Docker 컨테이너 실행  
- src 폴더 안에서 명령어를 실행해야 함(cd 명령어로 이동)
```VS code terminal
ReviewAnalyzer>src> docker compose up --build
# web-1, db-1의 로그에서 오류가 없는지 확인
# http://localhost:5000에 접속하여 화면이 나타나면 정상입니다.
```

4.  그 외
- 컨테이너 삭제하고 싶으면 'docker compose down' 실행
