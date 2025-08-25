import os
import pandas as pd
from collections import Counter
import ast  # 문자열을 파이썬 객체(리스트)로 안전하게 변환하기 위한 라이브러리

# 결과 파일들이 저장된 폴더 경로
results_dir = "./bertopic_results/"

# 1. 폴더 내의 모든 _topic_summary.csv 파일 경로 찾기
try:
    all_summary_files = [os.path.join(results_dir, f)
                         for f in os.listdir(results_dir)
                         if f.endswith("_topic_summary.csv")]
    if not all_summary_files:
        print(f"오류: '{results_dir}' 폴더에서 '_topic_summary.csv' 파일을 찾을 수 없습니다.")
    else:
        print(f"총 {len(all_summary_files)}개의 topic_summary 파일을 분석합니다.")
except FileNotFoundError:
    print(f"오류: '{results_dir}' 폴더를 찾을 수 없습니다. 경로를 확인해주세요.")
    all_summary_files = []

# 2. 모든 파일에서 키워드를 추출하여 하나의 리스트에 저장
all_keywords = []
for file_path in all_summary_files:
    try:
        df = pd.read_csv(file_path)
        
        # 'Representation' 컬럼이 없는 경우 건너뛰기
        if 'Representation' not in df.columns:
            continue
            
        # 결측값(NaN)이 있는 행은 제외
        df.dropna(subset=['Representation'], inplace=True)

        # Representation 컬럼의 각 행(문자열)을 실제 리스트로 변환하여 all_keywords에 추가
        for keyword_str in df['Representation']:
            try:
                # 예: "['산책', '나무']" -> ['산책', '나무']
                keyword_list = ast.literal_eval(keyword_str)
                if isinstance(keyword_list, list):
                    all_keywords.extend(keyword_list)
            except (ValueError, SyntaxError):
                # 문자열이 리스트 형태가 아닐 경우의 예외 처리
                # print(f"경고: '{keyword_str}'는 올바른 리스트 형식이 아닙니다. 건너뜁니다.")
                pass

    except Exception as e:
        print(f"오류: '{file_path}' 파일을 처리하는 중 문제가 발생했습니다: {e}")

# 3. 키워드 빈도수 계산
if all_keywords:
    keyword_counts = Counter(all_keywords)

    # 4. 빈도수 높은 순서로 정렬하여 데이터프레임으로 변환 후 출력
    print("\n" + "="*50)
    print("      전체 공원 토픽 키워드 빈도수 분석 결과")
    print("="*50)
    
    # 가장 흔한 50개 키워드를 데이터프레임으로 만듦
    counts_df = pd.DataFrame(keyword_counts.most_common(), columns=['Keyword', 'Frequency'])
    
    # to_string()을 사용하여 전체 출력을 깔끔하게 정렬
    print(counts_df.to_string(index=False))

else:
    print("\n분석할 키워드를 찾지 못했습니다. 파일 내용이나 경로를 확인해주세요.")