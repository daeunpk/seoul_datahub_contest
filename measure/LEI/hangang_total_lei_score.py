import pandas as pd
import numpy as np

try:
    # 1. 두 개의 분석 결과 파일 불러오기
    df_festival = pd.read_csv('measure/LEI/results/hangang_park_leisure_score.csv')
    df_sports = pd.read_csv('measure/LEI/results/hangang_sports_leisure_score.csv')

    # 2. '공원명'을 기준으로 두 데이터프레임 병합
    df_merged = pd.merge(df_festival[['공원명', '여가도_점수']],
                         df_sports[['공원명', '운동_여가도_점수']],
                         on='공원명', how='outer')
    df_merged = df_merged.fillna(0)

    # 3. 각 점수를 표준점수(Z-score)로 변환 후, T-점수(평균 50, 표준편차 10)로 조정
    # 축제 여가도 점수 조정
    fest_mean = df_merged['여가도_점수'].mean()
    fest_std = df_merged['여가도_점수'].std()
    # 표준편차가 0일 경우(모든 값이 같을 경우) 대비
    if fest_std > 0:
        df_merged['축제_조정점수'] = ((df_merged['여가도_점수'] - fest_mean) / fest_std) * 10 + 50
    else:
        df_merged['축제_조정점수'] = 50

    # 운동 여가도 점수 조정
    sport_mean = df_merged['운동_여가도_점수'].mean()
    sport_std = df_merged['운동_여가도_점수'].std()
    if sport_std > 0:
        df_merged['운동_조정점수'] = ((df_merged['운동_여가도_점수'] - sport_mean) / sport_std) * 10 + 50
    else:
        df_merged['운동_조정점수'] = 50

    # 4. 최종 '종합 여가도 점수' 계산 (5:5 가중치)
    df_merged['종합_여가도_점수'] = (df_merged['축제_조정점수'] * 0.5) + (df_merged['운동_조정점수'] * 0.5)

    # 5. 결과 정렬 및 출력
    final_results = df_merged[['공원명', '종합_여가도_점수', '축제_조정점수', '운동_조정점수']]
    results_sorted = final_results.sort_values(by='종합_여가도_점수', ascending=False).reset_index(drop=True)
    pd.options.display.float_format = '{:.2f}'.format
    
    print("--- 한강공원 종합 여가도 분석 결과 (표준점수 적용) ---")
    print(results_sorted)
    
    # 6. 최종 결과 파일로 저장
    output_filename = 'hangang_total_leisure_score_adjusted.csv'
    results_sorted.to_csv(output_filename, encoding='utf-8-sig', index=False)
    print(f"\n✅ 조정된 종합 분석 결과가 '{output_filename}' 파일로 성공적으로 저장되었습니다.")

except FileNotFoundError as e:
    print(f"오류: 필요한 CSV 파일을 찾을 수 없습니다. ({e.filename})")
except Exception as e:
    print(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")