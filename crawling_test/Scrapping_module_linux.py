import time
import pandas as pd
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup 
from multiprocessing import Manager, freeze_support

# --- 설정 ---
TARGET_RATINGS = ['최고', '좋음', '보통', '별로', '나쁨']
MAX_REVIEWS_PER_RATING = 100

def setup_driver(lock=None):
    options = uc.ChromeOptions()
    
    # [참고] 화면을 보려면 아래 줄 앞에 #을 붙이세요.
    # options.add_argument("--headless=new") 
    
    # 봇 탐지 회피용 설정
    options.add_argument("--no-sandbox") 
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.page_load_strategy = 'eager'
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    driver = None
    
    if lock: lock.acquire()
    
    try:
        driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"   [드라이버 로드 재시도] 에러: {e}")
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
    reviews_data = []
    review_article_xpath = "//article[contains(@class, 'sdp-review__article__list') or contains(@class, 'twc-pt-[16px]')]"
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, review_article_xpath)))
    except TimeoutException: return []
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
            if not product_option: product_option = get_text("div.twc-my-\\[16px\\]")
            review_title = get_text("div.sdp-review__article__list__headline")
            if not review_title: review_title = get_text("div.twc-mb-\\[8px\\].twc-font-bold")
            review_body = get_text("div.sdp-review__article__list__review__content")
            if not review_body: review_body = get_text("div.twc-break-all")
            helpful = 0
            try: 
                help_div = article.select_one("div.sdp-review__article__list__help")
                if help_div and help_div.has_attr("data-count"): helpful = int(help_div["data-count"])
                else:
                    help_text_div = article.find("div", string=lambda text: text and "명에게 도움되었습니다" in text)
                    if help_text_div:
                        text = help_text_div.get_text(strip=True)
                        helpful = int(text.split('명')[0].replace(',', '').strip())
            except: pass
            reviews_data.append({"별점필터": current_rating_filter, "작성자": author, "평점": rating, "날짜": date, "구매옵션": product_option, "제목": review_title, "내용": review_body, "도움됨": helpful})
        except: continue
    return reviews_data

def apply_rating_filter(driver, wait, rating_name):
    try:
        filter_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='combobox']")))
        if rating_name in filter_btn.text and "모든 별점" not in filter_btn.text: return True
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_btn)
        time.sleep(1) 
        driver.execute_script("arguments[0].click();", filter_btn)
        popup = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        option = popup.find_element(By.XPATH, f".//div[contains(text(), '{rating_name}')]")
        driver.execute_script("arguments[0].click();", option)
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        time.sleep(1.5) 
        return True
    except Exception: return False

def scrape_single_rating(target_url, rating_name, lock):
    start_delay = random.uniform(0.5, 2.0)
    time.sleep(start_delay)
    
    driver = setup_driver(lock)
    if not driver: return []

    collected = []
    print(f"🚀 START: [{rating_name}] 브라우저 켜짐. 수집 시작!")
    
    try:
        wait = WebDriverWait(driver, 20)
        driver.get(target_url)
        
        try:
            review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
            ActionChains(driver).move_to_element(review_tab).click().perform()
        except TimeoutException:
            print(f"FAIL: [{rating_name}] 상품평 탭 못 찾음")
            return []

        review_section = wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        
        if not apply_rating_filter(driver, wait, rating_name): return []

        visited_pages = set()
        consecutive_failures = 0

        while len(collected) < MAX_REVIEWS_PER_RATING:
            try:
                pagination_xpath = "//div[@data-page and @data-start and @data-end]"
                is_new_ui = False; pagination = None
                try:
                    pagination = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, pagination_xpath)))
                    if "twc-mt-[24px]" in pagination.get_attribute("class"): is_new_ui = True
                except: pass 
                current_page = 1
                if pagination:
                    try:
                        if is_new_ui: current_page = int(pagination.find_element(By.CSS_SELECTOR, "button[class*='twc-text-[#346aff]']").text.strip())
                        else: current_page = int(pagination.find_element(By.CSS_SELECTOR, "button.selected").text.strip())
                    except: pass
                if current_page not in visited_pages:
                    new_reviews = extract_reviews(driver, rating_name)
                    if new_reviews:
                        collected.extend(new_reviews)
                        visited_pages.add(current_page)
                        consecutive_failures = 0
                        print(f"✅ ING: [{rating_name}] {current_page}페이지 {len(new_reviews)}개 완료")
                    else:
                        if pagination is None and current_page == 1: break 
                        consecutive_failures += 1
                if len(collected) >= MAX_REVIEWS_PER_RATING: break
                if pagination is None: break
                if pagination:
                    next_btn = None; min_val = float('inf')
                    buttons = pagination.find_elements(By.XPATH, ".//button[span]") if is_new_ui else pagination.find_elements(By.CSS_SELECTOR, "button.sdp-review__article__page__num")
                    for btn in buttons:
                        try:
                            val = int(btn.text.strip())
                            if val not in visited_pages and val > current_page and val < min_val: min_val = val; next_btn = btn
                        except: continue
                    if next_btn:
                        try: next_btn.click()
                        except: driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(random.uniform(1.0, 1.5)) 
                    else:
                        try:
                            next_group = pagination.find_element(By.XPATH, ".//button[.//svg[not(contains(@class, 'twc-rotate'))]]")
                            if next_group.is_enabled():
                                try: next_group.click()
                                except: driver.execute_script("arguments[0].click();", next_group)
                                time.sleep(random.uniform(1.5, 2.0))
                            else: break
                        except: break
                else:
                    if consecutive_failures >= 3: break
                    time.sleep(1)
            except:
                consecutive_failures += 1
                if consecutive_failures >= 5: break
                time.sleep(1)
    except Exception as e:
        print(f"ERROR: [{rating_name}] {e}")
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
    
    print("=== [Linux] 리뷰 수집 시작 (시간 측정 추가) ===")
    
    m = Manager()
    lock = m.Lock()

    tasks = [(target_url, rating, lock) for rating in TARGET_RATINGS]
    all_results = []

    # 전체 소요 시간 측정 시작
    total_start_time = time.time()

    for i, task in enumerate(tasks):
        rating_name = task[1]
        print(f"\n>>> [{i+1}/5] '{rating_name}' 리뷰 수집 시작...")
        
        # [구간 시간 측정 시작]
        step_start_time = time.time()
        
        result = scrape_wrapper(task)
        all_results.extend(result)
        
        # [구간 시간 측정 종료]
        step_end_time = time.time()
        step_duration = step_end_time - step_start_time
        print(f"   └─ [{rating_name}] 완료! (걸린 시간: {step_duration:.2f}초)")

        time.sleep(2)

    # 전체 소요 시간 측정 종료
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time

    print(f"\n=== 전체 수집 종료 (총 소요 시간: {total_duration:.2f}초) ===")

    if all_results:
        df = pd.DataFrame(all_results)
        file_name = "coupang_reviews_linux.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\n🎉 [전체 완료] 총 {len(all_results)}개의 리뷰 저장 완료!")
    else:
        print("\n[알림] 수집된 리뷰가 없습니다.")