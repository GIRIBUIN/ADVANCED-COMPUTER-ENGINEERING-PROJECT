import os
import sys
import json
from flask import Flask, render_template, request, jsonify
import pandas as pd
import random
import time

# --- 경로 설정 ---
# src/app/ai와 src/app/crawling 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'crawling'))

# 모델 파일 임포트 (파일 이름은 대문자로 시작하므로, import 시 주의)
# 실제 Python에서는 'Crapping_module_ver1.py'를 'Crapping_module_ver1'로 임포트
try:
    from Crapping_module_ver1 import scrape_reviews_and_save  # 아래에서 함수명 변경 예정
    from analyzer import ReviewAnalasys
except ImportError as e:
    print(f"[ERROR] 모델 파일을 임포트할 수 없습니다: {e}")
    sys.exit(1)


app = Flask(__name__,
            static_folder='../static',
            template_folder='../templates')

# --- 설정 (크롤링 파일 경로) ---
# 크롤링 결과 Excel 파일의 임시 저장 경로
# 'src/app/crawling' 폴더에 저장
CRAWL_FILE_PATH = os.path.join(os.path.dirname(__file__), 'crawling', 'coupang_reviews_web_temp.xlsx')


@app.route('/')
def index():
    """초기 HTML 템플릿 렌더링"""
    # hello.html은 src/templates에 있다고 가정
    return render_template('hello.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_review_api():
    """
    핵심 리뷰 분석 API
    1. 크롤링 (Crapping_module_ver1.py)
    2. 전처리 (readData.py 로직)
    3. AI 분석 (analyzer.py)
    """
    data = request.get_json()
    link = data.get('link')
    keyword = data.get('keyword', '용량, 배터리, 디자인') # 키워드가 없으면 기본값 사용

    if not link:
        return jsonify({"success": False, "message": "링크를 입력해주세요."}), 400

    try:
        # --- 1. 크롤링 (Crapping_module_ver1.py 실행) ---
        # Crapping_module_ver1.py의 메인 로직을 함수화하여 호출
        # (아래 2. 파일 수정 지침 참조)
        all_reviews = scrape_reviews_and_save(link, CRAWL_FILE_PATH) 
        
        if not all_reviews:
            return jsonify({"success": False, "message": "크롤링에 실패했거나 리뷰가 없습니다."}), 500

        # --- 2. 전처리 (readData.py 로직 통합) ---
        # 크롤링된 데이터를 바로 전처리
        df = pd.DataFrame(all_reviews)
        clean_df = df.dropna(subset=['내용'])
        string_data = clean_df['내용'].to_string(index=False, header=False, index_names=False)
        lines = string_data.strip().split('\n')
        final_string = ' '.join([line.strip() for line in lines])
        
        if not final_string:
            return jsonify({"success": False, "message": "리뷰 데이터 전처리 결과, 분석 가능한 내용이 없습니다."}), 500
        
        # --- 3. AI 분석 (analyzer.py 실행) ---
        # analyzer.py의 ReviewAnalasys 함수를 호출하며, 필요한 인수를 전달하도록 수정 필요
        # (아래 2. 파일 수정 지침 참조)
        # analyzer.py 내부에서 final_string을 전역 변수로 가져오는 대신, 인수로 전달해야 웹 환경에서 동적으로 동작
        
        # 임시로 JSON 문자열 반환을 가정
        json_response_str = ReviewAnalasys(keyword, final_string)
        
        # AI 응답이 JSON 형식이 아닐 경우 오류 처리 (필수)
        try:
            analysis_result = json.loads(json_response_str)
        except json.JSONDecodeError:
            print(f"[AI ERROR] JSON 파싱 실패: {json_response_str}")
            return jsonify({"success": False, "message": "AI 분석 결과 형식이 올바르지 않습니다."}), 500
        
        # --- 4. 결과 반환 ---
        return jsonify({
            "success": True,
            "keyword": keyword,
            "result_json": analysis_result # 파싱된 JSON 객체 반환
        })

    except Exception as e:
        print(f"서버 처리 중 오류 발생: {e}")
        return jsonify({"success": False, "message": f"서버 처리 오류: {str(e)}"}), 500

if __name__ == '__main__':
    # Flask 서버 실행
    app.run(debug=True)