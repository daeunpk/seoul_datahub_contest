import pandas as pd
import time, random, os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

def crawl_reviews_by_count(key_words, target_reviews=700, headless=False, timeout=12, checkpoint_path=None):
    options = webdriver.ChromeOptions()
    # 1) 렌더링/메모리 줄이기
    prefs = {
        # "profile.managed_default_content_settings.images": 2,   # 이미지 차단
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 1,
    }
    options.add_experimental_option("prefs", prefs)
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--window-size=1280,2200")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, timeout)

    # 증분 저장 도우미
    def flush_checkpoint(rows):
        if not checkpoint_path or not rows:
            return
        df_ckpt = pd.DataFrame(rows)
        mode = "a" if os.path.exists(checkpoint_path) else "w"
        header = not os.path.exists(checkpoint_path)
        df_ckpt.to_csv(checkpoint_path, index=False, encoding="utf-8-sig", mode=mode, header=header)
        print(f"[checkpoint] 현재 {len(rows)}건(누적)을 '{checkpoint_path}'로 저장")

    def safe_find_all(by, sel, scope=None):
        try:
            return (scope or driver).find_elements(by, sel)
        except Exception:
            return []

    rows, seen = [], set()

    try:
        # 진입/검색
        driver.get('https://www.google.co.kr/maps/?hl=ko')
        q = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#searchboxinput")))
        q.clear(); q.send_keys(key_words); q.send_keys(Keys.ENTER)
        time.sleep(2)

        # /maps/place/ 우선 클릭
        try:
            place_links = driver.find_elements(By.XPATH, "//a[contains(@href,'/maps/place/')]")
            if place_links:
                driver.execute_script("arguments[0].click();", place_links[0])
                time.sleep(1.0)
            else:
                cards = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
                if cards:
                    driver.execute_script("arguments[0].click();", cards[0])
                    time.sleep(1.0)
        except Exception:
            pass

        # '전체 리뷰' 먼저, 실패 시 '리뷰' 탭
        see_all = None
        for xp in ["//*[contains(text(),'전체 리뷰')]",
                   "//*[contains(text(),'리뷰 모두')]",
                   "//*[contains(text(),'See all reviews')]"]:
            try:
                see_all = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, xp)))
                driver.execute_script("arguments[0].click();", see_all); time.sleep(0.8); break
            except Exception:
                pass
        if not see_all:
            btn = None
            try:
                btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="리뷰"]')))
            except Exception:
                btn = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//button[.//span[contains(text(),'리뷰')] or contains(.,'리뷰') or .//span[contains(text(),'Reviews')] or contains(.,'Reviews')]"
                )))
            driver.execute_script("arguments[0].click();", btn); time.sleep(0.8)

        # 정렬: 최신순(가능할 때)
        try:
            sort_btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((
                By.XPATH, "//button[contains(., '정렬') or contains(., 'Sort')]"
            )))
            driver.execute_script("arguments[0].click();", sort_btn); time.sleep(0.4)
            latest_btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((
                By.XPATH, "//*[contains(text(),'최신순') or contains(text(),'Newest')]"
            )))
            driver.execute_script("arguments[0].click();", latest_btn); time.sleep(0.8)
        except Exception:
            pass

        # 스크롤 컨테이너
        scroll_div = None
        for by, sel in [
            (By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf"),
            (By.XPATH, "//div[@role='region' and .//span[contains(text(),'리뷰') or contains(text(),'Reviews')]]"),
            (By.XPATH, "//div[contains(@class,'DxyBCb') and contains(@class,'m6QErb')]"),
        ]:
            try:
                scroll_div = WebDriverWait(driver, 6).until(EC.presence_of_element_located((by, sel)))
                if scroll_div: break
            except Exception:
                pass
        if not scroll_div:
            raise RuntimeError("리뷰 스크롤 컨테이너를 찾지 못했습니다.")

        def harvest_visible():
            # 더보기(본문 펼치기) — 루프당 최대 5개만 (과부하 방지)
            for b in safe_find_all(By.XPATH,
                "//button[.//span[contains(text(),'더보기')] or contains(.,'더보기') or .//span[contains(text(),'More')] or contains(.,'More')]"
            )[:5]:
                try:
                    driver.execute_script("arguments[0].click();", b)
                    time.sleep(0.03)
                except:
                    pass

            # 카드 후보
            cards = []
            for by, sel in [
                (By.CSS_SELECTOR, "div.jftiEf"),
                (By.CSS_SELECTOR, "div.jJc9Ad"),
                (By.XPATH, "//div[@data-review-id]"),
            ]:
                tmp = safe_find_all(by, sel)
                if tmp:
                    cards = tmp; break

            added = 0
            for c in cards:
                try:
                    rid = c.get_attribute("data-review-id")
                except:
                    rid = None

                # 작성자
                author = ""
                for by, sel in [(By.CSS_SELECTOR, ".d4r55"),
                                (By.XPATH, ".//div[contains(@class,'d4r55')]")]:
                    els = safe_find_all(by, sel, scope=c)
                    if els: author = els[0].text; break

                # 본문
                content = ""
                for by, sel in [(By.CSS_SELECTOR, ".wiI7pd"),
                                (By.XPATH, ".//span[contains(@class,'wiI7pd')]"),
                                (By.XPATH, ".//div[contains(@class,'MyEned')]//span")]:
                    els = safe_find_all(by, sel, scope=c)
                    if els:
                        content = " ".join(e.text for e in els).replace("\n", " ")
                        break

                # 별점
                rating = ""
                for by, sel in [(By.CSS_SELECTOR, ".kvMYJc"),
                                (By.XPATH, ".//span[contains(@aria-label,'별') or contains(@aria-label,'star')]")]:
                    els = safe_find_all(by, sel, scope=c)
                    if els:
                        rating = els[0].get_attribute("aria-label") or ""
                        break

                # 날짜
                date = ""
                for by, sel in [(By.CSS_SELECTOR, ".rsqaWe"),
                                (By.XPATH, ".//span[contains(@class,'rsqaWe')]"),
                                (By.XPATH, ".//span[contains(@class,'dehysf')]")]:
                    els = safe_find_all(by, sel, scope=c)
                    if els:
                        date = els[0].text
                        break

                key = rid or (author, date, content[:80])
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"작성자": author, "내용": content, "별점": rating, "작성일": date})
                added += 1

            return added

        stagnant = 0
        last_len = 0

        while len(rows) < target_reviews:
            try:
                gained = harvest_visible()
            except WebDriverException as e:
                # ★ 렌더러 크래시 시 부분 저장 후 종료
                print(f"[WARN] harvest 중 WebDriverException: {e}. 부분 저장 후 종료.")
                flush_checkpoint(rows)
                break

            # 스크롤(작게 여러 번) + 랜덤 지연
            for i in range(3):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_div)
                time.sleep(0.6 + random.random() * 0.5)

            # 진행/정체 판단
            if len(rows) <= last_len:
                stagnant += 1
            else:
                stagnant = 0
                last_len = len(rows)

            # 100건마다 체크포인트
            if checkpoint_path and len(rows) % 100 == 0:
                flush_checkpoint(rows)

            print(f"수집 {len(rows)} / 목표 {target_reviews}")

            # 여러 라운드 증가 없으면 종료
            if stagnant >= 6:
                print("더 이상 로드되지 않아 종료합니다.")
                break

        # 최종 결과 반환 (잘림 없이)
        return pd.DataFrame(rows[:target_reviews])

    finally:
        # 마지막으로도 체크포인트 저장 시도
        try:
            flush_checkpoint(rows)
        except Exception:
            pass
        driver.qu



# --- 함수 실행 (기존과 동일) ---
key_words = '뚝섬한강공원'
target_num_reviews = 700
out_csv = f"{key_words}_{target_num_reviews}_reviews.csv"

df = crawl_reviews_by_count(
    key_words,
    target_reviews=target_num_reviews,
    headless=False,
    timeout=12,
    checkpoint_path=out_csv  # ← 100건마다 누적 저장
)

# 최종 저장(중복 제거 옵션)
if not df.empty:
    df.drop_duplicates(subset=["작성자", "작성일", "내용"], inplace=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
print(f"\n크롤링 완료: {len(df)}건 (파일: {out_csv})")
