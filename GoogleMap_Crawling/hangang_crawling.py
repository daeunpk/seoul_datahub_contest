import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

# ====================================================================================
def crawl_reviews_by_count(key_words, target_reviews=50, headless=False, timeout=12):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--window-size=1280,2000")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get('https://www.google.co.kr/maps/?hl=ko')
        wait = WebDriverWait(driver, timeout)

        # 검색 및 리뷰 탭으로 이동 (기존 로직 유지)
        q = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#searchboxinput")))
        q.clear(); q.send_keys(key_words); q.send_keys(Keys.ENTER)
        time.sleep(2)

        try:
            first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.hfpxzc")))
            driver.execute_script("arguments[0].click();", first_result)
            time.sleep(1.5)
        except Exception:
            pass

        try:
            review_btn_xpath = "//button[contains(@aria-label, '리뷰') or .//div[text()='리뷰'] or .//span[text()='리뷰']]"
            review_btn = wait.until(EC.element_to_be_clickable((By.XPATH, review_btn_xpath)))
            driver.execute_script("arguments[0].click();", review_btn)
        except Exception:
            raise RuntimeError("리뷰 탭을 찾거나 클릭하는 데 실패했습니다.")

        scrollable_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf')))
        
        rows = []
        seen_review_ids = set()
        stagnant = 0
        
        print("\n[info] 리뷰 수집을 시작합니다 (스크롤과 데이터 수집 통합 방식)...")
        while True:
            if len(rows) >= target_reviews:
                print(f"[info] 목표 리뷰 수({target_reviews}개) 이상({len(rows)}개)을 수집하여 종료합니다.")
                break

            review_cards = driver.find_elements(By.XPATH, "//div[@data-review-id]")
            
            new_reviews_found_in_this_scroll = False
            for card in review_cards:
                review_id = card.get_attribute('data-review-id')
                
                if review_id not in seen_review_ids:
                    new_reviews_found_in_this_scroll = True
                    seen_review_ids.add(review_id)
                    
                    try:
                        more_button = card.find_element(By.XPATH, ".//button[contains(., '자세히') or contains(@aria-label, '더보기')]")
                        driver.execute_script("arguments[0].click();", more_button)
                        time.sleep(0.3)
                    except NoSuchElementException:
                        pass
                    except Exception as e:
                        print(f"[warn] '더보기' 버튼 클릭 중 에러: {e}")

                    try:
                        ### ★★★ 핵심 수정: main_content 확인 로직 위치 변경 ★★★
                        main_content = ""
                        try:
                            main_content = card.find_element(By.CLASS_NAME, 'wiI7pd').text
                        except NoSuchElementException:
                            # main_content를 찾지 못하면 바로 다음 리뷰로 건너뜀
                            continue
                        
                        # main_content가 비어있으면(텍스트가 없으면) 이 리뷰는 건너뜀
                        if not main_content.strip():
                            continue

                        # main_content가 있는 경우에만 태그 추출 및 나머지 작업 수행
                        tag_content = ""
                        try:
                            tag_elements = card.find_elements(By.CLASS_NAME, 'PBK6be')
                            tag_content = " ".join([tag.text for tag in tag_elements])
                        except NoSuchElementException:
                            pass
                        
                        full_content = f"{main_content} {tag_content}".strip().replace('\n', ' ')
                        
                        author = card.find_element(By.CLASS_NAME, 'd4r55').text
                        rating = card.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute('aria-label')
                        date = card.find_element(By.CLASS_NAME, 'rsqaWe').text
                        
                        rows.append({
                            '작성자': author,
                            '내용': full_content,
                            '별점': rating,
                            '작성일': date
                        })
                    except Exception as e:
                        print(f"[warn] 리뷰 데이터 추출 중 에러: {e}")
            
            print(f"리뷰 수집 중... 현재 {len(rows)} / {target_reviews}개")

            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(1.5)

            if not new_reviews_found_in_this_scroll:
                stagnant += 1
                if stagnant >= 5:
                    print("[info] 더 이상 새로운 리뷰가 로드되지 않아 수집을 중단합니다.")
                    break
            else:
                stagnant = 0

        df = pd.DataFrame(rows[:target_reviews])
        return df

    finally:
        driver.quit()
                
# ### ★★★ 핵심 수정 부분: 각 키워드마다 다른 리뷰 수를 설정 ★★★
if __name__ == "__main__":
    
    # 1. 크롤링할 키워드와 목표 리뷰 수를 딕셔너리 형태로 정의합니다.
    keywords_dict = {
        '여의도한강공원' : 1500,
        '반포한강공원' : 1500,
        '망원한강공원' : 1500,
        '잠실한강공원': 1500,
        '양화한강공원': 1500,
        '난지한강공원' : 1300,
        '광나루한강공원' : 820,
        '강서한강공원' : 208,
        '잠원한강공원(미래한강본부 잠원안내센터)' : 1500,
        '뚝섬한강공원' : 659,
        '이촌한강공원' : 1000,
    }
    
    # 2. .items()를 사용해 딕셔너리의 키(keyword)와 값(target_num)을 모두 가져옵니다.
    total_keywords = len(keywords_dict)
    for i, (keyword, target_num) in enumerate(keywords_dict.items()):
        print(f"\n{'='*60}")
        print(f"({i+1}/{total_keywords}) 번째 키워드 크롤링 시작: '{keyword}' (목표: {target_num}개)")
        print(f"{'='*60}")
        
        try:
            # 3. 함수를 호출할 때 해당 키워드의 목표 리뷰 수(target_num)를 전달합니다.
            df = crawl_reviews_by_count(keyword, target_reviews=target_num)

            if not df.empty:
                # 파일 이름에도 목표 리뷰 수를 포함하여 명확하게 만듭니다.
                file_name = f"{keyword}_{len(df)}_reviews_dic.csv"
                df.to_csv(file_name, index=False, encoding='utf-8-sig')
                print(f"\n크롤링 완료! '{file_name}' 파일로 저장이 완료되었습니다.")
                print(df.head())
            else:
                print(f"\n'{keyword}'에 대한 리뷰 데이터가 없어 파일을 저장하지 않았습니다.")
        
        except Exception as e:
            print(f"!!!!!! '{keyword}' 크롤링 중 심각한 오류 발생 !!!!!!")
            print(f"오류 메시지: {e}")
            print("!!!!!! 다음 키워드로 계속 진행합니다. !!!!!!")
            continue

    print("\n\n모든 키워드에 대한 크롤링 작업이 완료되었습니다.")