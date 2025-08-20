import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

        # 검색
        q = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#searchboxinput")))
        q.clear(); q.send_keys(key_words); q.send_keys(Keys.ENTER)

        # 결과가 두 가지 레이아웃 중 하나로 뜸: (1) 리스트 (2) 이미 상세
        time.sleep(2)

        # 1) 리스트가 보이면 첫 항목 클릭 (실패해도 넘어감)
        try:
            first_result = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
            if first_result:
                driver.execute_script("arguments[0].click();", first_result[0])
                time.sleep(1.5)
        except Exception:
            pass  # 이미 상세면 통과

        # 리뷰 탭 열기: CSS 먼저, 실패 시 XPath
        review_btn = None
        try:
            review_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="리뷰"]')))
        except Exception:
            pass
        if not review_btn:
            review_btn = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[.//span[contains(text(),'리뷰')] or contains(.,'리뷰') or .//span[contains(text(),'Reviews')] or contains(.,'Reviews')]"
            )))
        driver.execute_script("arguments[0].click();", review_btn)

        # 스크롤 컨테이너: 당신이 쓰던 셀렉터를 고정 사용
        scrollable_sel = 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'
        scrollable_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_sel)))

        # 리뷰 아이템 셀렉터(다중 후보)
        item_selectors = [
            (By.CSS_SELECTOR, "div.jftiEf"),
            (By.CSS_SELECTOR, "div.jJc9Ad"),
            (By.XPATH, "//div[@data-review-id]"),
        ]
        def review_count():
            for by, sel in item_selectors:
                els = driver.find_elements(by, sel)
                if els:
                    return len(els)
            return 0

        last = 0
        stagnant = 0
        while True:
            cnt = review_count()
            if cnt >= target_reviews:
                break

            # 당신 방식 그대로: 컨테이너에 직접 scrollTop
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(1.2)

            new_cnt = review_count()
            if new_cnt <= last:
                stagnant += 1
                if stagnant >= 5:
                    # 더 안 늘어나면 중단
                    break
            else:
                stagnant = 0
            last = new_cnt

        # 데이터 수집(당신 셀렉터 유지)
        author_elements  = driver.find_elements(By.CLASS_NAME, 'd4r55')[:target_reviews]
        content_elements = driver.find_elements(By.CLASS_NAME, 'wiI7pd')[:target_reviews]
        rating_elements  = driver.find_elements(By.CLASS_NAME, 'kvMYJc')[:target_reviews]
        date_elements    = driver.find_elements(By.CLASS_NAME, 'rsqaWe')[:target_reviews]

        data = {
            '작성자': [e.text for e in author_elements],
            '내용'  : [e.text.replace('\n', ' ') for e in content_elements],
            '별점'  : [e.get_attribute('aria-label') for e in rating_elements],
            '작성일': [e.text for e in date_elements],
        }
        min_len = min(len(v) for v in data.values()) if all(len(v)>0 for v in data.values()) else 0
        if min_len == 0:
            # 리뷰 카드 구조가 살짝 다를 때를 대비한 보정 (긴 본문 펼치기 등)
            # 필요시 여기서 '더보기' 버튼 클릭 루프 추가 가능
            pass

        df = pd.DataFrame({k: v[:min_len] for k, v in data.items()})
        return df

    finally:
        driver.quit()



# --- 함수 실행 (기존과 동일) ---
key_words = '강서한강공원'
target_num_reviews = 2000

df = crawl_reviews_by_count(key_words, target_reviews=target_num_reviews)
print(df)

file_name = f"{key_words}_{target_num_reviews}_reviews.csv"
df.to_csv(file_name, index=False, encoding='utf-8-sig')

print(f"\n크롤링 완료! '{file_name}' 파일로 저장이 완료되었습니다.")
print(df.head())