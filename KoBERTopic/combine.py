# _summary_topics.csv 파일들을 하나로 합치는 스크립트
import os
import pandas as pd
from tqdm import tqdm

# 결과 파일들이 저장된 폴더 경로
results_dir = "./bertopic_results/"
# 최종 저장될 파일 이름
output_filename = "combine_topic_summary.csv"

# 1. 폴더 내의 모든 _topic_summary.csv 파일 이름 찾기
try:
    all_summary_files = [f for f in os.listdir(results_dir) if f.endswith("_topic_summary.csv")]
    if not all_summary_files:
        print(f"오류: '{results_dir}' 폴더에서 '_topic_summary.csv' 파일을 찾을 수 없습니다.")
    else:
        print(f"총 {len(all_summary_files)}개의 topic_summary 파일을 통합합니다.")
except FileNotFoundError:
    print(f"오류: '{results_dir}' 폴더를 찾을 수 없습니다. 경로를 확인해주세요.")
    all_summary_files = []

# 2. 각 파일을 읽어와 리스트에 데이터프레임으로 저장
list_of_dataframes = []
if all_summary_files:
    for filename in tqdm(all_summary_files, desc="파일 통합 진행률"):
        try:
            # 2-1. 파일명에서 공원 이름 추출
            # 예: "중랑캠핑숲_topic_summary.csv" -> "중랑캠핑숲"
            park_name = filename.replace("_topic_summary.csv", "")
            
            # 2-2. 파일 전체 경로 생성
            file_path = os.path.join(results_dir, filename)
            
            # 2-3. CSV 파일 읽기
            df = pd.read_csv(file_path)
            
            # 2-4. 'Park_nm' 컬럼 추가하고 맨 앞에 위치시키기
            df['Park_nm'] = park_name
            
            # 2-5. 리스트에 추가
            list_of_dataframes.append(df)
            
        except Exception as e:
            print(f"오류: '{filename}' 파일을 처리하는 중 문제가 발생했습니다: {e}")

# 3. 모든 데이터프레임을 하나로 합치기
if list_of_dataframes:
    # pd.concat으로 모든 데이터프레임을 수직으로 쌓음
    combined_df = pd.concat(list_of_dataframes, ignore_index=True)
    
    # Park_nm 컬럼을 가장 앞으로 이동 (가독성 향상)
    cols = ['Park_nm'] + [col for col in combined_df.columns if col != 'Park_nm']
    combined_df = combined_df[cols]

    # 4. 최종 결과를 하나의 CSV 파일로 저장
    try:
        # 엑셀에서 한글이 깨지지 않도록 'utf-8-sig' 인코딩 사용
        combined_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n✅ 성공! 모든 파일이 '{output_filename}'으로 통합 저장되었습니다.")
        
        # 결과 미리보기
        print("\n--- 결과 미리보기 (상위 5개 행) ---")
        print(combined_df.head())
        
    except Exception as e:
        print(f"오류: 최종 파일을 저장하는 중 문제가 발생했습니다: {e}")
else:
    print("통합할 데이터가 없습니다.")