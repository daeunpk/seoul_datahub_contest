## 한강공원 축제 여가도 분석 스크립트
import pandas as pd
import numpy as np

# 1. 데이터 불러오기
try:
    df = pd.read_csv('measure/LEI/data/hangang_festival_list.csv')

    # 2. 샤논 다양성 지수 계산 함수 정의
    def calculate_shannon_diversity(series):
        # 축제 종류별 개수를 셉니다.
        counts = series.value_counts()
        # 각 축제가 전체에서 차지하는 비율을 계산합니다.
        proportions = counts / counts.sum()
        # 샤논 지수 공식을 적용합니다.
        shannon_index = -np.sum(proportions * np.log(proportions))
        return shannon_index

    # 3. 공원별 데이터 분석 및 여가도 계산
    # '공원명'을 기준으로 그룹화하여 분석을 수행합니다.
    park_analysis = df.groupby('park_nm').agg(
        # '축제명'의 개수를 세어 '총 축제 수'를 계산합니다.
        총_축제_수=('festival_nm', 'count'),
        # 함수를 이용해 '축제 다양성 지수'를 계산합니다.
        축제_다양성_지수=('festival_nm', calculate_shannon_diversity)
    ).reset_index()

    # 4. 최종 '여가도 점수' 산출
    # 공식을 적용하여 최종 점수를 계산합니다.
    park_analysis['여가도_점수'] = park_analysis['총_축제_수'] * (1 + park_analysis['축제_다양성_지수'])

    # 5. 결과 정렬 및 출력
    results_sorted = park_analysis.sort_values(by='여가도_점수', ascending=False)
    results_sorted = results_sorted.reset_index(drop=True)
    pd.options.display.float_format = '{:.2f}'.format

    print("--- 한강공원별 축제 여가도 분석 결과 ---")
    print(results_sorted)

    # 6. 결과 파일로 저장 (선택 사항)
    output_filename = 'hangang_park_leisure_score.csv'
    results_sorted.to_csv(output_filename, encoding='utf-8-sig', index=False)
    print(f"\n✅ 공원별 분석 결과가 '{output_filename}' 파일로 성공적으로 저장되었습니다.")


except FileNotFoundError:
    print("오류: 'hangang_festival_list.csv' 파일을 먼저 생성해야 합니다.")
except Exception as e:
    print(f"파일을 처리하는 중 오류가 발생했습니다: {e}")