import pandas as pd
import numpy as np

# 1. 데이터 불러오기
try:
    df = pd.read_csv('../LEI/data/seoul_culture_event.csv')

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

    # 5. 최종 '여가도 점수' 산출
    leisure_analysis['여가도_점수'] = leisure_analysis['총_행사_수'] * (1 + leisure_analysis['행사_다양성_지수'])

    # 6. 결과 정렬
    results_sorted = leisure_analysis.sort_values(by='여가도_점수', ascending=False)
    results_sorted = results_sorted.reset_index(drop=True)
    pd.options.display.float_format = '{:.2f}'.format

    # 7. 결과 출력
    print("--- 서울시 자치구별 문화행사 여가도 분석 결과 ---")
    print(results_sorted)

    # 8. CSV 파일로 저장 (추가된 부분)
    # 한글이 깨지지 않도록 'utf-8-sig' 인코딩을 사용합니다.
    # index=False는 불필요한 순번(0,1,2...)이 파일에 저장되지 않도록 합니다.
    output_filename = '../LEI/results/seoul_culture_event.csv'
    results_sorted.to_csv(output_filename, encoding='utf-8-sig', index=False)

    print(f"\n✅ 분석 결과가 '{output_filename}' 파일로 성공적으로 저장되었습니다.")


except FileNotFoundError:
    print("오류: 'seoul_culture_event.csv' 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"파일을 처리하는 중 오류가 발생했습니다: {e}")