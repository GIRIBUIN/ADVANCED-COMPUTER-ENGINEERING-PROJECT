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

def setup_driver():
    """undetected_chromedriver 초기화 (버전 고정)"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    # [중요] 사용자 환경에 맞춰 크롬 버전 고정
    driver = uc.Chrome(options=options, version_main=141)
    return driver

def extract_reviews(driver):
    """현재 페이지에 로드된 리뷰들을 추출"""
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
                "author": author, "rating": rating, "date": date, "product_option": product_option,
                "review_title": review_title, "review_body": review_body, "helpful_count": helpful
            })
        except Exception: continue
            
    return reviews_data

def scrape_coupang(url):
    driver = None
    all_reviews = []
    visited_pages = set() # [V7 추가] 방문한 페이지 번호를 기억하는 집합

    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        driver.get(url)
        print("[시작] 상품 페이지 로딩 중...")

        # 1. '상품평' 탭 클릭
        review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
        ActionChains(driver).move_to_element(review_tab).click().perform()
        wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        print("[이동] 상품평 탭 진입 성공")
        time.sleep(2)

        while True: # [메인 루프] 페이지 그룹 반복
            
            # [V7 핵심 변경] 현재 그룹 내에서 방문 안 한 페이지 순차 탐색
            while True:
                try:
                    pagination = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-start and @data-end]")))
                    
                    # 2-1. 현재 페이지 번호 확인 및 수집
                    current_btn = pagination.find_element(By.XPATH, ".//button[contains(@class, 'twc-text-[#346aff]') and contains(@class, 'twc-font-bold')]")
                    current_page_num = int(current_btn.text.strip())

                    if current_page_num not in visited_pages:
                        print(f"[수집] {current_page_num} 페이지 수집 시작...")
                        current_reviews = extract_reviews(driver)
                        all_reviews.extend(current_reviews)
                        visited_pages.add(current_page_num)
                        print(f"       -> {len(current_reviews)}개 완료 (누적 {len(all_reviews)}개)")

                    # 2-2. 현재 그룹에서 '아직 방문하지 않은' 가장 작은 페이지 번호 찾기
                    num_btns = pagination.find_elements(By.XPATH, ".//button[./span[string-length(text()) > 0]]")
                    next_target_btn = None
                    min_unvisited_page = float('inf')

                    for btn in num_btns:
                        page_num = int(btn.text.strip())
                        if page_num not in visited_pages:
                            # 방문 안 한 페이지 중 가장 작은 페이지를 우선 타겟으로 설정
                            if page_num < min_unvisited_page:
                                min_unvisited_page = page_num
                                next_target_btn = btn
                    
                    # 2-3. 타겟 페이지가 있으면 이동
                    if next_target_btn:
                        target_page = next_target_btn.text.strip()
                        print(f"[이동] {target_page} 페이지로 이동... (현재: {current_page_num}페이지)")
                        
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_target_btn)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", next_target_btn)
                        
                        try:
                            old_review = driver.find_element(By.XPATH, "(//article[.//div[contains(@class, 'sdp-review__article__list__help')]])[1]")
                            wait.until(EC.staleness_of(old_review))
                        except:
                            time.sleep(2.5)
                    else:
                        # 현재 그룹의 모든 페이지를 방문했으면 내부 루프 종료
                        print(f"[그룹 완료] 현재 보이는 모든 페이지({min(visited_pages, default=0)}~{max(visited_pages, default=0)}) 수집 끝.")
                        break 

                except Exception as e:
                    # print(f"[일시적 오류] 재시도 중... ({str(e)[:50]})")
                    time.sleep(1)
                    continue

            # 4. 다음 그룹(>) 이동 버튼 클릭
            try:
                current_pagination = driver.find_element(By.XPATH, "//div[@data-start]")
                current_start_val = current_pagination.get_attribute("data-start")

                # '>' 버튼 찾기 (마지막 자식 버튼)
                next_group_btn = driver.find_element(By.XPATH, "//div[@data-start and @data-end]/button[last()]")
                
                if next_group_btn.is_enabled() and next_group_btn.get_attribute("disabled") is None:
                    print(f"[그룹 이동] '>' 버튼 클릭!")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_group_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_group_btn)
                    
                    print("[대기] 새 그룹 로딩 중...")
                    # data-start 값이 바뀔 때까지 대기 (그룹 이동 확인)
                    wait.until(lambda d: d.find_element(By.XPATH, "//div[@data-start]").get_attribute("data-start") != current_start_val)
                    time.sleep(2)
                    print("[성공] 새 페이지 그룹 로드 완료!")
                else:
                    print("[전체 완료] 더 이상 이동할 다음 그룹이 없습니다.")
                    break

            except (NoSuchElementException, TimeoutException):
                print("[전체 완료] '>' 버튼을 찾을 수 없습니다. 스크래핑을 종료합니다.")
                break

    except Exception as e:
        print(f"\n[오류 발생] {e}")
        traceback.print_exc()
    finally:
        if driver:
            print(f"\n[종료] 총 {len(all_reviews)}개의 리뷰가 수집되었습니다.")
            try: driver.quit()
            except: pass
    
    return all_reviews

if __name__ == "__main__":
    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    
    reviews = scrape_coupang(target_url)
    if reviews:
        df = pd.DataFrame(reviews)
        file_name = "coupang_reviews_final_v7.xlsx"
        df.to_excel(file_name, index=False)
        print(f"[저장 완료] '{file_name}' 파일에 저장되었습니다.")