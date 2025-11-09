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
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    # [수정] 버전 불일치 오류 해결을 위해 version_main=141을 명시적으로 지정합니다.
    driver = uc.Chrome(options=options, version_main=141)
    return driver

def extract_reviews(driver):
    """현재 페이지의 리뷰 데이터를 추출합니다."""
    reviews_data = []
    # '도움이 돼요' 섹션이 있는 article만 정확히 타겟팅
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
        except Exception: continue # 개별 리뷰 파싱 실패 무시
            
    return reviews_data

def scrape_coupang(url):
    driver = None
    all_reviews = []
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        driver.get(url)
        print("[시작] 상품 페이지 이동 완료")

        # 1. 상품평 탭 클릭
        review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
        ActionChains(driver).move_to_element(review_tab).click().perform()
        wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        print("[이동] 상품평 탭 진입 성공")
        time.sleep(1.5) # 탭 로딩 안정화 대기

        while True: # [메인 루프] 10페이지 단위 그룹 반복 (1~10, 11~20...)
            
            # 2. 현재 그룹의 첫 페이지(예: 1, 11, 21...) 스크래핑
            current_reviews = extract_reviews(driver)
            all_reviews.extend(current_reviews)
            print(f"[수집] 현재 페이지 완료 ({len(current_reviews)}개)")

            # 3. 현재 그룹 내 나머지 페이지(예: 2~10) 순차 클릭 루프
            while True:
                try:
                    # [수정] 페이지네이션 영역을 더 정확하게 찾기 위해 data-start 속성이 있는 div를 타겟팅
                    pagination = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-start and @data-end]")))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination)
                    time.sleep(0.5) # 스크롤 후 안정화 대기

                    # [중요] 현재 선택된 페이지 번호 찾기 (파란색 볼드체 스타일 기준)
                    # twc-font-bold 와 twc-text-[#346aff] 클래스가 있는 버튼이 현재 페이지
                    current_btn = pagination.find_element(By.XPATH, ".//button[contains(@class, 'twc-font-bold') and contains(@class, 'twc-text-[#346aff]')]")
                    current_page_num = int(current_btn.text.strip())

                    # [중요] 클릭 가능한 모든 숫자 버튼 찾기 (span 내부에 숫자가 있는 버튼)
                    # XPath: 현재 페이지네이션 div 안의, span을 자식으로 가진 모든 button
                    num_btns = pagination.find_elements(By.XPATH, ".//button[./span[string-length(text()) > 0]]")
                    
                    next_target_btn = None
                    for btn in num_btns:
                        btn_num = int(btn.text.strip())
                        if btn_num > current_page_num:
                            next_target_btn = btn
                            break # 현재 페이지보다 큰 첫 번째 숫자를 찾으면 중단

                    if next_target_btn:
                        target_num = next_target_btn.text.strip()
                        print(f"[페이지 이동] {target_num} 페이지 클릭 시도")
                        
                        # 페이지 전환 감지를 위한 기준 요소 (상품평 섹션 전체)
                        old_section = driver.find_element(By.ID, "sdpReview")
                        
                        # 안전한 JS 클릭 (이미 스크롤했지만 확실히 하기 위해 재실행)
                        driver.execute_script("arguments[0].click();", next_target_btn)
                        
                        # 페이지 로딩 완료 대기
                        wait.until(EC.staleness_of(old_section))
                        time.sleep(1 + random.random()) # 봇 탐지 회피용 랜덤 대기

                        # 이동한 페이지 스크래핑
                        new_reviews = extract_reviews(driver)
                        all_reviews.extend(new_reviews)
                        print(f"[수집] {target_num} 페이지 완료 ({len(new_reviews)}개)")
                    else:
                        print("[그룹 완료] 현재 보이는 숫자 페이지 모두 수집 끝.")
                        break # 내부 while 루프 종료 -> '>' 버튼 클릭 단계로 이동

                except (StaleElementReferenceException, NoSuchElementException, TimeoutException):
                    # DOM 변경 등으로 요소를 놓치면 루프 재시도하여 다시 찾기
                    print("[재시도] 페이지 버튼을 다시 찾습니다...")
                    time.sleep(1)
                    continue

            # 4. 다음 그룹(>) 이동 버튼 클릭
            try:
                # [중요] '>' 버튼 찾기: svg는 있고, span(숫자)은 없는 버튼
                # 여기도 클릭 전 확실하게 스크롤을 먼저 수행
                # [수정] 페이지네이션 영역 내에서 다음 버튼을 찾도록 XPath 수정
                next_group_btn = driver.find_element(By.XPATH, "//div[@data-start and @data-end]//button[.//svg and not(.//span)]")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_group_btn)
                time.sleep(0.5)

                if next_group_btn.is_enabled():
                    print("[그룹 이동] 다음 10개 페이지(>) 로 이동합니다.")
                    old_section = driver.find_element(By.ID, "sdpReview")
                    
                    driver.execute_script("arguments[0].click();", next_group_btn)
                    
                    wait.until(EC.staleness_of(old_section))
                    time.sleep(2) # 그룹 이동은 데이터 로딩이 더 걸릴 수 있음
                else:
                    print("[전체 완료] 더 이상 이동할 페이지가 없습니다 (버튼 비활성).")
                    break
            except NoSuchElementException:
                print("[전체 완료] 다음 그룹(>) 버튼이 없습니다. 스크래핑 종료.")
                break

    except Exception as e:
        print(f"[치명적 오류] {e}")
        traceback.print_exc()
    finally:
        if driver: driver.quit()
    
    return all_reviews

if __name__ == "__main__":
    # [수정] 실제 테스트할 쿠팡 상품 페이지 URL을 입력하세요.
    test_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED" 
    
    reviews = scrape_coupang(test_url)
    if reviews:
        df = pd.DataFrame(reviews)
        df.to_excel("coupang_reviews_final.xlsx", index=False)
        print(f"[저장 완료] 총 {len(reviews)}개의 리뷰가 저장되었습니다.")