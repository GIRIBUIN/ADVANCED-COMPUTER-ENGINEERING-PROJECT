# RA/review_analyzer/crawling/Recommend_Product.py

"""
주어진 쿠팡 상품 페이지에서 키워드를 추출하여,
관련된 유사 상품 링크를 수집하는 모듈입니다.
"""

import time
import pandas as pd
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# (참고: ActionChains, random, NoSuchElementException 등은
#  이 파일에서 사용하는 함수에 필요하지 않아 import에서 제외하거나 주석 처리 가능합니다.)


def setup_driver():
    """undetected_chromedriver 초기화"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    try:
        driver = uc.Chrome(options=options, version_main=143)
    except Exception as e:
        print(f"[드라이버 로드 오류] {e}")
        print("version_main=141을 제거하고 자동 감지 모드로 다시 시도합니다.")
        driver = uc.Chrome(options=options)
    return driver

# ===================================================================
# [유사 상품 링크 수집 함수]
# : 상품 URL을 기반으로 키워드를 추출하고,
#   관련 상품 상위 3개의 링크를 반환합니다.
# ===================================================================

def get_related_product_links(target_url):
    """
    주어진 쿠팡 상품 URL에서 키워드를 추출하여 재검색한 후,
    상위 3개 상품의 링크를 반환합니다.
    """
    print(f"\n--- [유사 상품 링크 수집 시작] URL: {target_url[:50]}... ---")
    driver = None
    search_keyword = None
    links = []

    try:
        # 1. 드라이버 설정 및 페이지 접근
        driver = setup_driver()
        wait = WebDriverWait(driver, 30) # 로딩/캡차 대기 시간 30초
        driver.get(target_url)
        print("  -> 페이지 로드 대기 중...")
        # product-title이 로드될 때까지 대기
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-title")))
        time.sleep(2) # 추가 스크립트 로드 대기

        # --- [키워드 추출 로직] ---

        # 2. (1순위) '종류' 정보 탐색
        try:
            print("  -> (1순위) '상품 정보 > 종류' 탐색 중...")
            product_desc_div = driver.find_element(By.XPATH, "//div[contains(@class, 'product-description')]")
            kind_li = product_desc_div.find_element(By.XPATH, ".//li[contains(text(), '종류:')]")
            full_text = kind_li.text.strip()
            search_keyword = full_text.split(":")[-1].strip()
            
            if search_keyword:
                print(f"      -> 1순위 키워드 찾음: '{search_keyword}'")
            else:
                raise Exception("1순위 '종류:' 텍스트는 찾았으나 값이 비어있음")
                
        except Exception as e1:
            print(f"      -> 1순위 탐색 실패 또는 '종류' 항목 없음. (이유: {str(e1).splitlines()[0][:60]})")
            
            # 3. (2순위) '상품명' 탐색 (1순위 실패 시)
            if not search_keyword:
                try:
                    print("  -> (2순위) '상품명' 탐색 중...")
                    title_element = driver.find_element(By.CSS_SELECTOR, "h1.product-title span[class*='twc-font-bold']")
                    full_title = title_element.text.strip()
                    search_keyword = full_title.split(",")[0].strip() if "," in full_title else full_title
                        
                    if search_keyword:
                        print(f"      -> 2순위 키워드 찾음: '{search_keyword}'")
                    else:
                        raise Exception("2순위 '상품명'은 찾았으나 텍스트가 비어있음")
                        
                except Exception as e2:
                    print(f"      -> 2순위 탐색 실패. (이유: {str(e2).splitlines()[0][:60]})")
                    print(f"  [오류] 검색 키워드를 찾을 수 없습니다.")
                    return []

        if not search_keyword:
            print("  [오류] 1, 2순위 모두 실패하여 키워드를 확정할 수 없습니다.")
            return []

        # --- [재검색 및 링크 추출 로직] ---
        
        # 4. 키워드로 쿠팡 검색
        print(f"\n  -> '{search_keyword}' (으)로 쿠팡 재검색 시작...")
        search_url = f"https://www.coupang.com/np/search?q={search_keyword}"
        driver.get(search_url)

        # 5. 검색 결과(productList) 또는 "상품 없음" 메시지가 뜰 때까지 대기
        print("  -> 검색 결과 페이지 로딩 대기 중 (새 구조)")
        
        # 새 HTML 구조에 맞게 대기 XPath 변경 (li의 클래스 ProductUnit_productUnit__Qd6sv 를 기다림)
        robust_search_xpath = "//li[contains(@class, 'ProductUnit_productUnit')] | //div[contains(@class, 'search-empty-result')]"
        wait.until(EC.presence_of_element_located((By.XPATH, robust_search_xpath)))

        # 6. 상위 3개 상품(li.ProductUnit_productUnit__Qd6sv)의 링크(a) 추출
        
        # 새 HTML 구조에 맞게 상품 목록 CSS 선택자 변경
        product_items = driver.find_elements(By.CSS_SELECTOR, "li[class*='ProductUnit_productUnit__']")
        
        if not product_items:
            print("  -> 검색 결과가 없습니다. (상품 없음)")
            return []
            
        print(f"  -> 검색 결과 {len(product_items)}개 확인. 상위 3개 링크 추출 중...")
        
        count = 0
        for item in product_items:
            if count >= 3:
                break
            
            try:
                # 각 li > a 태그의 href 속성 값 추출
                link_element = item.find_element(By.CSS_SELECTOR, "a")
                href = link_element.get_attribute("href")
                
                if href:
                    if href.startswith("/vp/"):
                        href = "https://www.coupang.com" + href
                    
                    if href.startswith("https://www.coupang.com/vp/"):
                        links.append(href)
                        count += 1
                        print(f"      -> 링크 {count} 수집 완료.")
                    
            except Exception as link_e:
                print(f"      -> [오류] 개별 항목 링크 추출 실패: {link_e}")
                continue 
                        
    except TimeoutException:
        print("  [치명적 오류] 30초 내에 검색 결과 또는 '상품 없음' 메시지를 찾지 못했습니다.")
        print("      -> 캡차(보안 문자) 페이지에 막혔을 가능성이 높습니다.")
        traceback.print_exc()

    except Exception as main_e:
        print(f"  [치명적 오류] get_related_product_links 함수 실행 중단: {main_e}")
        traceback.print_exc()
    
    finally:
        if driver:
            try: 
                driver.quit()
                print(f"--- [유사 상품 링크 수집 종료] 총 {len(links)}개 링크 반환 ---")
            except: 
                pass
    
    return links


if __name__ == "__main__":
    # 대상 URL (예: 참치액)
    target_url = "https://www.coupang.com/vp/products/7224339339?vendorItemId=3051369121&sourceType=SDP_ALSO_VIEWED"
    
    # [새 함수 테스트 및 엑셀 저장]
    related_links = get_related_product_links(target_url)
    
    if related_links:
        print("\n[최종 수집된 관련 상품 링크]")
        for i, link in enumerate(related_links):
            print(f"{i+1}: {link}")
        
        # --- [엑셀 저장 로직 추가] ---
        try:
            # 1. DataFrame 생성 (리스트를 'Related_Links'라는 컬럼으로 만듦)
            df_links = pd.DataFrame(related_links, columns=["Related_Links"])
            
            # 2. 파일 이름 설정
            links_file_name = "related_product_links.xlsx"
            
            # 3. 엑셀로 저장 (인덱스 제외)
            df_links.to_excel(links_file_name, index=False)
            
            print(f"\n🎉 [저장 완료] 총 {len(related_links)}개의 링크가 '{links_file_name}'에 저장되었습니다!")
            
        except Exception as e:
            print(f"\n[오류] 링크를 엑셀 파일로 저장하는 중 문제가 발생했습니다: {e}")
            
    else:
        print("\n[알림] 수집된 관련 상품 링크가 없습니다.")