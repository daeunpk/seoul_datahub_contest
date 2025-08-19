## 구별 행사 여가도
import pandas as pd
import numpy as np

# 1. 데이터 불러오기
try:
    df = pd.read_csv('measure/LEI/data/seoul_culture_event.csv')

    # 2. 데이터 전처리
    df_cleaned = df.dropna(subset=['자치구', '분류'])
    df_cleaned = df_cleaned[~df_cleaned['자치구'].isin(['서울', ' '])]

    # 3. 샤논 다양성 지수 계산 함수 정의
    def calculate_shannon_diversity(series):
        counts = series.value_counts()
        proportions = counts / counts.sum()
        shannon_index = -np.sum(proportions * np.log(proportions))
        return shannon_index

    # 4. 구별 데이터 분석 및 여가도 계산
    leisure_analysis = df_cleaned.groupby('자치구').agg(
        총_행사_수=('분류', 'count'),
        행사_다양성_지수=('분류', calculate_shannon_diversity)
    ).reset_index()

# 5. 원본 '여가도 점수' 산출 (표준점수 계산의 기반으로 사용)
    leisure_analysis['여가도_점수_원본'] = leisure_analysis['총_행사_수'] * (1 + leisure_analysis['행사_다양성_지수'])

    # 6. 표준점수(Z-score) 방식으로 점수 조정 (새로운 방식)
    raw_score = leisure_analysis['여가도_점수_원본']
    score_mean = raw_score.mean()
    score_std = raw_score.std()

    # 표준편차가 0일 경우(모든 값이 같을 경우) 오류 방지
    if score_std > 0:
        leisure_analysis['여가도_조정점수'] = ((raw_score - score_mean) / score_std) * 10 + 50
    else:
        leisure_analysis['여가도_조정점수'] = 50 # 모든 구의 점수가 같다면 전부 50점

# 7. 최종 결과 정렬 및 출력
    # 새로 만든 '여가도_조정점수'를 기준으로 정렬합니다.
    results_sorted = leisure_analysis.sort_values(by='여가도_조정점수', ascending=False)
    results_sorted = results_sorted.reset_index(drop=True)
    pd.options.display.float_format = '{:.2f}'.format

    print("--- 서울시 자치구별 문화행사 여가도 분석 결과 (표준점수 적용) ---")
    print(results_sorted[['자치구', '여가도_조정점수', '총_행사_수', '행사_다양성_지수']])

    # 8. CSV 파일로 저장
    output_filename = 'measure/LEI/results/gu_leisure_score.csv'
    results_sorted.to_csv(output_filename, encoding='utf-8-sig', index=False)

    print(f"\n✅ 조정된 분석 결과가 '{output_filename}' 파일로 성공적으로 저장되었습니다.")

except FileNotFoundError:
    print("오류: 'seoul_culture_event.csv' 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"파일을 처리하는 중 오류가 발생했습니다: {e}")