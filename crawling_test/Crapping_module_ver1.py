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
    # [중요] 사용자 환경에 맞춰 크롬 버전 고정 (에러 발생 시 수정 필요)
    driver = uc.Chrome(options=options, version_main=141)
    return driver

def extract_reviews(driver):
    """현재 페이지에 로드된 리뷰들을 추출"""
    reviews_data = []
    # '도움이 돼요' 섹션이 있는 리뷰 article만 정확히 타겟팅
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
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        driver.get(url)
        print("[시작] 상품 페이지 로딩 중...")

        # 1. '상품평' 탭 클릭
        review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
        ActionChains(driver).move_to_element(review_tab).click().perform()
        
        # 리뷰 섹션이 확실히 로드될 때까지 대기
        wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        print("[이동] 상품평 탭 진입 성공")
        time.sleep(2) # 초기 로딩 안정화

        while True: # [메인 루프] 10페이지 단위 그룹 반복
            
            # 2. 현재 페이지 수집
            current_reviews = extract_reviews(driver)
            all_reviews.extend(current_reviews)
            print(f"[수집] 페이지 완료 (누적 {len(all_reviews)}개)")

            # 3. 그룹 내 나머지 숫자 페이지 순차 클릭
            while True:
                try:
                    # 페이지네이션 바 찾기 (data-start 속성이 있는 div)
                    pagination = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-start and @data-end]")))
                    
                    # 현재 활성화된 페이지 번호 찾기 (파란색 글씨)
                    current_btn = pagination.find_element(By.XPATH, ".//button[contains(@class, 'twc-text-[#346aff]') and contains(@class, 'twc-font-bold')]")
                    current_page_num = int(current_btn.text.strip())

                    # 현재 번호보다 큰 숫자 버튼들 찾기
                    next_num_btn = None
                    # span 안에 텍스트(숫자)가 있는 버튼만 필터링
                    num_btns = pagination.find_elements(By.XPATH, ".//button[./span[string-length(text()) > 0]]")
                    for btn in num_btns:
                        if int(btn.text.strip()) > current_page_num:
                            next_num_btn = btn
                            break 

                    if next_num_btn:
                        target_page = next_num_btn.text.strip()
                        print(f"[이동] {target_page} 페이지로 이동...")
                        
                        # 스크롤 및 클릭
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_num_btn)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", next_num_btn)
                        
                        # 로딩 대기 (중요: DOM 변경 감지)
                        try:
                            # 이전 페이지의 첫 번째 리뷰가 사라질 때까지 대기 (Staleness)
                            old_review = driver.find_element(By.XPATH, "(//article[.//div[contains(@class, 'sdp-review__article__list__help')]])[1]")
                            wait.until(EC.staleness_of(old_review))
                        except:
                            time.sleep(2) # 요소를 못 찾으면 안전하게 시간 대기

                        # 이동 후 리뷰 수집
                        new_reviews = extract_reviews(driver)
                        all_reviews.extend(new_reviews)
                        print(f"       -> {len(new_reviews)}개 추가 수집")
                    else:
                        print("[그룹 완료] 현재 그룹 페이지 수집 끝. 다음 그룹 버튼을 찾습니다.")
                        break 

                except Exception as e:
                    print(f"[일시적 오류] 페이지 이동 재시도... ({str(e)[:30]})")
                    time.sleep(1)
                    continue

            # 4. 다음 그룹(>) 이동 버튼 클릭 (V5 핵심 수정)
            try:
                # [V5 수정] 가장 단순하고 강력한 방법: 페이지네이션 바의 '마지막 자식 버튼'을 선택
                next_group_btn = driver.find_element(By.XPATH, "//div[@data-start and @data-end]/button[last()]")
                
                # 버튼이 활성화 상태인지 확인 (disabled 속성이 없어야 함)
                if next_group_btn.is_enabled() and next_group_btn.get_attribute("disabled") is None:
                    print("[그룹 이동] '>' 버튼 클릭 시도...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_group_btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_group_btn)
                    
                    # 그룹 이동은 로딩이 오래 걸리므로 넉넉히 대기
                    time.sleep(4)
                    
                    # 새 그룹이 로드되었는지 검증 (예: 11페이지가 보이는지)
                    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-start and @data-end]")))
                    print("[그룹 이동] 성공! 다음 그룹 로드 완료.")
                else:
                    print("[전체 완료] '>' 버튼이 비활성화되었습니다. (더 이상 리뷰 없음)")
                    break

            except (NoSuchElementException, TimeoutException):
                print("[전체 완료] 다음 그룹(>) 버튼을 찾을 수 없습니다. 스크래핑을 종료합니다.")
                break

    except Exception as e:
        print(f"\n[치명적 오류] {e}")
        traceback.print_exc()
    finally:
        if driver:
            print(f"\n[종료] 브라우저를 닫습니다. 총 {len(all_reviews)}개 리뷰 수집됨.")
            try: driver.quit()
            except: pass # 종료 시 발생하는 핸들 에러 무시
    
    return all_reviews

if __name__ == "__main__":
    # 테스트할 URL
    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    
    reviews = scrape_coupang(target_url)
    if reviews:
        df = pd.DataFrame(reviews)
        file_name = "coupang_reviews_final_v5.xlsx"
        df.to_excel(file_name, index=False)
        print(f"[저장 완료] '{file_name}' 파일에 저장되었습니다.")