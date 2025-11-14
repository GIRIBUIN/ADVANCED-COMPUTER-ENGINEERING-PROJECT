from flask import Flask, request, jsonify, render_template
import pandas as pd
import importlib.util
import json
from pathlib import Path
import sys 
from jinja2.exceptions import TemplateNotFound

# --- 모듈 로딩 및 경로 설정 ---
# app.py가 위치한 디렉토리의 절대 경로
BASE_DIR = Path(__file__).parent
# 가능한 모듈 검색 경로 목록을 정의
SEARCH_PATHS = [
    BASE_DIR,                       # 1. /src/app/ 
    BASE_DIR / "crawling",          # 2. /src/app/crawling/ 
    BASE_DIR.parent,                # 3. /src/
    BASE_DIR / "ai",
]

# Python이 내부 모듈 import (analyzer가 chatbot을 import)를 찾을 수 있도록 
# 모든 검색 경로를 sys.path에 추가
for path in SEARCH_PATHS:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

def load_module_from_path(module_name):
    """지정된 모듈 이름으로 파일 시스템에서 모듈을 찾고 로드함."""
    
    found_path = None
    
    for path in SEARCH_PATHS:
        file_path = path / f"{module_name}.py"
        if file_path.exists():
            found_path = file_path
            break

    if not found_path:
        # 오류 메시지에 검색한 모든 경로를 포함하여 사용자가 파일 위치를 확인하도록 도움.
        checked_dirs = [str(p.resolve()) for p in SEARCH_PATHS]
        error_msg = f"모듈 파일 '{module_name}.py'를 다음 위치들 중 어디에서도 찾을 수 없습니다: \n" + "\n".join(checked_dirs)
        raise FileNotFoundError(error_msg)
             
    print(f"모듈 로드 성공: {found_path.resolve()}")
    
    # 명시적으로 절대 경로를 사용하여 모듈 로드
    spec = importlib.util.spec_from_file_location(module_name, found_path.resolve())
    if spec is None:
        raise ImportError(f"모듈 {module_name}의 스펙을 찾을 수 없습니다.")
        
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

try:
    # 필요한 모듈 로드
    crap_module = load_module_from_path("Crapping_module_ver1")
    anal_module = load_module_from_path("analyzer")
    
except FileNotFoundError as e:
    print(f"오류: 프로젝트 파일을 찾을 수 없습니다. {e}")
    # 파일 위치를 확인하거나, load_module_from_path 함수의 경로 설정을 확인 필요.
    raise

# --- Flask 앱 및 라우팅 ---
# hello.html, main.js, style.css를 같은 폴더에서 서빙하기 위해 설정
app = Flask(
    __name__, 
    template_folder=BASE_DIR / 'templates',           
    static_url_path='/static',
    static_folder=BASE_DIR / 'static' 
)

@app.route('/')
def index():    # 추후에 명확한 하나의 path로 단축 고려.
    try:
        # 1. /src/app/templates/hello.html 시도
        return render_template('hello.html')
    except TemplateNotFound:
        # 2. /src/app/templates/html/hello.html 등 서브 폴더를 가정하고 시도
        try:
            return render_template('html/hello.html')
        except TemplateNotFound:
            # 3. /src/app/templates/pages/hello.html 등 다른 서브 폴더를 가정하고 시도
            try:
                return render_template('pages/hello.html')
            except TemplateNotFound as e:
                # 모든 시도가 실패하면 오류를 다시 발생시켜 디버깅을 도움.
                print("템플릿 경로 확인 실패: 'hello.html' 파일을 찾지 못했습니다.")
                print(f"검색된 폴더: {app.template_folder.resolve()}")
                print("혹시 파일 이름에 오타는 없는지, 또는 'template' 폴더 내에 'html' 또는 'pages' 등의 추가 서브 폴더가 있는지 확인해주세요.")
                raise e # TemplateNotFound 예외를 다시 발생.

@app.route('/api/analyze', methods=['POST'])
def analyze_reviews():
    data = request.get_json()
    link = data.get('link')
    keyword = data.get('keyword')

    if not link or not keyword:
        return jsonify({"message": "링크와 키워드를 모두 제공해야 합니다."}), 400

    try:
        # 1. 크롤링 모듈 실행
        all_results = []
        # 'crap_module.TARGET_RATINGS'가 있는지 확인하고 없으면 기본값 설정
        target_ratings = getattr(crap_module, 'TARGET_RATINGS', [5, 4, 3, 2, 1]) 

        for rating in target_ratings:
            # scrape_single_rating 함수가 존재하는지 확인
            if hasattr(crap_module, 'scrape_single_rating'):
                rating_reviews = crap_module.scrape_single_rating(link, rating)
                all_results.extend(rating_reviews)
            else:
                return jsonify({"message": "크롤링 모듈(Crapping_module_ver1.py)에서 'scrape_single_rating' 함수를 찾을 수 없습니다."}), 500

        if not all_results:
            return jsonify({"message": "제공된 링크에서 리뷰를 수집할 수 없었습니다."}), 500

        # 2. 데이터 전처리 및 리뷰 문자열 생성
        temp_df = pd.DataFrame(all_results)
        clean_df = temp_df.dropna(subset=['내용']) 
        review_string = clean_df.to_string(index=False, header=False, index_names=False)   
        lines = review_string.strip().split('\n')
        review_string = ' '.join([line.strip() for line in lines])
        
        # 3. AI 분석 모듈 실행 (수정된 analyzer.py의 함수 호출 필요)
        anal_module.chatbot.reset()
        # analyzer.py에 추가할 analyze_reviews 함수를 호출.
        ai_response = anal_module.analyze_reviews(keyword, review_string)
        
        # 4. JSON 파싱
        try:
            start_index = ai_response.find('{')
            end_index = ai_response.rfind('}')
            json_string = ai_response[start_index:end_index+1].strip()
            result_json = json.loads(json_string)
        except json.JSONDecodeError:
            return jsonify({
                "message": "AI 응답 형식이 올바르지 않습니다. AI가 JSON이 아닌 텍스트를 반환했을 수 있습니다.",
                "raw_response": ai_response,
                "keyword": keyword
            }), 500

        return jsonify({
            "result_json": result_json,
            "keyword": keyword
        })

    except Exception as e:
        import traceback
        traceback.print_exc() # 서버 로그에 상세 오류 출력
        return jsonify({"message": f"서버 처리 중 오류가 발생했습니다: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)