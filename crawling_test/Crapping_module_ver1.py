import time
import pandas as pd
import traceback
import random
import os
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# [필수] 병렬 처리 및 락(Lock) 관리를 위한 라이브러리
from multiprocessing import Pool, freeze_support, Manager

# --- 설정 ---
TARGET_RATINGS = ['최고', '좋음', '보통', '별로', '나쁨']
MAX_REVIEWS_PER_RATING = 100

def setup_driver(lock=None):
    """
    undetected_chromedriver 초기화
    [중요] Lock을 사용하여 여러 프로세스가 동시에 드라이버 파일을 건드리는 것을 방지
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless") # 필요 시 주석 해제
    
    driver = None
    
    # 락(Lock)을 획득한 프로세스만 드라이버 초기화 진입
    if lock:
        lock.acquire()
    
    try:
        # print(f"   [시스템] 드라이버 초기화 중... (PID: {os.getpid()})")
        # 버전 141로 강제 지정 (사용자 크롬 버전에 맞춤)
        driver = uc.Chrome(options=options, version_main=141)
    except Exception as e:
        print(f"   [드라이버 오류] 141버전 실패, 재시도... 오류: {e}")
        try:
            # 실패 시 안전 장치 (버전 미지정)
            driver = uc.Chrome(options=options)
        except Exception as e2:
            print(f"   [치명적 오류] 드라이버 로드 완전 실패: {e2}")
    finally:
        # 드라이버 로드가 끝나면(성공하든 실패하든) 락 해제 -> 다음 프로세스 진입 허용
        if lock:
            # 파일 충돌 방지를 위해 락 해제 전 약간의 텀을 둠
            time.sleep(2) 
            lock.release()
            
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
            if not date: 
                date = article.find_element(By.XPATH, ".//div[i[contains(@class, 'twc-bg-full-star')]]/following-sibling::div").text.strip()
            
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
        time.sleep(1)
        filter_btn.click()
        time.sleep(1)

        popup = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        option = popup.find_element(By.XPATH, f".//div[contains(text(), '{rating_name}')]")
        option.click()
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        time.sleep(3) 
        return True
    except Exception as e:
        print(f"[{rating_name}] 필터 적용 실패: {str(e)[:50]}")
        return False

def scrape_single_rating(target_url, rating_name, lock):
    """하나의 별점에 대해 브라우저를 새로 열고 수집"""
    
    # setup_driver 호출 시 lock 전달
    driver = setup_driver(lock)
    if not driver:
        return []

    collected = []
    print(f"START: [{rating_name}] 브라우저 로드 완료, 수집 시작")
    
    try:
        wait = WebDriverWait(driver, 30)
        driver.get(target_url)
        time.sleep(3) 

        review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
        ActionChains(driver).move_to_element(review_tab).click().perform()
        
        review_section = wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        time.sleep(2) 

        if not apply_rating_filter(driver, wait, rating_name):
            print(f"FAIL: [{rating_name}] 필터 적용 불가")
            return []

        visited_pages = set()
        while len(collected) < MAX_REVIEWS_PER_RATING:
            try:
                pagination_xpath = "//div[@data-page and @data-start and @data-end]"
                is_new_ui = False 
                try:
                    pagination = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, pagination_xpath))
                    )
                    if "twc-mt-[24px]" in pagination.get_attribute("class"):
                        is_new_ui = True
                except TimeoutException:
                    pagination = None 

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

                if current_page not in visited_pages:
                    new_reviews = extract_reviews(driver, rating_name)
                    if new_reviews:
                        collected.extend(new_reviews)
                        visited_pages.add(current_page)
                        print(f"ING: [{rating_name}] {current_page}페이지 {len(new_reviews)}개 수집 (누적: {len(collected)})")
                    else:
                         if pagination is None and current_page == 1:
                             break 
                         time.sleep(2)

                if len(collected) >= MAX_REVIEWS_PER_RATING: break

                if pagination:
                    next_btn = None
                    min_val = float('inf')

                    if is_new_ui:
                        page_buttons = pagination.find_elements(By.XPATH, ".//button[span]")
                        for btn in page_buttons:
                            try:
                                val = int(btn.text.strip())
                                if val not in visited_pages and val > current_page and val < min_val:
                                    min_val = val
                                    next_btn = btn
                            except: continue 
                    else:
                        for btn in pagination.find_elements(By.CSS_SELECTOR, "button.sdp-review__article__page__num"):
                            val = int(btn.text.strip())
                            if val not in visited_pages and val > current_page and val < min_val:
                                min_val = val
                                next_btn = btn
                    
                    if next_btn:
                        next_btn.click()
                        time.sleep(random.uniform(2.5, 4.0)) 
                    else:
                        try:
                            next_group = pagination.find_element(By.XPATH, ".//button[.//svg[not(contains(@class, 'twc-rotate'))]]")
                            if next_group.is_enabled() and next_group.get_attribute("disabled") is None:
                                current_start_val = None
                                if not is_new_ui:
                                    current_start_val = pagination.get_attribute("data-start")
                                next_group.click()
                                if not is_new_ui:
                                    wait.until(lambda d: d.find_element(By.XPATH, pagination_xpath).get_attribute("data-start") != current_start_val)
                                else:
                                    wait.until(EC.staleness_of(next_group)) 
                                time.sleep(random.uniform(2.5, 4.0))
                            else:
                                break
                        except NoSuchElementException:
                            break
                else:
                    break
            except Exception as page_e: 
                break
    except Exception as e:
        print(f"ERROR: [{rating_name}] 수집 중 오류: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print(f"END: [{rating_name}] 종료 (최종: {len(collected)}개)")
            try: driver.quit()
            except: pass
    
    return collected[:MAX_REVIEWS_PER_RATING]

def scrape_wrapper(args):
    # args = (url, rating, lock)
    return scrape_single_rating(*args)

if __name__ == "__main__":
    freeze_support()

    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    
    print("=== 병렬 리뷰 스크래핑 시작 (프로세스 5개 가동) ===")
    
    # [중요] Manager를 사용하여 프로세스 간 공유되는 Lock 생성
    m = Manager()
    lock = m.Lock()

    # 파라미터에 lock 추가
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
        file_name = "coupang_reviews_parallel_fixed.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\n🎉 [전체 완료] 총 {len(all_results)}개의 리뷰가 '{file_name}'에 저장되었습니다!")
    else:
        print("\n[알림] 수집된 리뷰가 없습니다.")