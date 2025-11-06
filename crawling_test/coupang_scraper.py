import undetected_chromedriver as uc
import time
import random
import re
import json
import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

# --- 1. 설정 (사용자 입력) ---
# 스크래핑할 쿠팡 상품 URL
TARGET_URL = "https://www.coupang.com/vp/products/8070703179?itemId=22947201334&searchId=edfbc22f87a248dea8450fa5967312bc&sourceType=brandstore_display_ads-carousel&storeId=192848&subSourceType=brandstore_display_ads-carousel&vendorId=A00012012&vendorItemId=90113908086"

# 로테이팅 프록시 목록 (인증 정보 포함)
# 형식: "http://사용자이름:비밀번호@프록시주소:포트"
# 프록시를 사용하지 않으려면 이 리스트를 비워두세요: PROXIES =
PROXIES = [
    # 예시: "http://user123:pass456@proxy.example.com:8000",
    # 여기에 실제 프록시 정보를 추가하세요.
]

# 결과 및 상태 파일 이름
STATE_FILE = 'progress.json'
OUTPUT_FILE = 'reviews.csv'

# --- 2. 헬퍼 함수 및 클래스 ---

def get_random_user_agent():
    """최신 실제 User-Agent 목록에서 무작위로 하나를 반환합니다."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15'
    ]
    return random.choice(user_agents)

def initialize_driver():
    """
    undetected-chromedriver와 selenium-wire를 사용하여
    회피 기술이 적용된 드라이버 인스턴스를 생성하고 반환합니다.
    """
    options = uc.ChromeOptions()
    
    # 자동화 탐지를 피하기 위한 옵션들
    options.add_argument(f'--user-agent={get_random_user_agent()}')
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-plugins-discovery")
    
    seleniumwire_options = {}
    if PROXIES:
        proxy = random.choice(PROXIES)
        print(f"이번 세션에 사용할 프록시: {proxy.split('@')[1]}")
        seleniumwire_options = {
            'proxy': {
                'http': proxy,
                'https': proxy,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

    # 드라이버 인스턴스 생성
    driver = uc.Chrome(
        options=options,
        seleniumwire_options=seleniumwire_options,
        use_subprocess=True,# 메모리 관리 및 안정성 향상
        version_main=141
    )
    driver.set_page_load_timeout(60) # 페이지 로드 타임아웃 설정
    return driver

def humanized_delay(min_seconds=1.5, max_seconds=3.5):
    """인간과 유사한 무작위 지연을 생성합니다."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def humanized_click(driver, element):
    """
    ActionChains를 사용하여 요소를 인간처럼 클릭합니다.
    (마우스 이동 -> 잠시 멈춤 -> 클릭)
    """
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element)
        actions.pause(random.uniform(0.2, 0.7))
        actions.click()
        actions.perform()
        return True
    except Exception as e:
        print(f"클릭 중 오류 발생: {e}")
        # 예외 발생 시 JavaScript 클릭 시도
        try:
            driver.execute_script("arguments.click();", element)
            return True
        except Exception as js_e:
            print(f"JavaScript 클릭도 실패: {js_e}")
            return False

def load_state():
    """상태 파일(progress.json)에서 마지막 진행 상황을 로드합니다."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            print(f"'{STATE_FILE}'에서 진행 상황을 로드합니다.")
            return json.load(f)
    return {'last_page': 0, 'total_reviews': None, 'collected_reviews': 0}

def save_state(state):
    """현재 진행 상황을 상태 파일에 저장합니다."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)
    print(f"진행 상황 저장 완료: {state}")

def get_total_review_count(driver):
    """상품평 버튼에서 전체 리뷰 수를 파싱합니다."""
    try:
        # 상품평 탭으로 스크롤
        review_tab_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'review'))
        )
        driver.execute_script("arguments.scrollIntoView({block: 'center'});", review_tab_button)
        humanized_delay(1, 2)
        
        # 상품평 버튼 클릭
        if not humanized_click(driver, review_tab_button):
            raise Exception("상품평 탭 버튼 클릭 실패")
        print("상품평 탭으로 이동했습니다.")
        humanized_delay(2, 4)

        # 전체 리뷰 수 텍스트 가져오기
        count_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.sdp-review__average__total-star__info-count'))
        )
        count_text = count_element.text.replace(',', '') # 쉼표 제거
        
        # 정규 표현식으로 숫자만 추출
        numbers = re.findall(r'\d+', count_text)
        if numbers:
            return int(numbers)
        else:
            print("리뷰 수를 찾을 수 없습니다.")
            return 0
    except (TimeoutException, NoSuchElementException) as e:
        print(f"전체 리뷰 수를 가져오는 중 오류 발생: {e}")
        return None

def scrape_reviews_from_page(driver):
    """현재 페이지의 모든 리뷰 데이터를 스크래핑합니다."""
    reviews_data =[]
    try:
        review_elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.sdp-review__article__list'))
        )
        
        for review in review_elements:
            try:
                user_name = review.find_element(By.CSS_SELECTOR, '.sdp-review__article__list__info__user__name').text.strip()
            except NoSuchElementException:
                user_name = "N/A"
            
            try:
                rating = review.find_element(By.CSS_SELECTOR, '.sdp-review__article__list__info__product-info__star-orange').get_attribute('data-rating')
            except NoSuchElementException:
                rating = "N/A"

            try:
                product_option = review.find_element(By.CSS_SELECTOR, '.sdp-review__article__list__info__product-info__name').text.strip()
            except NoSuchElementException:
                product_option = "N/A"
            
            try:
                review_date = review.find_element(By.CSS_SELECTOR, '.sdp-review__article__list__info__user__info__date').text.strip()
            except NoSuchElementException:
                review_date = "N/A"
            
            try:
                review_content = review.find_element(By.CSS_SELECTOR, '.sdp-review__article__list__review__content').text.strip()
            except NoSuchElementException:
                review_content = "N/A"
            
            reviews_data.append({
                'user_name': user_name,
                'rating': rating,
                'product_option': product_option,
                'date': review_date,
                'content': review_content
            })
    except TimeoutException:
        print("리뷰 요소를 기다리는 중 타임아웃 발생.")
    except Exception as e:
        print(f"리뷰 스크래핑 중 예기치 않은 오류 발생: {e}")
        
    return reviews_data

def go_to_page(driver, page_number):
    """지정된 페이지 번호로 이동합니다."""
    try:
        # 페이지네이션 영역으로 스크롤
        pagination_div = driver.find_element(By.ID, 'btfTab')
        driver.execute_script("arguments.scrollIntoView({block: 'center'});", pagination_div)
        humanized_delay()

        page_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'div.sdp-review__article__page button[data-page="{page_number}"]'))
        )
        print(f"{page_number} 페이지로 이동합니다...")
        if not humanized_click(driver, page_button):
            raise Exception(f"{page_number} 페이지 버튼 클릭 실패")
        humanized_delay(2, 4) # 페이지 로딩 대기
        return True
    except TimeoutException:
        print(f"{page_number} 페이지 버튼을 찾을 수 없거나 클릭할 수 없습니다. 마지막 페이지일 수 있습니다.")
        return False
    except Exception as e:
        print(f"{page_number} 페이지로 이동 중 오류 발생: {e}")
        return False

# --- 3. 메인 실행 로직 ---

def main():
    state = load_state()
    
    # 이전에 수집된 리뷰가 있으면 DataFrame으로 로드, 없으면 새로 생성
    if os.path.exists(OUTPUT_FILE):
        all_reviews_df = pd.read_csv(OUTPUT_FILE)
    else:
        all_reviews_df = pd.DataFrame()

    # 마스터 루프: 목표를 달성하거나 더 이상 진행할 수 없을 때까지 반복
    while state['total_reviews'] is None or state['collected_reviews'] < state['total_reviews']:
        driver = None
        try:
            # --- 드라이버 초기화 및 페이지 접속 ---
            driver = initialize_driver()
            driver.get(TARGET_URL)
            print("페이지 접속 완료. 초기 렌더링 대기 중...")
            humanized_delay(3, 5)

            # --- 목표(전체 리뷰 수) 설정 ---
            if state['total_reviews'] is None:
                total_reviews = get_total_review_count(driver)
                if total_reviews is not None:
                    state['total_reviews'] = total_reviews
                    save_state(state)
                else:
                    print("전체 리뷰 수를 가져올 수 없어 스크립트를 종료합니다.")
                    break # 루프 탈출
            
            print(f"총 목표 리뷰 수: {state['total_reviews']}, 현재까지 수집된 리뷰 수: {state['collected_reviews']}")

            # --- 작업 재개 페이지로 이동 ---
            start_page = state['last_page'] + 1
            if start_page > 1:
                print(f"작업을 재개합니다. {start_page} 페이지부터 시작합니다.")
                if not go_to_page(driver, start_page):
                    print("시작 페이지로 이동 실패. 스크립트를 잠시 후 재시도합니다.")
                    raise WebDriverException("재개 페이지 이동 실패")

            # --- 스크래핑 및 페이지네이션 루프 ---
            current_page = start_page
            while True:
                print(f"--- {current_page} 페이지 스크래핑 시작 ---")
                
                # 현재 페이지 리뷰 수집
                new_reviews = scrape_reviews_from_page(driver)
                if new_reviews:
                    new_reviews_df = pd.DataFrame(new_reviews)
                    all_reviews_df = pd.concat([all_reviews_df, new_reviews_df], ignore_index=True)
                    
                    # 중복 제거 및 저장
                    all_reviews_df.drop_duplicates(subset=['user_name', 'date', 'content'], keep='last', inplace=True)
                    all_reviews_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
                    
                    # 상태 업데이트
                    state['last_page'] = current_page
                    state['collected_reviews'] = len(all_reviews_df)
                    save_state(state)
                    print(f"{len(new_reviews)}개의 신규 리뷰 수집. 총 {state['collected_reviews']}개 리뷰 저장 완료.")
                else:
                    print("현재 페이지에서 수집된 리뷰가 없습니다. 다음 페이지로 넘어갑니다.")

                # 목표 달성 여부 확인
                if state['total_reviews'] is not None and state['collected_reviews'] >= state['total_reviews']:
                    print("목표한 모든 리뷰를 수집했습니다. 스크립트를 종료합니다.")
                    return # 성공적으로 종료

                # 다음 페이지로 이동
                current_page += 1
                if not go_to_page(driver, current_page):
                    print("더 이상 다음 페이지가 없습니다. 스크래핑을 종료합니다.")
                    return # 성공적으로 종료

        except (WebDriverException, Exception) as e:
            print(f"마스터 루프에서 심각한 오류 발생: {e}")
            print("드라이버를 재시작하고 30초 후에 작업을 재개합니다...")
            if driver:
                driver.quit()
            time.sleep(30) # 재시도 전 대기 시간
        
        finally:
            if driver:
                driver.quit()

if __name__ == "__main__":
    main()