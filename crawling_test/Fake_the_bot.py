import time
import pandas as pd
import traceback
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent # User-Agent 위장을 위해 추가

def setup_driver():
    """
    데스크톱 전용 랜덤 User-Agent가 적용된 undetected_chromedriver 인스턴스를 설정합니다.
    """
    print("[로그] 드라이버 설정을 시작합니다.")
    options = uc.ChromeOptions()
    
    # --- 해결: User-Agent를 '데스크톱'으로 한정하여 환경 불일치 문제 해결 ---
    ua = UserAgent(platforms='desktop')
    user_agent = ua.random
    print(f"[로그] 적용된 User-Agent: {user_agent}")
    options.add_argument(f'--user-agent={user_agent}')
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    driver = uc.Chrome(options=options,version_main=141)
    print("[로그] Chrome 드라이버가 성공적으로 시작되었습니다.")
    return driver

def human_like_delay(min_seconds=1.5, max_seconds=3.0):
    """
    지정된 범위 내에서 무작위 지연 시간을 생성하여 예측 불가능한 패턴을 만듭니다.
    """
    time.sleep(random.uniform(min_seconds, max_seconds))

def scrape_coupang_reviews(url):
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        print(f"[로그] URL로 이동했습니다: {url}")

        reviews_data = []
        current_page = 1
        wait = WebDriverWait(driver, 20)
        actions = ActionChains(driver)

        # --- 세션 워밍업 ---
        print("[로그] 세션 워밍업: 실제 사용자처럼 페이지를 탐색합니다.")
        driver.execute_script("window.scrollBy(0, 500);")
        human_like_delay(1, 2)
        driver.execute_script("window.scrollBy(0, -200);")
        human_like_delay(1, 2.5)

        # --- '상품평' 탭으로 인간적인 이동 및 클릭 ---
        print("[로그] '상품평' 탭 버튼을 찾는 중...")
        review_tab_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]"))
        )
        
        print("[로그] '상품평' 탭으로 스크롤 및 마우스 이동...")
        actions.move_to_element(review_tab_button).perform()
        human_like_delay(0.5, 1.5)

        print("[로그] '상품평' 탭 클릭 명령을 실행합니다.")
        review_tab_button.click()
        
        print("[로그] 리뷰 섹션이 로드되기를 기다립니다...")
        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.sdp-review__article__page"))
        )
        print("[성공] 리뷰 섹션이 완전히 로드되었습니다.")

        # --- 페이지네이션 루프 ---
        while True:
            print(f"--- 현재 페이지({current_page}) 스크래핑 시작 ---")
            
            human_like_delay(1.0, 2.5)
            
            review_articles = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.sdp-review__article__list"))
            )
            print(f"[로그] {len(review_articles)}개의 리뷰를 찾았습니다.")

            first_review_on_page = review_articles

            for article in review_articles:
                try:
                    author = article.find_element(By.CSS_SELECTOR, "span.sdp-review__article__list__info__user__name").text.strip()
                    rating_element = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__star-orange")
                    rating = int(rating_element.get_attribute("data-rating"))
                    date = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__reg-date").text.strip()
                    product_option = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__name").text.strip()
                    
                    review_body = ""
                    try:
                        review_body = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__review__content").text.strip()
                    except NoSuchElementException: pass
                    
                    reviews_data.append({
                        "author": author, "rating": rating, "date": date, 
                        "product_option": product_option, "review_body": review_body
                    })
                except Exception as e:
                    print(f"[오류] 리뷰 하나를 파싱하는 중 문제가 발생했습니다: {e}")
            
            try:
                next_page_button = driver.find_element(By.CSS_SELECTOR, "button.sdp-review__article__page__next")
                
                if next_page_button.is_enabled():
                    print("[로그] 다음 페이지로 이동합니다.")
                    actions.move_to_element(next_page_button).perform()
                    human_like_delay(0.6, 1.2)
                    
                    driver.execute_script("arguments.click();", next_page_button)
                    
                    print("[로그] 페이지가 갱신되기를 기다립니다...")
                    wait.until(EC.staleness_of(first_review_on_page))
                    
                    current_page += 1
                else:
                    print("[로그] 다음 페이지 버튼이 비활성화되어 스크래핑을 종료합니다.")
                    break
            except NoSuchElementException:
                print("[로그] 다음 페이지 버튼을 찾을 수 없어 스크래핑을 종료합니다. (마지막 페이지)")
                break
            except TimeoutException:
                print("[알림] 페이지 갱신을 기다리는 중 시간 초과. 마지막 페이지일 수 있으므로 종료합니다.")
                break

    except Exception as e:
        print(f"\n[오류] 스크래핑 중 예상치 못한 오류가 발생했습니다: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print("[로그] 드라이버를 종료합니다.")
            driver.quit()

    return reviews_data

if __name__ == "__main__":
    target_url = "https://www.coupang.com/vp/products/8070703179?itemId=22947201334&searchId=edfbc22f87a248dea8450fa5967312bc&sourceType=brandstore_display_ads-carousel&storeId=192848&subSourceType=brandstore_display_ads-carousel&vendorId=A00012012&vendorItemId=90113908086"
     # 실제 스크래핑할 Coupang 상품 페이지 URL로 변경하세요.    
    scraped_reviews = scrape_coupang_reviews(target_url)

    if scraped_reviews:
        df = pd.DataFrame(scraped_reviews)
        file_name = "coupang_reviews_final.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')
        print(f"\n[성공] 총 {len(scraped_reviews)}개의 리뷰를 '{file_name}' 파일로 저장했습니다.")
    else:
        print("\n[알림] 스크래핑된 리뷰가 없습니다.")