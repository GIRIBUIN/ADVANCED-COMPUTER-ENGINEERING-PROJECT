import time
import pandas as pd
import traceback
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

# --- 설정 ---
TARGET_RATINGS = ['최고', '좋음', '보통', '별로', '나쁨']
MAX_REVIEWS_PER_RATING = 100

def setup_driver():
    """undetected_chromedriver 초기화"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    # 크롬 버전 고정 (사용자 환경에 맞게 변경 가능)
    driver = uc.Chrome(options=options, version_main=141)
    return driver

def extract_reviews(driver, current_rating_filter):
    """리뷰 데이터 추출 함수"""
    reviews_data = []
    articles = driver.find_elements(By.XPATH, "//article[.//div[contains(@class, 'sdp-review__article__list__help')]]")
    for article in articles:
        try:
            author = article.find_element(By.CSS_SELECTOR, "span[data-member-id]").text.strip()
            rating = len(article.find_elements(By.CSS_SELECTOR, "i.twc-bg-full-star"))
            date = article.find_element(By.XPATH, ".//div[i[contains(@class, 'twc-bg-full-star')]]/following-sibling::div").text.strip()
            product_option = article.find_element(By.CSS_SELECTOR, "div.twc-my-\\[16px\\]").text.strip()
            try: review_title = article.find_element(By.CSS_SELECTOR, "div.twc-mb-\\[8px\\].twc-font-bold").text.strip()
            except: review_title = ""
            try: review_body = article.find_element(By.CSS_SELECTOR, "div.twc-break-all").text.strip()
            except: review_body = ""
            try: helpful = int(article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__help").get_attribute("data-count"))
            except: helpful = 0
            reviews_data.append({
                "filter": current_rating_filter, "author": author, "rating": rating, "date": date,
                "product_option": product_option, "review_title": review_title, "review_body": review_body, "helpful_count": helpful
            })
        except: continue
    return reviews_data

def click_rating_filter(driver, wait, rating_name):
    """[V10 핵심] 별점 필터 클릭 로직 강화"""
    for attempt in range(3): # 재시도 횟수 3회로 증가
        try:
            print(f"['{rating_name}'] 필터 적용 시도... ({attempt+1}/3)")
            
            # 1. 드롭다운 버튼 찾기 및 클릭 (role='combobox' 활용)
            filter_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[role='combobox']")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_btn)
            time.sleep(0.5)
            # 일반 클릭 시도 후 실패하면 JS 클릭 시도
            try: filter_btn.click()
            except: driver.execute_script("arguments[0].click();", filter_btn)
            
            # 2. [중요] 옵션 리스트가 나타날 때까지 대기
            # 텍스트를 포함하는 리스트 아이템(li)이나 div 등이 보일 때까지 기다림
            option_xpath = f"//*[contains(text(), '{rating_name}') and not(contains(@class, 'selected'))]" 
            # 이미 선택된 '최고' 텍스트 등을 제외하기 위해 not(contains(@class, 'selected')) 같은 조건을 추가할 수도 있음.
            # 여기서는 가장 단순하게 텍스트로만 찾되, 클릭 가능한 상태인지 확인합니다.

            rating_option = wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
            
            # 3. 옵션 클릭
            # 안정성을 위해 JS 클릭 사용
            driver.execute_script("arguments[0].click();", rating_option)
            
            # 4. 클릭 후 필터가 적용되어 리스트가 갱신될 때까지 잠시 대기
            time.sleep(3)
            print(f"['{rating_name}'] 필터 적용 성공!")
            return True

        except Exception as e:
            print(f"[재시도] 필터 적용 실패: {str(e)[:50]}...")
            # 실패 시 혹시 열려있을 드롭다운을 닫기 위해 바탕화면 등을 클릭하는 동작을 추가할 수도 있음
            time.sleep(2)

    print(f"[최종 실패] '{rating_name}' 필터를 적용하지 못했습니다.")
    return False

def scrape_coupang(url):
    driver = None
    all_reviews = []
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        driver.get(url)
        print("[시작] 페이지 로딩 중...")

        review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
        ActionChains(driver).move_to_element(review_tab).click().perform()
        wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        print("[이동] 상품평 탭 진입 성공")
        time.sleep(2)

        for rating_name in TARGET_RATINGS:
            print(f"\n--- [{rating_name}] 리뷰 수집 시작 (목표: {MAX_REVIEWS_PER_RATING}개) ---")
            if not click_rating_filter(driver, wait, rating_name): continue

            rating_reviews = []
            visited_pages = set()

            while len(rating_reviews) < MAX_REVIEWS_PER_RATING:
                try:
                    try:
                         pagination = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-start and @data-end]")))
                         current_btn = pagination.find_element(By.XPATH, ".//button[contains(@class, 'twc-text-[#346aff]') and contains(@class, 'twc-font-bold')]")
                         current_page_num = int(current_btn.text.strip())
                    except: current_page_num = 1

                    if current_page_num not in visited_pages:
                        new_data = extract_reviews(driver, rating_name)
                        rating_reviews.extend(new_data)
                        visited_pages.add(current_page_num)
                        print(f"   -> {current_page_num}페이지: {len(new_data)}개 완료 (현재 별점 누적: {len(rating_reviews)}개)")

                    if len(rating_reviews) >= MAX_REVIEWS_PER_RATING:
                        print(f"   [완료] '{rating_name}' 목표 달성!")
                        break

                    next_target_btn = None
                    min_unvisited = float('inf')
                    try:
                        num_btns = pagination.find_elements(By.XPATH, ".//button[./span[string-length(text()) > 0]]")
                        for btn in num_btns:
                            p_num = int(btn.text.strip())
                            if p_num not in visited_pages and p_num < min_unvisited:
                                min_unvisited = p_num
                                next_target_btn = btn
                    except: pass

                    if next_target_btn:
                        driver.execute_script("arguments[0].click();", next_target_btn)
                        time.sleep(3)
                    else:
                        try:
                            current_start = pagination.get_attribute("data-start")
                            next_group_btn = driver.find_element(By.XPATH, "//div[@data-start and @data-end]/button[last()]")
                            if next_group_btn.is_enabled() and next_group_btn.get_attribute("disabled") is None:
                                driver.execute_script("arguments[0].click();", next_group_btn)
                                wait.until(lambda d: d.find_element(By.XPATH, "//div[@data-start]").get_attribute("data-start") != current_start)
                                time.sleep(3)
                            else:
                                print(f"   [종료] 더 이상 페이지 없음.")
                                break
                        except:
                             print(f"   [종료] 페이지네이션 끝.")
                             break
                except Exception:
                    break 
            all_reviews.extend(rating_reviews[:MAX_REVIEWS_PER_RATING])

    except Exception as e:
        print(f"\n[오류] {e}")
        traceback.print_exc()
    finally:
        if driver:
            print(f"\n[종료] 총 {len(all_reviews)}개 수집됨.")
            try: driver.quit()
            except: pass
    return all_reviews

if __name__ == "__main__":
    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    reviews = scrape_coupang(target_url)
    if reviews:
        df = pd.DataFrame(reviews)
        df.to_excel("coupang_reviews_final_v10.xlsx", index=False)
        print("[저장 완료]")