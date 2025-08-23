# 한강 공원 안전성 점수 계산
import pandas as pd
import io

# 1. 자치구별 안전성 점수 데이터 불러오기
safety_data = pd.read_csv('measure/SAF/result/safety_total_score.csv').to_csv(index=False)
saf_df = pd.read_csv(io.StringIO(safety_data))

# '자치구'를 인덱스로 설정하면 점수를 쉽게 찾아올 수 있습니다.
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
    '여의도한강공원' : ['영등포구']
}

# 3. 공원별 안전성 점수 계산
park_safety_scores = []

for park, districts in han_parks.items():
    scores = []
    # 공원에 속한 자치구들의 safety_score를 가져옵니다.
    for district in districts:
        try:
            # .loc를 사용해 해당 자치구의 safety_score를 찾습니다.
            score = saf_df.loc[district, 'safety_score']
            scores.append(score)
        except KeyError:
            print(f"경고: '{district}'의 안전성 점수 데이터를 찾을 수 없습니다. 계산에서 제외됩니다.")
    
    # 점수 리스트의 평균을 계산합니다.
    if scores:
        average_score = sum(scores) / len(scores)
    else:
        average_score = 0  # 해당 자치구의 점수가 하나도 없는 경우
        
    park_safety_scores.append({
        '한강공원': park,
        '안전성_점수': average_score
    })

# 4. 결과를 DataFrame으로 변환하고 CSV로 저장
output_df = pd.DataFrame(park_safety_scores)
output_df = output_df.sort_values(by='안전성_점수', ascending=False) # 점수 순으로 정렬

output_filename = 'safety_hangang_total_score.csv'
output_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"'{output_filename}' 파일로 저장이 완료되었습니다.")
print("\n--- 결과 미리보기 ---")
print(output_df)