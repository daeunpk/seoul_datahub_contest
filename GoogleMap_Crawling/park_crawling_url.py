import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# ====================================================================================
def crawl_reviews_by_count(key_words=None, target_reviews=50, headless=False, timeout=12, place_url=None):
    """
    key_words: 키워드 검색어 (place_url이 없을 때 사용)
    place_url: 구글맵 장소 상세 URL (이 값이 있으면 키워드 검색을 건너뜀)
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--window-size=1280,2000")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        wait = WebDriverWait(driver, timeout)

        # --- 0) URL 모드: 장소 링크로 직접 진입 ---
        if place_url:
            # hl=ko 보장
            if "hl=ko" not in place_url:
                sep = "&" if "?" in place_url else "?"
                place_url = f"{place_url}{sep}hl=ko"
            driver.get(place_url)
        else:
            # --- 1) 키워드 모드: 검색 후 첫 결과 진입 ---
            driver.get('https://www.google.co.kr/maps/?hl=ko')
            q = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#searchboxinput")))
            q.clear(); q.send_keys(key_words); q.send_keys(Keys.ENTER)
            time.sleep(2)

            try:
                first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.hfpxzc")))
                driver.execute_script("arguments[0].click();", first_result)
                time.sleep(1.5)
            except Exception:
                pass

        # --- 2) 리뷰 탭으로 이동 ---
        # 2-a) 현재 페이지에 리뷰 버튼이 있으면 클릭
        try:
            review_btn_xpath = "//button[contains(@aria-label, '리뷰') or .//div[text()='리뷰'] or .//span[text()='리뷰']]"
            review_btn = wait.until(EC.element_to_be_clickable((By.XPATH, review_btn_xpath)))
            driver.execute_script("arguments[0].click();", review_btn)
        except TimeoutException:
            # 2-b) 일부 페이지는 리뷰 카운트(“리뷰 n개”) 버튼만 보이는 경우가 있어 대체 시도
            try:
                alt_xpath = "//button[contains(., '리뷰') and (contains(., '개') or contains(., '전체'))]"
                alt_btn = wait.until(EC.element_to_be_clickable((By.XPATH, alt_xpath)))
                driver.execute_script("arguments[0].click();", alt_btn)
            except TimeoutException:
                raise RuntimeError("리뷰 탭(또는 리뷰 보기 버튼)을 찾거나 클릭하는 데 실패했습니다.")

        # --- 3) 리뷰 스크롤 영역 확보 ---
        scrollable_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf')))

        rows = []
        seen_review_ids = set()
        stagnant = 0

        print("\n[info] 리뷰 수집을 시작합니다 (URL/키워드 공통 로직)...")
        while True:
            if len(rows) >= target_reviews:
                print(f"[info] 목표 리뷰 수({target_reviews}개) 이상({len(rows)}개)을 수집하여 종료합니다.")
                break

            # 리뷰 카드
            review_cards = driver.find_elements(By.XPATH, "//div[@data-review-id]")

            new_reviews_found_in_this_scroll = False
            for card in review_cards:
                review_id = card.get_attribute('data-review-id') or ""
                if not review_id:
                    continue
                if review_id in seen_review_ids:
                    continue

                # 새 리뷰
                new_reviews_found_in_this_scroll = True
                seen_review_ids.add(review_id)

                # 더보기 펼치기
                try:
                    more_button = card.find_element(By.XPATH, ".//button[contains(., '자세히') or contains(@aria-label, '더보기')]")
                    driver.execute_script("arguments[0].click();", more_button)
                    time.sleep(0.2)
                except NoSuchElementException:
                    pass
                except Exception as e:
                    print(f"[warn] '더보기' 버튼 클릭 중 에러: {e}")

                # 본문 + 태그(볼드) 결합
                try:
                    main_content = ""
                    try:
                        main_content = card.find_element(By.CLASS_NAME, 'wiI7pd').text
                    except NoSuchElementException:
                        pass

                    tag_content = ""
                    try:
                        tag_elements = card.find_elements(By.CLASS_NAME, 'PBK6be')
                        tag_content = " ".join([t.text for t in tag_elements if t.text.strip()])
                    except NoSuchElementException:
                        pass

                    full_content = f"{main_content} {tag_content}".strip().replace('\n', ' ')

                    # 작성자 / 별점 / 날짜
                    author = ""
                    try:
                        author = card.find_element(By.CLASS_NAME, 'd4r55').text
                    except NoSuchElementException:
                        # 대체 셀렉터 시도 (간혹 클래스가 바뀌는 경우)
                        try:
                            author = card.find_element(By.XPATH, ".//button[contains(@aria-label,'프로필')]/div").text
                        except Exception:
                            author = ""

                    # 별점은 aria-label: "별표 N개"
                    rating = ""
                    try:
                        rating = card.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute('aria-label')
                    except NoSuchElementException:
                        # 대체: role='img' + aria-label
                        try:
                            rating = card.find_element(By.XPATH, ".//*[@role='img' and contains(@aria-label,'별표')]").get_attribute('aria-label')
                        except Exception:
                            rating = ""

                    date_txt = ""
                    try:
                        date_txt = card.find_element(By.CLASS_NAME, 'rsqaWe').text
                    except NoSuchElementException:
                        # 대체: time 태그
                        try:
                            date_txt = card.find_element(By.XPATH, ".//span/time").text
                        except Exception:
                            date_txt = ""

                    # 불필요 조각(타임코드 등) 제거: "0:06" 같은 패턴
                    full_content = re.sub(r"\b\d{1,2}:\d{2}\b", "", full_content).strip()

                    rows.append({
                        "작성자": author,
                        "내용": full_content,
                        "별점": rating,
                        "작성일": date_txt
                    })

                except Exception as e:
                    print(f"[warn] 리뷰 데이터 추출 중 에러: {e}")

            print(f"리뷰 수집 중... 현재 {len(rows)} / {target_reviews}개")

            # 스크롤 다운
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(1.3)

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


# ============================
# 사용 예시
# ============================
if __name__ == "__main__":
    # ❶ URL로 바로 크롤링 (요청하신 서울대공원 링크)
    PLACE_URL = "https://maps.app.goo.gl/5sWZUxuAvqb1oZLP8"

    try:
        df = crawl_reviews_by_count(
            key_words=None,
            place_url=PLACE_URL,      # ← 링크만 넣으면 됨
            target_reviews=1500,       # 원하는 개수
            headless=False,           # 서버/CLI면 True 추천
            timeout=12
        )
        if not df.empty:
            out = f"서울대공원_{len(df)}_reviews_from_url.csv"
            df.to_csv(out, index=False, encoding="utf-8-sig")
            print(f"\n저장 완료: {out}")
            print(df.head())
        else:
            print("리뷰가 비어 있습니다.")
    except Exception as e:
        print("에러:", e)

    # ❷ (선택) 키워드 모드도 그대로 사용 가능
    # df2 = crawl_reviews_by_count(key_words="서울대공원", target_reviews=200, headless=True)
