import pandas as pd
from collections import Counter
import ast  # 문자열을 파이썬 리스트로 안전하게 변환

# 🔽 이전에 모든 topic_summary.csv를 합쳐서 저장한 파일 이름을 여기에 입력하세요.
combined_file_path = "./bertopic_results/combine_topic_summary.csv"

try:
    # 1. 통합된 CSV 파일을 데이터프레임으로 읽어오기
    df = pd.read_csv(combined_file_path)
    print(f"✅ '{combined_file_path}' 파일을 성공적으로 불러왔습니다.")

    # 2. Topic ID가 -1인 행(노이즈 토픽)을 먼저 제외
    df_filtered = df[df['Topic'] != -1].copy()
    print(f"노이즈 토픽(-1)을 제외하고 총 {len(df_filtered)}개의 유효 토픽을 분석합니다.")
    
    # 3. 필터링된 데이터에서 모든 키워드를 하나의 리스트로 추출
    all_keywords = []
    
    # 'Representation' 컬럼에 결측값이 있을 경우를 대비해 제거
    df_filtered.dropna(subset=['Representation'], inplace=True)
    
    for keyword_str in df_filtered['Representation']:
        try:
            # 문자열 "['단어1', '단어2']"를 실제 리스트 ['단어1', '단어2']로 변환
            keyword_list = ast.literal_eval(keyword_str)
            if isinstance(keyword_list, list):
                all_keywords.extend(keyword_list)
        except (ValueError, SyntaxError):
            # 변환 중 오류가 발생하면 건너뛰기
            pass

    # 4. 전체 키워드 리스트의 빈도수 계산
    if all_keywords:
        keyword_counts = Counter(all_keywords)
        
        # 5. 최종 결과를 데이터프레임으로 만들어 출력
        print("\n" + "="*50)
        print("    전체 공원 토픽 키워드 빈도수 분석 (노이즈 제외)")
        print("="*50)
        
        counts_df = pd.DataFrame(keyword_counts.most_common(), columns=['Keyword', 'Frequency'])
        
        print(counts_df.to_string(index=False))
        
    else:
        print("분석할 키워드를 찾지 못했습니다.")

except FileNotFoundError:
    print(f"❌ 오류: '{combined_file_path}' 파일을 찾을 수 없습니다. 파일 이름을 확인해주세요.")
except Exception as e:
    print(f"❌ 파일 처리 중 오류가 발생했습니다: {e}")