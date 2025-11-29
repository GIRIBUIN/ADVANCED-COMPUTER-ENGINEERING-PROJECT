# RA/review_analyzer/facade.py

"""
애플리케이션의 핵심 비즈니스 로직을 처리하는 '퍼사드(Facade)' 모듈입니다.
크롤링, AI 분석, DB 저장 등 여러 모듈의 기능을 조합하여 transaction을 제어합니다.
"""

# 현재 패키지 내의 모듈들을 상대 경로로 임포트합니다.
from .crawling import Crapping_module_ver1 as crawl_module
from .ai import analyzer as ai_module
from .db import db

# 기본 라이브러리
import pandas as pd
import hashlib
from multiprocessing import Pool, Manager
import os
import json
import traceback # 오류 로깅을 위해 추가

def analyze_reviews(link, keywords):
    """
    주어진 URL과 키워드로 리뷰를 분석하는 전체 과정을 수행합니다.
    (병렬 크롤링 -> 데이터 취합 -> AI 분석)
    """
    try:
        # --- 크롤링 ---
        print("LOG: Starting parallel crawling...")
        manager = Manager()
        lock = manager.Lock()
        tasks = [(link, rating, lock) for rating in crawl_module.TARGET_RATINGS]

        # 동시에 실행할 프로세스 수 결정 (CPU 코어 수와 작업 수 중 작은 값, 최대 4개로 제한)
        num_processes = 2

        all_reviews = []
        with Pool(processes=num_processes) as pool:
            results_list = pool.map(crawl_module.scrape_wrapper, tasks)
            for result in results_list:
                all_reviews.extend(result)
        
        if not all_reviews:
            raise Exception("크롤링을 통해 수집된 리뷰가 없습니다.")

        # --- AI 분석 ---
        print("LOG: Starting AI analysis...")
        temp_df = pd.DataFrame(all_reviews)
        if '내용' not in temp_df.columns:
             raise Exception("수집된 리뷰 데이터에 '내용' 컬럼이 없습니다.")
             
        clean_df = temp_df.dropna(subset=['내용'])
        review_string = ' '.join(clean_df['내용'].astype(str).tolist())[:15000] 
        ai_response_json_str = ai_module.analyze_reviews(keywords, review_string)

        try:
            ai_data = json.loads(ai_response_json_str)
            # 참고: 현재 크롤링 모듈은 상품명, 카테고리를 가져오지 않으므로 해당 로직은 제거됨
            # ai_data['product_name'] = product_name 
            final_analysis_text = json.dumps(ai_data, ensure_ascii=False)
        except json.JSONDecodeError:
            # AI가 JSON 형식이 아닌 일반 텍스트를 반환한 경우
            final_analysis_text = ai_response_json_str

        # --- 최종 결과 데이터 생성 ---
        keywords_str = ",".join(sorted(keywords))
        unique_string = link + keywords_str
        analysis_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
        
        result_data = {
            "analysis_id": analysis_id,
            "url": link,
            "keywords": keywords,
            "analysis_text": final_analysis_text,
            # 카테고리 정보는 DB 저장 시 '기타'로 기본 처리되므로 여기서는 제외
            # "category_name": category_name 
        }

        return {"status": "success", "data": result_data}

    except Exception as e:
        print(f"ERROR in analyze_reviews: {e}")
        traceback.print_exc() # 개발 중 상세 오류 확인을 위해 스택 트레이스 출력
        return {"status": "error", "message": str(e)}


def save_analysis_to_library(analysis_data, user_id):
    """
    분석된 결과를 데이터베이스의 라이브러리에 저장합니다.
    """
    db_conn = db.get_db()
    
    analysis_id = analysis_data.get('analysis_id')
    url = analysis_data.get('url')
    analysis_text = analysis_data.get('analysis_text')
    keywords = analysis_data.get('keywords')
    
    # 'category_name'이 분석 데이터에 없을 경우를 대비하여 기본값 '기타' 사용
    category_name = analysis_data.get('category_name', '기타')

    try:
        # 분석 결과가 DB에 없으면 새로 저장
        if not db.does_analysis_exist(analysis_id):
            category_id = db.find_or_create_category(category_name)
            keyword_ids = db.find_or_create_keywords(keywords)
            db.save_analysis(analysis_id, url, analysis_text, category_id)
            db.link_analysis_to_keywords(analysis_id, keyword_ids)

        # 사용자의 라이브러리에 연결
        if not db.find_library_item(user_id, analysis_id):
            db.add_to_library(user_id, analysis_id)
        
        db_conn.commit()
        return {"status": "success", "message": "라이브러리에 저장되었습니다."}

    except Exception as e:
        db_conn.rollback()
        print(f"ERROR in save_analysis_to_library: {e}")
        traceback.print_exc()
        return {"status": "error", "message": "라이브러리 저장 중 오류가 발생했습니다."}