import time
import pandas as pd
import traceback
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def scrape_coupang_reviews(url):
    driver = None
    try:
        # --- 1. 드라이버 설정 ---
        print("[로그] 드라이버 설정을 시작합니다.")
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        driver = uc.Chrome(options=options)
        print("[로그] Chrome 드라이버가 성공적으로 시작되었습니다.")
        
        driver.get(url)
        print(f"[로그] URL로 이동했습니다: {url}")

        reviews_data = []
        current_page = 1

        # --- 2. '상품평' 탭으로 이동 ---
        print("[로그] '상품평' 탭 버튼을 찾는 중...")
        review_tab_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]"))
        )
        
        print("[로그] '상품평' 탭 위치로 스크롤합니다.")
        driver.execute_script("arguments[0].scrollIntoView(true);", review_tab_button)
        time.sleep(1)

        print("[로그] '상품평' 탭 클릭 명령을 실행합니다.")
        driver.execute_script("arguments[0].click();", review_tab_button)
        
        print("[로그] 리뷰 섹션 전체가 로드되기를 기다립니다...")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.sdp-review__article__page"))
        )
        print("[성공] 리뷰 섹션이 완전히 로드되었습니다.")

        # --- 3. 페이지네이션 루프 ---
        while True:
            print(f"--- 현재 페이지({current_page}) 스크래핑 시작 ---")
            
            time.sleep(1) # 페이지 변경 후 DOM이 안정화될 시간을 줌
            review_articles = driver.find_elements(By.CSS_SELECTOR, "article.sdp-review__article__list")
            print(f"[로그] {len(review_articles)}개의 리뷰를 찾았습니다.")
            
            if not review_articles:
                print("[알림] 현재 페이지에서 리뷰를 찾지 못해 종료합니다.")
                break

            # --- 4. 데이터 추출 ---
            for i, article in enumerate(review_articles, 1):
                try:
                    # (데이터 추출 로직은 동일)
                    author = article.find_element(By.CSS_SELECTOR, "span.sdp-review__article__list__info__user__name").text.strip()
                    rating_element = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__star-orange")
                    rating = int(rating_element.get_attribute("data-rating"))
                    date = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__reg-date").text.strip()
                    product_option = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__info__product-info__name").text.strip()
                    
                    try:
                        review_title = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__headline").text.strip()
                    except NoSuchElementException:
                        review_title = ""
                        
                    try:
                        review_body = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__review__content").text.strip()
                    except NoSuchElementException:
                        review_body = ""
                    
                    try:
                        helpful_container = article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__help")
                        helpful_count = int(helpful_container.get_attribute("data-count"))
                    except (NoSuchElementException, ValueError, AttributeError):
                        helpful_count = 0

                    reviews_data.append({
                        "author": author, "rating": rating, "date": date, "product_option": product_option,
                        "review_title": review_title, "review_body": review_body, "helpful_count": helpful_count
                    })
                except Exception as e:
                    print(f"[오류] 리뷰 하나를 파싱하는 중 문제가 발생했습니다: {e}")
            
            # --- 5. 다음 페이지로 이동 ---
            try:
                pagination_container = driver.find_element(By.CSS_SELECTOR, "div.sdp-review__article__page")
                next_page_button = pagination_container.find_element(By.CSS_SELECTOR, "button.sdp-review__article__page__next")
                
                if next_page_button.is_enabled():
                    print("[로그] 다음 페이지로 이동합니다.")
                    driver.execute_script("arguments[0].click();", next_page_button)
                    current_page += 1
                    
                    # !<-- 해결: time.sleep(2) 대신, 다음 페이지의 리뷰 섹션이 로드될 때까지 명시적으로 대기
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.sdp-review__article__page"))
                    )
                else:
                    print("[로그] 다음 페이지 버튼이 비활성화되어 스크래핑을 종료합니다.")
                    break
            except NoSuchElementException:
                print("[로그] 다음 페이지 버튼을 찾을 수 없어 스크래핑을 종료합니다. (마지막 페이지)")
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
    target_url = "https://www.coupang.com/vp/products/8201777608?itemId=19748050323&searchId=d73c5817f03d4077a1e40c098f4a3c15&sourceType=brandstore_display_ads&storeId=189766&subSourceType=brandstore_display_ads&vendorId=A01064449&vendorItemId=86851606092"
    
    print(f"'{target_url}' 주소의 리뷰 스크래핑을 시작합니다...")
    scraped_reviews = scrape_coupang_reviews(target_url)

    if scraped_reviews:
        df = pd.DataFrame(scraped_reviews)
        file_name = "coupang_reviews_final.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')
        print(f"\n[성공] 총 {len(scraped_reviews)}개의 리뷰를 '{file_name}' 파일로 저장했습니다.")
    else:
        print("\n[알림] 스크래핑된 리뷰가 없습니다.")
    
    print("[로그] 스크립트 실행이 완료되었습니다.")