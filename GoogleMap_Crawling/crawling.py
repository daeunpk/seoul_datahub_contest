import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def crawl_reviews_local(key_words, number_of_scrolls, num_reviews=10):
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        url = 'https://www.google.co.kr/maps/?hl=ko'
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        
        # --- 2. 검색 및 리뷰 탭 클릭 ---
        query_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#searchboxinput')))
        query_input.send_keys(key_words)
        query_input.send_keys(Keys.ENTER)

        # ★★★★★ 핵심 수정 부분 ★★★★★
        # 검색 결과 패널이 로드될 때까지 명시적으로 기다립니다.
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf')))
        
        review_tab_selector = 'button[aria-label*="리뷰"]'
        review_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, review_tab_selector)))
        review_tab.click()

        # --- 3. 스크롤 ---
        scrollable_div_selector = 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'
        scrollable_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_div_selector)))
        
        for i in range(number_of_scrolls):
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            print(f"Scrolling... {i+1}/{number_of_scrolls}")
            time.sleep(1.5)
        
        # --- 4. 데이터 수집 ---
        author_elements = driver.find_elements(By.CLASS_NAME, 'd4r55')[:num_reviews] # 작성자
        content_elements = driver.find_elements(By.CLASS_NAME, 'wiI7pd')[:num_reviews] # 내용
        rating_elements = driver.find_elements(By.CLASS_NAME, 'kvMYJc')[:num_reviews] # 별점
        date_elements = driver.find_elements(By.CLASS_NAME, 'rsqaWe')[:num_reviews] # 작성일
        
        data = {
            '작성자': [element.text for element in author_elements],
            # .text로 텍스트를 가져온 후 .replace('\n', ' ')를 추가하여 줄 바꿈을 공백으로 변경
            '내용': [element.text.replace('\n', ' ') for element in content_elements],
            '별점': [element.get_attribute('aria-label') for element in rating_elements],
            '작성일': [element.text for element in date_elements]
        }
        
        min_length = min(len(v) for v in data.values())
        df = pd.DataFrame({k: v[:min_length] for k, v in data.items()})
        
        return df

    finally:
        driver.quit()

# --- 함수 실행 ---
key_words = '뚝섬한강공원'
number_of_scrolls = 50000
num_re = 50

df = crawl_reviews_local(key_words, number_of_scrolls, num_re)
print(df)

# 2. 데이터프레임을 CSV 파일로 저장
# 파일 이름은 '검색어_reviews.csv' 형식으로 만들어집니다.
file_name = f"{key_words}_reviews.csv"
# index=False: 데이터프레임의 인덱스(0, 1, 2...)는 저장하지 않음
# encoding='utf-8-sig': 한글이 깨지지 않도록 설정 (특히 Windows Excel에서 중요)
df.to_csv(file_name, index=False, encoding='utf-8-sig')

print(f"\n크롤링 완료! '{file_name}' 파일로 저장이 완료되었습니다.")
print("\n--- 저장된 데이터 샘플 ---")
print(df.head())