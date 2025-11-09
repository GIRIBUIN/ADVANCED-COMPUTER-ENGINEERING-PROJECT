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

# --- 설정 ---
TARGET_RATINGS = ['최고', '좋음', '보통', '별로', '나쁨']
MAX_REVIEWS_PER_RATING = 100

def setup_driver():
    """undetected_chromedriver 초기화"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    try:
        driver = uc.Chrome(options=options, version_main=141)
    except Exception as e:
        print(f"[드라이버 로드 오류] {e}")
        print("version_main=141을 제거하고 자동 감지 모드로 다시 시도합니다.")
        driver = uc.Chrome(options=options)
    return driver

def extract_reviews(driver, current_rating_filter):
    """리뷰 데이터 추출 (필터 전/후 겸용)"""
    reviews_data = []
    
    review_article_xpath = "//article[contains(@class, 'sdp-review__article__list') or contains(@class, 'twc-pt-[16px]')]"

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, review_article_xpath))
        )
    except TimeoutException:
        print("     -> 10초 대기했으나 리뷰 요소를 찾지 못했습니다. (리뷰 없음 또는 로딩 실패)")
        return []

    articles = driver.find_elements(By.XPATH, review_article_xpath)
    
    for article in articles:
        try:
            def get_text(selector):
                try: return article.find_element(By.CSS_SELECTOR, selector).text.strip()
                except: return ""

            author = article.find_element(By.CSS_SELECTOR, "span[data-member-id]").text.strip()
            rating = len(article.find_elements(By.CSS_SELECTOR, "i.twc-bg-full-star"))
            date = get_text("div.sdp-review__article__list__info__product-info__reg-date")
            if not date: date = article.find_element(By.XPATH, ".//div[i[contains(@class, 'twc-bg-full-star')]]/following-sibling::div").text.strip()
            
            product_option = get_text("div.sdp-review__article__list__info__product-info__name")
            if not product_option: product_option = get_text("div.twc-my-\\[16px\\]")
            
            review_title = get_text("div.sdp-review__article__list__headline")
            if not review_title: review_title = get_text("div.twc-mb-\\[8px\\].twc-font-bold")

            review_body = get_text("div.sdp-review__article__list__review__content")
            if not review_body: review_body = get_text("div.twc-break-all")
            
            helpful = 0
            try: helpful = int(article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__help").get_attribute("data-count"))
            except: pass
            
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
        print(f"   -> ['{rating_name}'] 필터 적용 시도...")
        filter_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='combobox']")))
        
        if rating_name in filter_btn.text and "모든 별점" not in filter_btn.text:
            print(f"      ['{rating_name}'] 이미 선택됨.")
            return True

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_btn)
        time.sleep(1)
        filter_btn.click()
        time.sleep(1)

        popup = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        option = popup.find_element(By.XPATH, f".//div[contains(text(), '{rating_name}')]")
        option.click()
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        print(f"      ['{rating_name}'] 필터 적용 완료. 로딩 대기...")
        time.sleep(3) 
        return True
    except Exception as e:
        print(f"      [오류] 필터 적용 실패: {str(e)[:50]}")
        return False

def scrape_single_rating(target_url, rating_name):
    """하나의 별점에 대해 브라우저를 새로 열고 수집"""
    driver = None
    collected = []
    try:
        print(f"\n=== [{rating_name}] 수집 시작 ===")
        driver = setup_driver()
        wait = WebDriverWait(driver, 30)
        driver.get(target_url)
        time.sleep(5)

        review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
        ActionChains(driver).move_to_element(review_tab).click().perform()
        review_section = wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        time.sleep(2)

        if not apply_rating_filter(driver, wait, rating_name):
            print(f"   [실패] '{rating_name}' 필터 적용 불가.")
            return []

        # --- [ 페이지네이션 로직 v29 (수정됨) ] ---
        visited_pages = set()
        while len(collected) < MAX_REVIEWS_PER_RATING:
            try:
                # 1. 페이지네이션 바(Bar) 감지
                pagination_xpath = "//div[@data-start and @data-end] | //div[contains(@class, 'twc-mt-[24px]')]"
                is_new_ui = False
                try:
                    pagination = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, pagination_xpath))
                    )
                    if "twc-mt-[24px]" in pagination.get_attribute("class"):
                        is_new_ui = True
                except TimeoutException:
                    pagination = None 

                # 2. 현재 페이지 번호 확인
                if pagination:
                    try:
                        if is_new_ui:
                            current_page = int(pagination.find_element(By.CSS_SELECTOR, "button[class*='twc-text-[#346aff]']").text.strip())
                        else:
                            current_page = int(pagination.find_element(By.CSS_SELECTOR, "button.selected").text.strip())
                    except Exception:
                        current_page = 1 
                else:
                    current_page = 1

                # 3. 리뷰 수집
                if current_page not in visited_pages:
                    new_reviews = extract_reviews(driver, rating_name)
                    if new_reviews:
                        collected.extend(new_reviews)
                        visited_pages.add(current_page)
                        print(f"   -> {current_page}페이지: {len(new_reviews)}개 수집 (누적: {len(collected)}/{MAX_REVIEWS_PER_RATING})")
                    else:
                         print(f"   -> {current_page}페이지: 리뷰 없음 (로딩 지연 또는 마지막 페이지)")
                         if pagination is None and current_page == 1:
                             break 
                         time.sleep(2)

                if len(collected) >= MAX_REVIEWS_PER_RATING: break

                # 4. 다음 페이지 이동
                if pagination:
                    next_btn = None
                    min_val = float('inf')

                    if is_new_ui:
                        # [수정됨 v29] 숫자 버튼들: <span> 태그를 가진 버튼
                        # (이전: .//button[span[number(text())]])
                        page_buttons = pagination.find_elements(By.XPATH, ".//button[span]")
                        for btn in page_buttons:
                            try:
                                val = int(btn.text.strip())
                                if val not in visited_pages and val > current_page and val < min_val:
                                    min_val = val
                                    next_btn = btn
                            except: continue 
                    else:
                        # [필터 전] 로직 (유지)
                        for btn in pagination.find_elements(By.CSS_SELECTOR, "button.sdp-review__article__page__num"):
                            val = int(btn.text.strip())
                            if val not in visited_pages and val > current_page and val < min_val:
                                min_val = val
                                next_btn = btn
                    
                    if next_btn:
                        # 2, 3, 4 등 다음 페이지 번호 클릭
                        next_btn.click()
                        time.sleep(3)
                    else:
                        # '>' (다음 그룹) 버튼 시도
                        try:
                            # [수정됨 v29] '>' 버튼을 더 정확하게 찾음
                            # '<' 버튼(twc-rotate)을 제외한 svg 버튼
                            # (이전: .//button[last()][.//svg])
                            next_group = pagination.find_element(By.XPATH, ".//button[.//svg[not(contains(@class, 'twc-rotate'))]]")
                            
                            if next_group.is_enabled() and next_group.get_attribute("disabled") is None:
                                # [수정됨 v29] 'data-start' 속성 대기 로직은 
                                # 'is_new_ui'가 아닐 때만(필터 전) 실행
                                current_start_val = None
                                if not is_new_ui:
                                    current_start_val = pagination.get_attribute("data-start")

                                next_group.click()
                                
                                if not is_new_ui:
                                    # [필터 전] data-start 값이 바뀔 때까지 대기
                                    wait.until(lambda d: d.find_element(By.XPATH, pagination_xpath).get_attribute("data-start") != current_start_val)
                                else:
                                    # [필터 후]는 data-start가 없으므로, 페이지 번호가 바뀔 때까지 대기 (예: 11페이지)
                                    wait.until(EC.staleness_of(next_group)) # '>' 버튼이 사라질 때(재로딩)까지 대기
                                
                                time.sleep(3)
                            else:
                                print("   [완료] 더 이상 페이지가 없습니다. ('>' 버튼 비활성화)")
                                break
                        except NoSuchElementException:
                            print("   [완료] 다음 그룹(>) 버튼 없음.")
                            break
                else:
                    print("   [완료] 단일 페이지입니다. (페이지네이션 바 없음)")
                    break

            except Exception as page_e: 
                print(f"   [오류] 페이지 순회 중 에러: {page_e}")
                traceback.print_exc() 
                break

    except Exception as e:
        print(f"   [오류] {rating_name} 수집 중 에러: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print(f"=== [{rating_name}] 종료 (최종 수집: {len(collected)}개) ===\n")
            try: driver.quit()
            except: pass
    
    return collected[:MAX_REVIEWS_PER_RATING]

if __name__ == "__main__":
    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    
    all_results = []
    for rating in TARGET_RATINGS:
        rating_reviews = scrape_single_rating(target_url, rating)
        all_results.extend(rating_reviews)
        time.sleep(5)

    if all_results:
        df = pd.DataFrame(all_results)
        file_name = "coupang_reviews_final_v29_pagination_fix_2.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\n🎉 [전체 완료] 총 {len(all_results)}개의 리뷰가 '{file_name}'에 저장되었습니다!")
    else:
        print("\n[알림] 수집된 리뷰가 없습니다.")