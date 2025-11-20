import time
import pandas as pd
import traceback
import random
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# 병렬 처리 및 프로세스 간 동기화를 위한 라이브러리
from multiprocessing import Pool, freeze_support, Manager

# --- 설정 ---
TARGET_RATINGS = ['최고', '좋음', '보통', '별로', '나쁨']
MAX_REVIEWS_PER_RATING = 100

def setup_driver(lock=None):
    """
    undetected_chromedriver 초기화 (Headless 적용 & 충돌 방지)
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    # [속도 향상] Headless 모드 적용 (탐지 우회를 위해 'new' 옵션 사용)
    # 만약 실행 시 차단되거나 리뷰가 0개라면 이 줄을 주석 처리하세요.
    #options.add_argument("--headless=new") 
    
    # 리소스 절약 옵션
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = None
    
    # 드라이버 파일 충돌 방지를 위해 락 획득
    if lock: lock.acquire()
    
    try:
        # 특정 버전(141) 지정 (사용자 환경에 맞춤)
        driver = uc.Chrome(options=options, version_main=141)
    except Exception as e:
        try:
            # 실패 시 자동 감지 모드로 재시도
            driver = uc.Chrome(options=options)
        except Exception as e2:
            print(f"   [치명적 오류] 드라이버 로드 실패: {e2}")
    finally:
        # 드라이버 로드 후 락 해제 (다른 프로세스 진입 허용)
        if lock:
            time.sleep(1) 
            lock.release()
            
    return driver

def extract_reviews(driver, current_rating_filter):
    """리뷰 데이터 추출 (구형 UI / 신형 UI 호환)"""
    reviews_data = []
    
    # 리뷰 아이템을 찾는 포괄적인 XPath
    review_article_xpath = "//article[contains(@class, 'sdp-review__article__list') or contains(@class, 'twc-pt-[16px]')]"

    try:
        # 요소가 로드될 때까지 짧게 대기
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, review_article_xpath))
        )
    except TimeoutException:
        return []

    articles = driver.find_elements(By.XPATH, review_article_xpath)
    
    for article in articles:
        try:
            def get_text(selector):
                try: return article.find_element(By.CSS_SELECTOR, selector).text.strip()
                except: return ""

            # 작성자
            author = article.find_element(By.CSS_SELECTOR, "span[data-member-id]").text.strip()
            
            # 평점
            rating = len(article.find_elements(By.CSS_SELECTOR, "i.twc-bg-full-star"))
            
            # 날짜
            date = get_text("div.sdp-review__article__list__info__product-info__reg-date")
            if not date: 
                date = article.find_element(By.XPATH, ".//div[i[contains(@class, 'twc-bg-full-star')]]/following-sibling::div").text.strip()
            
            # 구매옵션
            product_option = get_text("div.sdp-review__article__list__info__product-info__name")
            if not product_option: 
                product_option = get_text("div.twc-my-\\[16px\\]")
            
            # 리뷰 제목
            review_title = get_text("div.sdp-review__article__list__headline")
            if not review_title: 
                review_title = get_text("div.twc-mb-\\[8px\\].twc-font-bold")

            # 리뷰 내용
            review_body = get_text("div.sdp-review__article__list__review__content")
            if not review_body: 
                review_body = get_text("div.twc-break-all")
            
            # 도움됨 카운트
            helpful = 0
            try: 
                helpful = int(article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__help").get_attribute("data-count"))
            except: 
                try:
                    helpful_text = article.find_element(By.XPATH, ".//div[contains(text(), '명에게 도움되었습니다.')]").text
                    helpful = int(helpful_text.split('명')[0].replace(',', '').strip())
                except:
                    pass
            
            reviews_data.append({
                "별점필터": current_rating_filter,
                "작성자": author, "평점": rating, "날짜": date, "구매옵션": product_option,
                "제목": review_title, "내용": review_body, "도움됨": helpful
            })
        except: 
            continue
    return reviews_data

def apply_rating_filter(driver, wait, rating_name):
    """별점 필터 적용"""
    try:
        filter_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='combobox']")))
        
        if rating_name in filter_btn.text and "모든 별점" not in filter_btn.text:
            return True

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_btn)
        time.sleep(0.5)
        filter_btn.click()
        
        popup = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        option = popup.find_element(By.XPATH, f".//div[contains(text(), '{rating_name}')]")
        option.click()
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        time.sleep(1.5) # 필터 적용 후 로딩 대기
        return True
    except Exception as e:
        # print(f"[{rating_name}] 필터 적용 실패: {str(e)[:50]}")
        return False

def scrape_single_rating(target_url, rating_name, lock):
    """스마트 대기(Dynamic Wait)를 적용하여 속도를 최적화한 수집 함수"""
    
    # 초기 진입 시 프로세스 몰림 방지 (0.5~2초 랜덤 대기)
    start_delay = random.uniform(0.5, 2.0)
    time.sleep(start_delay)
    
    driver = setup_driver(lock)
    if not driver: return []

    collected = []
    print(f"START: [{rating_name}] (Headless) 수집 시작")
    
    try:
        # [속도 최적화] 기본 대기 시간 설정
        wait = WebDriverWait(driver, 20)
        driver.get(target_url)
        
        # 상품평 탭 클릭
        try:
            review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
            ActionChains(driver).move_to_element(review_tab).click().perform()
        except TimeoutException:
            print(f"FAIL: [{rating_name}] 상품평 탭을 찾을 수 없음")
            return []

        # 리뷰 섹션 로딩
        review_section = wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        
        # 별점 필터 적용
        if not apply_rating_filter(driver, wait, rating_name):
            print(f"FAIL: [{rating_name}] 필터 적용 실패")
            return []

        visited_pages = set()
        consecutive_failures = 0

        while len(collected) < MAX_REVIEWS_PER_RATING:
            try:
                # 페이지네이션 바 감지 (최대 5초만 대기)
                pagination_xpath = "//div[@data-page and @data-start and @data-end]"
                is_new_ui = False 
                pagination = None
                
                try:
                    pagination = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, pagination_xpath))
                    )
                    if "twc-mt-[24px]" in pagination.get_attribute("class"):
                        is_new_ui = True
                except TimeoutException:
                    pass # 없으면 단일 페이지일 수 있음

                # 현재 페이지 번호 파악
                current_page = 1
                if pagination:
                    try:
                        if is_new_ui:
                            current_page = int(pagination.find_element(By.CSS_SELECTOR, "button[class*='twc-text-[#346aff]']").text.strip())
                        else:
                            current_page = int(pagination.find_element(By.CSS_SELECTOR, "button.selected").text.strip())
                    except: pass

                # --- 리뷰 수집 ---
                if current_page not in visited_pages:
                    new_reviews = extract_reviews(driver, rating_name)
                    if new_reviews:
                        collected.extend(new_reviews)
                        visited_pages.add(current_page)
                        consecutive_failures = 0
                        print(f"ING: [{rating_name}] {current_page}페이지 {len(new_reviews)}개 (누적: {len(collected)})")
                    else:
                        if pagination is None and current_page == 1:
                            print(f"INFO: [{rating_name}] 리뷰 없음 -> 종료")
                            break 
                        consecutive_failures += 1
                
                if len(collected) >= MAX_REVIEWS_PER_RATING: break

                # --- 다음 페이지 이동 ---
                if pagination:
                    next_btn = None
                    min_val = float('inf')

                    if is_new_ui:
                        buttons = pagination.find_elements(By.XPATH, ".//button[span]")
                    else:
                        buttons = pagination.find_elements(By.CSS_SELECTOR, "button.sdp-review__article__page__num")
                        
                    for btn in buttons:
                        try:
                            val = int(btn.text.strip())
                            if val not in visited_pages and val > current_page and val < min_val:
                                min_val = val
                                next_btn = btn
                        except: continue
                    
                    if next_btn:
                        try: next_btn.click()
                        except: driver.execute_script("arguments[0].click();", next_btn)
                        
                        # [속도 최적화] 페이지 로딩 대기 (봇 탐지 방지용 최소 딜레이 포함)
                        time.sleep(random.uniform(1.5, 2.5)) 
                        
                    else:
                        # 다음 그룹(>) 버튼 처리
                        try:
                            next_group = pagination.find_element(By.XPATH, ".//button[.//svg[not(contains(@class, 'twc-rotate'))]]")
                            if next_group.is_enabled():
                                try: next_group.click()
                                except: driver.execute_script("arguments[0].click();", next_group)
                                time.sleep(random.uniform(2.0, 3.0))
                            else:
                                break
                        except: break
                else:
                    if consecutive_failures >= 3: break
                    time.sleep(2)

            except Exception:
                consecutive_failures += 1
                if consecutive_failures >= 5: break
                time.sleep(1)

    except Exception as e:
        print(f"ERROR: [{rating_name}] 오류 발생: {e}")
        traceback.print_exc()
    finally:
        if driver:
            try: driver.quit()
            except: pass
    
    return collected[:MAX_REVIEWS_PER_RATING]

# 병렬 처리를 위한 래퍼 함수
def scrape_wrapper(args):
    return scrape_single_rating(*args)

if __name__ == "__main__":
    # Windows 멀티프로세싱 필수 설정
    freeze_support()

    # 대상 URL (여기에 원하시는 상품 URL을 입력하세요)
    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    
    print("=== 병렬 리뷰 스크래핑 시작 (프로세스 5개 / Headless) ===")
    
    # 프로세스 간 공유 락 생성
    m = Manager()
    lock = m.Lock()

    # 작업 목록 생성
    tasks = [(target_url, rating, lock) for rating in TARGET_RATINGS]

    start_time = time.time()
    all_results = []

    # 프로세스 풀 가동 (5개 동시 실행)
    with Pool(processes=len(TARGET_RATINGS)) as pool:
        results_list = pool.map(scrape_wrapper, tasks)
        for result in results_list:
            all_results.extend(result)

    end_time = time.time()
    print(f"\n=== 전체 수집 종료 (소요 시간: {end_time - start_time:.2f}초) ===")

    if all_results:
        df = pd.DataFrame(all_results)
        file_name = "coupang_reviews_final_parallel.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\n🎉 [전체 완료] 총 {len(all_results)}개의 리뷰가 '{file_name}'에 저장되었습니다!")
    else:
        print("\n[알림] 수집된 리뷰가 없습니다. (Headless 탐지 여부 확인 필요)")