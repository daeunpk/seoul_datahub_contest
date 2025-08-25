# 한강 공원 안전성 점수 계산
import pandas as pd
import io

# 1. 자치구별 안전성 점수 데이터 불러오기
safety_data = pd.read_csv('measure/SAF/result/safety_total_score.csv').to_csv(index=False)
saf_df = pd.read_csv(io.StringIO(safety_data))

# '자치구'를 인덱스로 설정
saf_df.set_index('자치구', inplace=True)

# 2. 한강공원과 해당 자치구 목록 정의
han_parks = {
    '광나루한강공원': ['강동구', '송파구'],
    '잠실한강공원': ['송파구'],
    '뚝섬한강공원': ['광진구'],
    '잠원한강공원': ['강남구', '서초구'],
    '반포한강공원': ['서초구'],
    '이촌한강공원': ['용산구'],
    '망원한강공원': ['마포구'],
    '양화한강공원': ['영등포구'],
    '난지한강공원': ['마포구'],
    '강서한강공원': ['강서구'],
    '여의도한강공원': ['영등포구']
}

# 3. 계산할 점수 컬럼 목록
score_columns = ['safety_score', 'CRI_score', 'DRM_score', 'FIR_score', 'MED_score', 'RST_score', 'TRA_score']

# 4. 공원별 점수 계산
park_safety_scores = []

for park, districts in han_parks.items():
    park_scores = {'한강공원': park}
    
    for col in score_columns:
        scores = []
        for district in districts:
            try:
                score = saf_df.loc[district, col]
                scores.append(score)
            except KeyError:
                print(f"경고: '{district}'의 {col} 데이터를 찾을 수 없습니다. 계산에서 제외됩니다.")
        
        # 평균 점수 계산
        if scores:
            park_scores[col] = sum(scores) / len(scores)
        else:
            park_scores[col] = 0
    
    park_safety_scores.append(park_scores)

# 5. 결과를 DataFrame으로 변환하고 CSV로 저장
output_df = pd.DataFrame(park_safety_scores)
output_df = output_df.sort_values(by='safety_score', ascending=False) # 종합 점수 기준 정렬

output_filename = 'safety_hangang_total_score.csv'
output_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"'{output_filename}' 파일로 저장이 완료되었습니다.")
print("\n--- 결과 미리보기 ---")
print(output_df)
