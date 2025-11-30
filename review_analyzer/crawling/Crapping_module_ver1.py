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
from bs4 import BeautifulSoup # 데이터 추출 가속용

# 병렬 처리 및 프로세스 간 동기화를 위한 라이브러리
from multiprocessing import Pool, freeze_support, Manager

# --- 설정 ---
TARGET_RATINGS = ['최고', '좋음', '보통', '별로', '나쁨']
MAX_REVIEWS_PER_RATING = 100

def setup_driver(lock=None):
    """
    undetected_chromedriver 초기화 
    (Headless + Eager Mode + 이미지 차단 적용)
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    # [핵심 변경 1] 페이지 로딩 전략: Eager
    # DOM(HTML 구조)만 로드되면 이미지/CSS 로딩을 기다리지 않고 즉시 제어권을 넘김
    options.page_load_strategy = 'eager'
    
    # [핵심 변경 2] 이미지 로딩 아예 차단 (네트워크 대역폭 및 렌더링 시간 절약)
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # [속도 향상] Headless 모드 (필요시 주석 해제하여 사용)
    # options.add_argument("--headless=new") 
    
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = None
    
    if lock: lock.acquire()
    
    try:
        driver = uc.Chrome(options=options, version_main=141)
    except Exception as e:
        try:
            driver = uc.Chrome(options=options)
        except Exception as e2:
            print(f"   [치명적 오류] 드라이버 로드 실패: {e2}")
    finally:
        if lock:
            time.sleep(1) 
            lock.release()
            
    return driver

def extract_reviews(driver, current_rating_filter):
    """
    BeautifulSoup을 이용한 고속 데이터 추출
    """
    reviews_data = []
    
    # 리뷰 아이템을 찾는 XPath
    review_article_xpath = "//article[contains(@class, 'sdp-review__article__list') or contains(@class, 'twc-pt-[16px]')]"

    try:
        # Eager 모드여도 데이터가 실제 DOM에 꽂힐 때까지는 기다려야 함
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, review_article_xpath))
        )
    except TimeoutException:
        return []

    # Selenium은 HTML 소스만 덤프하고, 분석은 Python(BeautifulSoup)이 수행
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    articles = soup.find_all('article', class_=lambda x: x and ('sdp-review__article__list' in x or 'twc-pt-[16px]' in x))
    
    for article in articles:
        try:
            def get_text(selector):
                el = article.select_one(selector)
                return el.get_text(strip=True) if el else ""

            author_el = article.select_one("span[data-member-id]")
            author = author_el.get_text(strip=True) if author_el else ""
            
            rating = len(article.select("i.twc-bg-full-star"))
            
            date = get_text("div.sdp-review__article__list__info__product-info__reg-date")
            if not date:
                try:
                    stars_div = article.select_one("div:has(> i.twc-bg-full-star)")
                    if stars_div:
                        date_div = stars_div.find_next_sibling("div")
                        if date_div: date = date_div.get_text(strip=True)
                except: pass
            
            product_option = get_text("div.sdp-review__article__list__info__product-info__name")
            if not product_option: 
                product_option = get_text("div.twc-my-\\[16px\\]")
            
            review_title = get_text("div.sdp-review__article__list__headline")
            if not review_title: 
                review_title = get_text("div.twc-mb-\\[8px\\].twc-font-bold")

            review_body = get_text("div.sdp-review__article__list__review__content")
            if not review_body: 
                review_body = get_text("div.twc-break-all")
            
            helpful = 0
            try: 
                help_div = article.select_one("div.sdp-review__article__list__help")
                if help_div and help_div.has_attr("data-count"):
                    helpful = int(help_div["data-count"])
                else:
                    help_text_div = article.find("div", string=lambda text: text and "명에게 도움되었습니다" in text)
                    if help_text_div:
                        text = help_text_div.get_text(strip=True)
                        helpful = int(text.split('명')[0].replace(',', '').strip())
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
    """별점 필터 적용 (JS 강제 클릭)"""
    try:
        filter_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='combobox']")))
        
        if rating_name in filter_btn.text and "모든 별점" not in filter_btn.text:
            return True

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_btn)
        time.sleep(1) 
        driver.execute_script("arguments[0].click();", filter_btn)
        
        popup = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        option = popup.find_element(By.XPATH, f".//div[contains(text(), '{rating_name}')]")
        
        driver.execute_script("arguments[0].click();", option)
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        time.sleep(1.5) 
        return True
    except Exception as e:
        print(f"   FAIL: [{rating_name}] 필터 진입 실패")
        return False

def scrape_single_rating(target_url, rating_name, lock):
    """최적화된 수집 함수 (Eager load + BeautifulSoup + Parallel)"""
    
    start_delay = random.uniform(0.5, 2.0)
    time.sleep(start_delay)
    
    driver = setup_driver(lock)
    if not driver: return []

    collected = []
    print(f"START: [{rating_name}] 수집 시작")
    
    try:
        wait = WebDriverWait(driver, 20)
        driver.get(target_url)
        
        try:
            review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
            ActionChains(driver).move_to_element(review_tab).click().perform()
        except TimeoutException:
            print(f"FAIL: [{rating_name}] 상품평 탭을 찾을 수 없음")
            return []

        review_section = wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        
        if not apply_rating_filter(driver, wait, rating_name):
            print(f"FAIL: [{rating_name}] 필터 적용 실패")
            return []

        visited_pages = set()
        consecutive_failures = 0

        while len(collected) < MAX_REVIEWS_PER_RATING:
            try:
                # 페이지네이션 로딩 대기
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
                    pass 

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
                            print(f"INFO: [{rating_name}] 리뷰가 존재하지 않음 -> 종료")
                            break 
                        consecutive_failures += 1
                
                if len(collected) >= MAX_REVIEWS_PER_RATING: break

                if pagination is None:
                    if len(collected) > 0:
                        print(f"INFO: [{rating_name}] 단일 페이지 수집 완료. 종료.")
                    break

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
                        # JS Click 사용 (Eager 모드에서 레이아웃 이동 시 안정성 확보)
                        try: next_btn.click()
                        except: driver.execute_script("arguments[0].click();", next_btn)
                        
                        # [최적화] 페이지 이동 대기 시간을 조금 더 줄임 (이미지 로딩 안 하므로)
                        time.sleep(random.uniform(1.0, 1.5)) 
                    else:
                        try:
                            next_group = pagination.find_element(By.XPATH, ".//button[.//svg[not(contains(@class, 'twc-rotate'))]]")
                            if next_group.is_enabled():
                                try: next_group.click()
                                except: driver.execute_script("arguments[0].click();", next_group)
                                time.sleep(random.uniform(1.5, 2.0))
                            else:
                                print(f"INFO: [{rating_name}] 마지막 페이지 도달 (총 {len(collected)}개). 종료.")
                                break
                        except:
                            print(f"INFO: [{rating_name}] 더 이상 이동할 페이지가 없습니다 (총 {len(collected)}개). 종료.")
                            break
                else:
                    if consecutive_failures >= 3: break
                    time.sleep(1)

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

def scrape_wrapper(args):
    return scrape_single_rating(*args)

if __name__ == "__main__":
    freeze_support()

    target_url = "https://www.coupang.com/vp/products/7666070794?itemId=26528256734&searchId=feed-916be5672b844ae3a868a9ae4de0a60d-view_together_ads-P7224339339&vendorItemId=93409074156&sourceType=SDP_ADS&clickEventId=42651fd0-cb6e-11f0-bf3a-f1516b466eb7"
    
    print("=== 병렬 리뷰 스크래핑 시작 (Eager Mode + Image Block + BS4) ===")
    
    m = Manager()
    lock = m.Lock()

    tasks = [(target_url, rating, lock) for rating in TARGET_RATINGS]

    start_time = time.time()
    all_results = []

    with Pool(processes=len(TARGET_RATINGS)) as pool:
        results_list = pool.map(scrape_wrapper, tasks)
        for result in results_list: 
            all_results.extend(result)

    end_time = time.time()
    print(f"\n=== 전체 수집 종료 (소요 시간: {end_time - start_time:.2f}초) ===")

    if all_results:
        df = pd.DataFrame(all_results)
        file_name = "coupang_reviews_final_speedup.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\n🎉 [전체 완료] 총 {len(all_results)}개의 리뷰가 '{file_name}'에 저장되었습니다!")
    else:
        print("\n[알림] 수집된 리뷰가 없습니다.")