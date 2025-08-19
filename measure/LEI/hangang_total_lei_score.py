import pandas as pd

try:
    # 1. 두 개의 분석 결과 파일 불러오기
    df_festival = pd.read_csv('measure/LEI/results/hangang_park_leisure_score.csv')
    df_sports = pd.read_csv('measure/LEI/results/hangang_sports_leisure_score.csv')

    # 2. '공원명'을 기준으로 두 데이터프레임 병합
    # 한쪽에만 데이터가 있는 공원도 포함하기 위해 'outer' 방식으로 병합
    df_merged = pd.merge(df_festival[['공원명', '여가도_점수']],
                         df_sports[['공원명', '운동_여가도_점수']],
                         on='공원명', how='outer')

    # 병합 후 데이터가 없는(NaN) 부분은 0으로 채워 분석 오류 방지
    df_merged = df_merged.fillna(0)

    # 3. 각 점수 정규화 (Min-Max Scaling)
    # 축제 여가도 점수를 0~100점 척도로 변환
    min_fest = df_merged['여가도_점수'].min()
    max_fest = df_merged['여가도_점수'].max()
    df_merged['축제_정규화_점수'] = 100 * (df_merged['여가도_점수'] - min_fest) / (max_fest - min_fest)

    # 운동 여가도 점수를 0~100점 척도로 변환
    min_sport = df_merged['운동_여가도_점수'].min()
    max_sport = df_merged['운동_여가도_점수'].max()
    df_merged['운동_정규화_점수'] = 100 * (df_merged['운동_여가도_점수'] - min_sport) / (max_sport - min_sport)

    # 4. 최종 '종합 여가도 점수' 계산 (5:5 가중치)
    df_merged['종합_여가도_점수'] = (df_merged['축제_정규화_점수'] * 0.5) + (df_merged['운동_정규화_점수'] * 0.5)

    # 5. 결과 정렬 및 출력
    # 최종 결과에 필요한 컬럼만 선택
    final_results = df_merged[['공원명', '종합_여가도_점수', '축제_정규화_점수', '운동_정규화_점수']]
    results_sorted = final_results.sort_values(by='종합_여가도_점수', ascending=False).reset_index(drop=True)
    pd.options.display.float_format = '{:.2f}'.format
    
    print("--- 한강공원 종합 여가도 분석 결과 ---")
    print(results_sorted)
    
    # 6. 최종 결과 파일로 저장
    output_filename = 'hangang_total_leisure_score.csv'
    results_sorted.to_csv(output_filename, encoding='utf-8-sig', index=False)
    print(f"\n✅ 종합 분석 결과가 '{output_filename}' 파일로 성공적으로 저장되었습니다.")

except FileNotFoundError as e:
    print(f"오류: 필요한 CSV 파일을 찾을 수 없습니다. ({e.filename})")
except Exception as e:
    print(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")