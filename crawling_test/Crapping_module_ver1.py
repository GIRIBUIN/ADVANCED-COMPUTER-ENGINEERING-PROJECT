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
    
    # 리뷰 article을 식별하는 XPath (필터 전/후 CSS 클래스가 다를 수 있어 통합)
    review_article_xpath = "//article[contains(@class, 'sdp-review__article__list') or contains(@class, 'twc-pt-[16px]')]"

    try:
        # 리뷰 목록이 로드될 때까지 최소 1개 이상 기다림
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, review_article_xpath))
        )
    except TimeoutException:
        print("     -> 10초 대기했으나 리뷰 요소를 찾지 못했습니다. (리뷰 없음 또는 로딩 실패)")
        return []

    articles = driver.find_elements(By.XPATH, review_article_xpath)
    
    for article in articles:
        try:
            # 공용 함수: CSS 셀렉터로 텍스트 가져오기
            def get_text(selector):
                try: return article.find_element(By.CSS_SELECTOR, selector).text.strip()
                except: return ""

            # 작성자 (필수)
            author = article.find_element(By.CSS_SELECTOR, "span[data-member-id]").text.strip()
            
            # 평점 (필수) - 별 아이콘 개수 계산
            rating = len(article.find_elements(By.CSS_SELECTOR, "i.twc-bg-full-star"))
            
            # 날짜 (필터 전/후 XPath가 다름)
            date = get_text("div.sdp-review__article__list__info__product-info__reg-date")
            if not date: 
                # 필터 후 UI (twc-...)
                date = article.find_element(By.XPATH, ".//div[i[contains(@class, 'twc-bg-full-star')]]/following-sibling::div").text.strip()
            
            # 구매옵션 (필터 전/후 XPath가 다름)
            product_option = get_text("div.sdp-review__article__list__info__product-info__name")
            if not product_option: 
                # 필터 후 UI (twc-...)
                product_option = get_text("div.twc-my-\\[16px\\]")
            
            # 리뷰 제목 (필터 전/후 XPath가 다름)
            review_title = get_text("div.sdp-review__article__list__headline")
            if not review_title: 
                # 필터 후 UI (twc-...)
                review_title = get_text("div.twc-mb-\\[8px\\].twc-font-bold")

            # 리뷰 내용 (필터 전/후 XPath가 다름)
            review_body = get_text("div.sdp-review__article__list__review__content")
            if not review_body: 
                # 필터 후 UI (twc-...)
                review_body = get_text("div.twc-break-all")
            
            # 도움됨 (필터 전/후 XPath가 다름)
            helpful = 0
            try: 
                # 필터 전
                helpful = int(article.find_element(By.CSS_SELECTOR, "div.sdp-review__article__list__help").get_attribute("data-count"))
            except: 
                try:
                    # 필터 후
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
            # 개별 리뷰 파싱 실패 시 다음 리뷰로 넘어감
            continue
    return reviews_data

def apply_rating_filter(driver, wait, rating_name):
    """별점 필터 적용"""
    try:
        print(f"   -> ['{rating_name}'] 필터 적용 시도...")
        
        # 필터 드롭다운 버튼 찾기 (콤보박스 역할)
        filter_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='combobox']")))
        
        # 이미 적용되었는지 텍스트로 확인 (예: '최고(123,456)')
        if rating_name in filter_btn.text and "모든 별점" not in filter_btn.text:
            print(f"       ['{rating_name}'] 이미 선택됨.")
            return True

        # 버튼을 화면 중앙으로 스크롤 후 클릭
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_btn)
        time.sleep(1) # 스크롤 안정화
        filter_btn.click()
        time.sleep(1) # 팝업 표시 대기

        # 별점 옵션 팝업 찾기
        popup = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        # 팝업 내에서 원하는 별점 텍스트(예: '최고')를 가진 div 클릭
        option = popup.find_element(By.XPATH, f".//div[contains(text(), '{rating_name}')]")
        option.click()
        
        # 팝업이 사라질 때까지 대기 (리뷰 목록 리로딩 시작)
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-radix-popper-content-wrapper]")))
        print(f"       ['{rating_name}'] 필터 적용 완료. 로딩 대기...")
        time.sleep(3) # 리뷰 목록이 AJAX로 새로고침될 때까지 충분히 대기
        return True
    except Exception as e:
        print(f"       [오류] 필터 적용 실패: {str(e)[:50]}")
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
        time.sleep(5) # 페이지 초기 로드 대기

        # '상품평' 탭으로 이동
        review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'상품평')]")))
        ActionChains(driver).move_to_element(review_tab).click().perform()
        
        # 리뷰 섹션(sdpReview)이 나타날 때까지 대기
        review_section = wait.until(EC.presence_of_element_located((By.ID, "sdpReview")))
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        time.sleep(2) # 스크롤 후 관련 요소 로드 대기

        # 별점 필터 적용
        if not apply_rating_filter(driver, wait, rating_name):
            print(f"   [실패] '{rating_name}' 필터 적용 불가.")
            return []

        # --- [ 페이지네이션 로직 ] ---
        visited_pages = set()
        while len(collected) < MAX_REVIEWS_PER_RATING:
            try:
                # 1. 페이지네이션 바(Bar) 감지
                
                # #############################################################
                # [수정됨] data-page, data-start, data-end 속성을 모두 가진 div로 명확하게 지정
                pagination_xpath = "//div[@data-page and @data-start and @data-end]"
                # #############################################################
                
                is_new_ui = False # 기본값은 필터 전 UI로 가정
                try:
                    # 페이지네이션 바가 로드될 때까지 10초 대기
                    pagination = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, pagination_xpath))
                    )
                    # 새 UI(필터 후)인지 확인
                    if "twc-mt-[24px]" in pagination.get_attribute("class"):
                        is_new_ui = True
                except TimeoutException:
                    pagination = None # 10초간 못찾으면 페이지네이션이 없는 것(1페이지)으로 간주

                # 2. 현재 페이지 번호 확인
                if pagination:
                    try:
                        if is_new_ui:
                            # [필터 후] 활성화된(파란색) 버튼의 텍스트를 현재 페이지로 인식
                            current_page = int(pagination.find_element(By.CSS_SELECTOR, "button[class*='twc-text-[#346aff]']").text.strip())
                        else:
                            # [필터 전] 'selected' 클래스를 가진 버튼 (기존 로직)
                            current_page = int(pagination.find_element(By.CSS_SELECTOR, "button.selected").text.strip())
                    except Exception:
                        current_page = 1 # 버튼을 못찾으면 1페이지로 간주
                else:
                    current_page = 1

                # 3. 리뷰 수집
                if current_page not in visited_pages:
                    new_reviews = extract_reviews(driver, rating_name)
                    if new_reviews:
                        collected.extend(new_reviews)
                        visited_pages.add(current_page)
                        print(f"   -> {current_page}페이지: {len(new_reviews)}개 수집 (누적: {len(collected)}/{MAX_REVIEWS_PER_RATING})")
                    else:
                         print(f"   -> {current_page}페이지: 리뷰 없음 (로딩 지연 또는 마지막 페이지)")
                         # 페이지네이션 바가 없는데(pagination is None) 리뷰도 없으면(1페이지) 종료
                         if pagination is None and current_page == 1:
                             break 
                         time.sleep(2)

                if len(collected) >= MAX_REVIEWS_PER_RATING: break

                # 4. 다음 페이지 이동
                if pagination:
                    next_btn = None
                    min_val = float('inf')

                    if is_new_ui:
                        # [필터 후] 로직
                        # 숫자 버튼들: <span> 태그를 가진 버튼
                        page_buttons = pagination.find_elements(By.XPATH, ".//button[span]")
                        for btn in page_buttons:
                            try:
                                val = int(btn.text.strip())
                                # 방문 안 했고, 현재 페이지보다 크고, 가장 작은 다음 페이지 찾기
                                if val not in visited_pages and val > current_page and val < min_val:
                                    min_val = val
                                    next_btn = btn
                            except: continue 
                    else:
                        # [필터 전] 로직
                        for btn in pagination.find_elements(By.CSS_SELECTOR, "button.sdp-review__article__page__num"):
                            val = int(btn.text.strip())
                            if val not in visited_pages and val > current_page and val < min_val:
                                min_val = val
                                next_btn = btn
                    
                    if next_btn:
                        # 2, 3, 4 등 다음 페이지 번호 클릭
                        next_btn.click()
                        time.sleep(random.uniform(2.5, 4.0)) # 페이지 로딩 대기
                    else:
                        # '>' (다음 그룹) 버튼 시도
                        try:
                            # '>' 버튼: svg가 있고, 그 svg가 'twc-rotate'(<) 클래스를 갖지 않음
                            next_group = pagination.find_element(By.XPATH, ".//button[.//svg[not(contains(@class, 'twc-rotate'))]]")
                            
                            if next_group.is_enabled() and next_group.get_attribute("disabled") is None:
                                current_start_val = None
                                if not is_new_ui:
                                    # [필터 전]은 data-start 속성으로 페이지 그룹 변경을 감지
                                    current_start_val = pagination.get_attribute("data-start")

                                next_group.click()
                                
                                if not is_new_ui:
                                    # [필터 전] data-start 값이 바뀔 때까지 대기
                                    wait.until(lambda d: d.find_element(By.XPATH, pagination_xpath).get_attribute("data-start") != current_start_val)
                                else:
                                    # [필터 후]는 data-start가 없으므로, '>' 버튼이 사라질 때(재로딩)까지 대기
                                    wait.until(EC.staleness_of(next_group)) 
                                
                                time.sleep(random.uniform(2.5, 4.0)) # 페이지 로딩 대기
                            else:
                                print("   [완료] 더 이상 페이지가 없습니다. ('>' 버튼 비활성화)")
                                break
                        except NoSuchElementException:
                            print("   [완료] 다음 그룹(>) 버튼 없음.")
                            break
                else:
                    print("   [완료] 단일 페이지입니다. (페이지네이션 바 없음)")
                    break

            except Exception as page_e: 
                print(f"   [오류] 페이지 순회 중 에러: {page_e}")
                traceback.print_exc() 
                break

    except Exception as e:
        print(f"   [오류] {rating_name} 수집 중 에러: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print(f"=== [{rating_name}] 종료 (최종 수집: {len(collected)}개) ===\n")
            try: driver.quit()
            except: pass
    
    return collected[:MAX_REVIEWS_PER_RATING]

if __name__ == "__main__":
    # 대상 URL
    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    
    all_results = []
    for rating in TARGET_RATINGS:
        rating_reviews = scrape_single_rating(target_url, rating)
        all_results.extend(rating_reviews)
        time.sleep(random.uniform(3, 6)) # 다음 별점 수집 전 휴식

    if all_results:
        df = pd.DataFrame(all_results)
        file_name = "coupang_reviews_final_fixed_v2.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\n🎉 [전체 완료] 총 {len(all_results)}개의 리뷰가 '{file_name}'에 저장되었습니다!")
    else:
        print("\n[알림] 수집된 리뷰가 없습니다.")