## 한강공원 종합 점수 계산
import numpy as np
import pandas as pd

# 1. 파일 경로 정의
# 실제 파일 이름이 다르다면 이 부분을 수정해주세요.
# 파일 이름은 사용자가 제공한 스니펫의 접두사를 기반으로 가정합니다.
lei_file = 'measure/LEI/results/hangang_total_leisure_score_adjusted.csv'
acc_file = 'measure/ACC/final_result/hangang_final.csv'
saf_file = 'measure/SAF/result/safety_hangang_total_score.csv'
nat_file = 'bertopic_results/sentiment/hangang_ranking_topic.csv'

try:
    # 2. 각 CSV 파일 불러오기
    lei_df = pd.read_csv(lei_file)
    acc_df = pd.read_csv(acc_file)
    saf_df = pd.read_csv(saf_file)
    nat_df = pd.read_csv(nat_file)

    # 3. 각 파일에서 필요한 컬럼만 선택 및 이름 변경
    lei_scores = lei_df[['공원명', '종합_여가도_점수']].rename(columns={'종합_여가도_점수': 'LEI_score'})
    acc_scores = acc_df[['공원명', '종합점수_100']].rename(columns={'종합점수_100': 'ACC_score'})
    saf_scores = saf_df[['한강공원', '안전성_점수']].rename(columns={'한강공원' : '공원명', '안전성_점수': 'SAF_score'})
    nat_scores = nat_df[['Park_nm', 'eco_score_std']].rename(columns={'Park_nm': '공원명', 'eco_score_std': 'NAT_score'})

    # 4. 3개의 데이터프레임을 '자치구' 기준으로 병합
    merged_df = pd.merge(lei_scores, acc_scores, on='공원명', how='outer')
    merged_df = pd.merge(merged_df, nat_scores, on='공원명', how='outer')
    final_df = pd.merge(merged_df, saf_scores, on='공원명', how='outer')
    final_df.fillna(0, inplace=True)

    # 5. 가중치(LEI:ACC:SAF = 2:2:3)를 적용하여 '원본 총점' 계산
    weights = {'LEI': 2, 'ACC': 2, 'SAF': 3, 'NAT': 3} 
    final_df['원본_총점'] = (final_df['LEI_score'] * weights['LEI'] +
                              final_df['ACC_score'] * weights['ACC'] +
                              final_df['SAF_score'] * weights['SAF'] +
                              final_df['NAT_score'] * weights['NAT'])

    # 방법 1: '이론상 최고점' 기준 점수
    theoretical_max_score = (100 * sum(weights.values()))
    final_df['Score_Theoretical'] = (final_df['원본_총점'] / theoretical_max_score) * 100
    
    # 방법 2: 'Z-Score 변환' 기준 점수
    mean_score = final_df['원본_총점'].mean()
    std_score = final_df['원본_총점'].std()
    if std_score > 0:
        final_df['Z-Score'] = (final_df['원본_총점'] - mean_score) / std_score
    else:
        final_df['Z-Score'] = 0
    
    def sigmoid(z):
        return 1 / (1 + np.exp(-z))
    final_df['Score_Z_Transformed'] = sigmoid(final_df['Z-Score']) * 100
        
    # 7. '이론상 최고점 기준 점수'로 정렬
    final_df_sorted = final_df.sort_values(by='Score_Theoretical', ascending=False)
    
    # 8. 결과 출력
    # Score_Theoretical: 이론상 최고점(100점) 대비 점수
    # Score_Z_Transformed: Z-Score를 시그모이드 함수로 변환한 점수
    # Z-Score: 원본 총점의 Z-Score
    output_df = final_df_sorted[['공원명', 'Score_Theoretical', 'Score_Z_Transformed', 'Z-Score']]
    
    output_filename = 'hangang_total_final.csv'
    output_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print(f"\n\n{'='*50}")
    print("최종 지표합 점수 계산 완료!")
    print("="*50)
    print(output_df.to_string(index=False))

except FileNotFoundError as e:
    print(f"오류: 파일을 찾을 수 없습니다. 경로를 확인해주세요. -> {e}")
except KeyError as e:
    print(f"오류: CSV 파일에 필요한 컬럼 이름이 없습니다. 컬럼 이름을 확인해주세요. -> {e}")