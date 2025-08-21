import pandas as pd
import time, random, hashlib, os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def crawl_reviews_by_count(key_words, target_reviews=700, headless=False, timeout=15, checkpoint_path=None):
    # --- 브라우저 옵션 ---
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--window-size=1280,2200")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, timeout)

    # --- 유틸리티 함수 ---
    def stable_key(rid, author, date, content):
        if rid: return f"id::{rid}"
        base = f"{(author or '').strip()}|{(date or '').strip()}|{(content or '').strip()[:120]}"
        return "mix::" + hashlib.md5(base.encode("utf-8", "ignore")).hexdigest()

    def flush_checkpoint(rows_list):
        if not checkpoint_path or not rows_list: return
        pd.DataFrame(rows_list).to_csv(checkpoint_path, index=False, encoding="utf-8-sig", mode="w", header=True)
        print(f"[checkpoint] 누적 {len(rows_list)}건 저장 → {checkpoint_path}")

    # --- 크롤링 본 작업 ---
    rows, seen_keys = [], set()
    try:
        driver.get('https://www.google.co.kr/maps/?hl=ko')
        q = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#searchboxinput")))
        q.clear(); q.send_keys(key_words); q.send_keys(Keys.ENTER)

        ### ★★★ 1. 검색 결과 클릭 로직 강화 ★★★
        # 검색 결과 목록(왼쪽 패널)이 나타날 때까지 기다립니다.
        print("[info] 검색 결과 로딩 대기 중...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf, div[aria-label^='검색 결과']")))
        
        # 첫 번째 결과(a.hfpxzc)를 찾아 클릭합니다.
        try:
            first_result_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.hfpxzc")))
            driver.execute_script("arguments[0].click();", first_result_link)
            print("[info] 첫 번째 검색 결과 클릭 완료.")
        except TimeoutException:
            print("[warn] 검색 결과 목록에서 첫 항목을 찾을 수 없습니다. 이미 상세 페이지일 수 있습니다.")
            pass # 이미 상세 페이지로 바로 넘어간 경우

        ### ★★★ 2. 상세 정보 패널 전환 대기 ★★★
        # 리뷰 탭이 나타날 때까지 기다려서, 화면이 상세 정보창으로 완전히 전환되었음을 보장합니다.
        print("[info] 상세 정보 패널 로딩 및 리뷰 탭 대기 중...")
        try:
            xpath = "//button[.//div[text()='리뷰'] or .//span[text()='리뷰'] or text()='리뷰']"
            review_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", review_btn)
            print("[info] 리뷰 탭 클릭 완료.")
        except TimeoutException:
            raise RuntimeError("상세 정보 패널에서 리뷰 탭을 찾는 데 실패했습니다.")
        
        ### ★★★ 3. 올바른 스크롤 대상 지정 ★★★
        # 리뷰 탭을 클릭한 '이후에' 스크롤 대상을 찾음으로써, '리뷰 목록'을 정확히 지정합니다.
        print("[info] 리뷰 스크롤 패널 찾는 중...")
        scroll_div_selector = 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf[role="main"]'
        scroll_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, scroll_div_selector)))
        
        # 리뷰 카드(항목)를 찾는 함수
        def find_cards():
            return driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf') and @data-review-id]")

        # 화면에 보이는 리뷰 수집
        def harvest_visible():
            for card in find_cards():
                try:
                    # ... (이하 데이터 수집 로직은 이전과 거의 동일)
                    rid = card.get_attribute("data-review-id")
                    author = card.find_element(By.CSS_SELECTOR, ".d4r55").text
                    date = card.find_element(By.CSS_SELECTOR, ".rsqaWe").text
                    content_element = card.find_element(By.CSS_SELECTOR, ".wiI7pd")
                    
                    try:
                        more_btn = content_element.find_element(By.XPATH, ".//button[contains(., '더보기')]")
                        driver.execute_script("arguments[0].click();", more_btn)
                    except Exception: pass
                    
                    content = content_element.text
                    rating = card.find_element(By.CSS_SELECTOR, ".kvMYJc").get_attribute("aria-label") or ""
                    
                    key = stable_key(rid, author, date, content)
                    if key in seen_keys: continue
                    
                    seen_keys.add(key)
                    rows.append({"작성자": author, "내용": content.replace("\n", " "), "별점": rating, "작성일": date})
                except Exception: continue
        
        # 스크롤 루프
        stagnant, last_len = 0, -1
        while len(rows) < target_reviews:
            harvest_visible()
            scroll_div.send_keys(Keys.END)
            time.sleep(1.5 + random.random())

            current_len = len(rows)
            if current_len == last_len: stagnant += 1
            else: stagnant = 0
            
            print(f"수집 {current_len} / 목표 {target_reviews} (정체: {stagnant})")
            last_len = current_len

            if stagnant >= 5:
                print("[info] 더 이상 새로운 리뷰가 없어 수집을 종료합니다.")
                break
            
            if checkpoint_path and (len(rows) % 100 < 10 and len(rows) > 0 and len(rows) != last_len):
                flush_checkpoint(rows)

        return pd.DataFrame(rows[:target_reviews])

    finally:
        if checkpoint_path and rows: flush_checkpoint(rows)
        driver.quit()

# --- 실행 코드 ---
if __name__ == "__main__":
    key_words = "잠원한강공원"
    target_num_reviews = 700
    checkpoint_file = f"{key_words}_reviews_checkpoint.csv"

    df = crawl_reviews_by_count(key_words, target_reviews=target_num_reviews, checkpoint_path=checkpoint_file)
    
    final_file = f"{key_words}_reviews_final.csv"
    if not df.empty:
        df.drop_duplicates(subset=["작성자", "작성일", "내용"], inplace=True, keep='first')
        df.to_csv(final_file, index=False, encoding="utf-8-sig")
        print(f"\n크롤링 완료: 최종 {len(df)}건 저장 → {final_file}")
        print(df.head())
    else:
        print("\n크롤링된 데이터가 없습니다.")