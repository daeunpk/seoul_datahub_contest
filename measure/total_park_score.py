# 최종 공원 가중치 다르게 점수
import pandas as pd

# 1. 파일 경로 정의
# 실제 파일 이름이 다르다면 이 부분을 수정해주세요.
# 파일 이름은 사용자가 제공한 스니펫의 접두사를 기반으로 가정합니다.
lei_file = 'measure/LEI/results/gu_leisure_score.csv'
acc_file = 'measure/ACC/final_result/nonhangang_final.csv'
saf_file = 'measure/SAF/result/safety_total_score.csv'
# nat_file = 'measure/.csv'

try:
    # 2. 각 CSV 파일 불러오기
    lei_df = pd.read_csv(lei_file)
    acc_df = pd.read_csv(acc_file)
    saf_df = pd.read_csv(saf_file)

    # 3. 각 파일에서 필요한 컬럼만 선택 및 이름 변경
    lei_scores = lei_df[['자치구', '여가도_조정점수']].rename(columns={'여가도_조정점수': 'LEI_score'})
    acc_scores = acc_df[['구', '종합점수_100']].rename(columns={'구': '자치구', '종합점수_100': 'ACC_score'})
    saf_scores = saf_df[['자치구', 'safety_score']].rename(columns={'safety_score': 'SAF_score'})

    # 4. 3개의 데이터프레임을 '자치구' 기준으로 병합
    merged_df = pd.merge(lei_scores, acc_scores, on='자치구', how='outer')
    final_df = pd.merge(merged_df, saf_scores, on='자치구', how='outer')
    final_df.fillna(0, inplace=True)

    # 5. 가중치(LEI:ACC:SAF = 2:2:3)를 적용하여 '원본 총점' 계산
    weights = {'LEI': 2, 'ACC': 2, 'SAF': 3}
    final_df['원본_총점'] = (final_df['LEI_score'] * weights['LEI'] +
                              final_df['ACC_score'] * weights['ACC'] +
                              final_df['SAF_score'] * weights['SAF'])

    ### ★★★ 핵심 수정 부분: 100점 만점 기준으로 변환 ★★★
    # 6. Min-Max 정규화를 사용하여 100점 만점으로 변환
    raw_scores = final_df['원본_총점']
    min_score = raw_scores.min()
    max_score = raw_scores.max()

    # 분모가 0이 되는 경우(모든 점수가 동일한 경우)를 방지
    if (max_score - min_score) > 0:
        final_df['최종_점수(100점_환산)'] = ((raw_scores - min_score) / (max_score - min_score)) * 100
    else:
        # 모든 점수가 같다면 모두 100점으로 처리
        final_df['최종_점수(100점_환산)'] = 100

    # 7. '원본_총점'을 기준으로 Z-Score 계산
    mean_score = final_df['원본_총점'].mean()
    std_score = final_df['원본_총점'].std()
    
    # 표준편차가 0인 경우(모든 점수가 동일) Z-Score는 0
    if std_score > 0:
        final_df['Z-Score'] = (final_df['원본_총점'] - mean_score) / std_score
    else:
        final_df['Z-Score'] = 0
        
    # 7. 100점 만점 점수를 기준으로 내림차순 정렬
    final_df_sorted = final_df.sort_values(by='최종_점수(100점_환산)', ascending=False)
    
    # 8. 결과 출력 및 파일 저장
    # 최종 결과물로 '자치구'와 100점 만점 점수 컬럼만 선택
    output_df = final_df_sorted[['자치구', '최종_점수(100점_환산)', 'Z-Score']]
    
    # output_filename = '최종_지표합_점수(100점_만점).csv'
    # output_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

    print(f"\n\n{'='*50}")
    print("최종 지표합 점수 계산 및 100점 변환 완료!")
    # print(f"결과가 '{output_filename}' 파일로 저장되었습니다.")
    print("="*50)
    print(output_df)

except FileNotFoundError as e:
    print(f"오류: 파일을 찾을 수 없습니다. 파일 이름(LEI.csv, ACC.csv, SAF.csv)을 확인해주세요. -> {e}")
except KeyError as e:
    print(f"오류: CSV 파일에 필요한 컬럼 이름이 없습니다. 컬럼 이름을 확인해주세요. -> {e}")