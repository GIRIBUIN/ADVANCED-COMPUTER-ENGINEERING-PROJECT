# src/app/facade.py

from .crawling import Crapping_module_ver1 as crawl_module
from .ai import analyzer as ai_module
from .db import db
import pandas as pd
import hashlib
from multiprocessing import Pool, Manager
import os
import json

def analyze_reviews(link, keywords):
    """
    [리뷰 분석]
    분석 결과는 DB에 저장하지 않기로 했음.
    크롤링과 AI 분석만 수행하고 결과를 반환.
    """
    try:
        # --- 카테고리, 제품명 ---
        print("LOG: Fetching metadata...")
        metadata = crawl_module.get_product_metadata(link)
        product_name = metadata.get('product_name', '알 수 없는 제품')
        category_name = metadata.get('category_name', '기타')

        # --- 크롤링 ---
        print("LOG: Starting disposable analysis (crawl)...")
        manager = Manager()
        lock = manager.Lock()
        tasks = [(link, rating, lock) for rating in crawl_module.TARGET_RATINGS]

        num_processes = min(len(tasks), os.cpu_count() or 4)

        with Pool(processes=num_processes) as pool:
            results_list = pool.starmap(crawl_module.scrape_single_rating, tasks)
        all_reviews = [item for sublist in results_list for item in sublist]
        
        if not all_reviews:
            raise Exception("크롤링 결과 리뷰를 수집하지 못했습니다.")

        # --- AI 분석 ---
        print("LOG: Starting disposable analysis (AI)...")
        temp_df = pd.DataFrame(all_reviews)
        if '내용' not in temp_df.columns:
             raise Exception("수집된 리뷰 데이터 형식이 올바르지 않습니다.")
             
        clean_df = temp_df.dropna(subset=['내용'])

        review_string = ' '.join(clean_df['내용'].astype(str).tolist())[:15000] 

        ai_response_json_str = ai_module.analyze_reviews(keywords, review_string)

        try:
            ai_data = json.loads(ai_response_json_str)
            ai_data['product_name'] = product_name 
            final_analysis_text = json.dumps(ai_data, ensure_ascii=False)
        except:
            final_analysis_text = ai_response_json_str

        # --- analysis_id : 저장 할 때 필요해서 생성 ---
        keywords_str = ",".join(sorted(keywords))
        unique_string = link + keywords_str
        analysis_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
        
        result_data = {
            "analysis_id": analysis_id,
            "url": link,
            "keywords": keywords,
            "analysis_text": str(final_analysis_text), # JSON -> text
            "category_name": category_name
        }

        return {"status": "success", "data": result_data}

    except Exception as e:
        print(f"ERROR in analyze_reviews_only: {e}")
        return {"status": "error", "message": str(e)}


def save_analysis_to_library(analysis_data, user_id):
    """
    [라이브러리 저장]
    'analyze_reviews'하고 저장
    """
    db_conn = db.get_db()
    
    # 저장할 데이터 추출
    analysis_id = analysis_data.get('analysis_id')
    url = analysis_data.get('url')
    analysis_text = analysis_data.get('analysis_text')
    if isinstance(analysis_text, dict):
            # dict -> text
            analysis_text = json.dumps(analysis_text, ensure_ascii=False)

    keywords = analysis_data.get('keywords')
    category_name = analysis_data.get('category_name', '기타')

    try:
        cursor = db_conn.cursor()
        
        # ANALYSES 테이블 확인/생성
        if not db.isitem_from_library(analysis_id):
            category_id = db.find_or_create_category(category_name)
            keyword_ids = db.find_or_create_keywords(keywords)
            
            db.save_analysis(analysis_id, url, analysis_text, category_id)
            db.link_analysis_to_keywords(analysis_id, keyword_ids)

        # LIBRARY 테이블 연결
        if not db.find_library_item(user_id, analysis_id):
            db.add_to_library(user_id, analysis_id)
        
        db_conn.commit()
        return {"status": "success", "message": "라이브러리에 저장되었습니다."}

    except Exception as e:
        db_conn.rollback()
        print(f"ERROR in save_analysis_to_library: {e}")
        return {"status": "error", "message": str(e)}