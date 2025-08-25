import os
import pandas as pd
from transformers import pipeline
from tqdm import tqdm

import torch
from transformers import BertTokenizer, BertForSequenceClassification
import torch.nn.functional as F

# --- 1. 초기 설정 ---

# 🔽 1-1. 직접 확인하고 자연 관련 토픽만 남겨둔 통합 파일의 경로
MANUALLY_FILTERED_TOPICS_PATH = "./bertopic_results/combine_topic_summary_cleaned.csv" 

# 🔽 1-2. 공원별 문서-토픽 파일이 저장된 폴더 경로
DOCS_TOPICS_DIR = "./bertopic_results/"

# 🔽 1-3. 최종 결과가 저장될 파일 이름
FINAL_SCORE_OUTPUT_PATH = "감정분석_test.csv"

# --- 2. 감성 분석 모델 로딩 (시간이 걸리므로 맨 처음에 한 번만 실행) ---
print("감성 분석 모델을 로딩합니다... (시간이 소요될 수 있습니다)")
# GPU 사용 가능 시 device=0으로 설정하면 속도가 매우 빨라집니다. (없으면 device=-1 또는 생략)
sentiment_analyzer = pipeline('sentiment-analysis', model='kykim/bert-kor-base', device=-1)
print("✅ 모델 로딩 완료!")


# --- 3. 분석 시작 ---

try:
    # 3-1. 수동으로 필터링한 '자연 관련' 토픽 목록 불러오기
    approved_topics_df = pd.read_csv(MANUALLY_FILTERED_TOPICS_PATH)
    # 혹시 모를 -1 토픽(노이즈)은 코드 상에서 한 번 더 제외
    approved_topics_df = approved_topics_df[approved_topics_df['Topic'] != -1]
    print(f"\n✅ '{MANUALLY_FILTERED_TOPICS_PATH}' 파일에서 {len(approved_topics_df)}개의 자연 관련 토픽을 불러왔습니다.")

except FileNotFoundError:
    print(f"❌ 오류: '{MANUALLY_FILTERED_TOPICS_PATH}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
    approved_topics_df = pd.DataFrame() # 빈 데이터프레임으로 초기화

# 3-2. 공원별 문서-토픽 파일 목록 가져오기
try:
    doc_topic_files = [f for f in os.listdir(DOCS_TOPICS_DIR) if f.endswith("_document_topics.csv")]
    print(f"✅ '{DOCS_TOPICS_DIR}' 폴더에서 {len(doc_topic_files)}개의 공원 리뷰 파일을 찾았습니다.")
except FileNotFoundError:
    print(f"❌ 오류: '{DOCS_TOPICS_DIR}' 폴더를 찾을 수 없습니다. 경로를 확인해주세요.")
    doc_topic_files = []

# --- 4. 공원별 점수 계산 루프 ---

final_park_scores = {}

if not approved_topics_df.empty and doc_topic_files:
    for filename in tqdm(doc_topic_files, desc="공원별 감성 점수 계산 중"):
        
        # 4-1. 파일명에서 공원 이름 추출
        park_name = filename.replace("_document_topics.csv", "")
        
        # 4-2. 해당 공원의 '자연 관련' 토픽 ID 목록만 가져오기
        approved_ids_for_park = approved_topics_df[approved_topics_df['Park_nm'] == park_name]['Topic'].tolist()
        
        if not approved_ids_for_park:
            # print(f"INFO: '{park_name}'에 해당하는 자연 관련 토픽이 없습니다. 건너뜁니다.")
            continue

        # 4-3. 해당 공원의 전체 리뷰 파일 불러오기
        file_path = os.path.join(DOCS_TOPICS_DIR, filename)
        park_reviews_df = pd.read_csv(file_path)
        
        # 4-4. '자연 관련' 토픽에 해당하는 리뷰만 필터링
        eco_reviews_df = park_reviews_df[park_reviews_df['Topic_ID'].isin(approved_ids_for_park)]
        
        if eco_reviews_df.empty:
            # print(f"INFO: '{park_name}'에 자연 관련 리뷰가 없습니다. 건너뜁니다.")
            continue
            
        # 4-5. 필터링된 리뷰들에 대해 감성 분석 수행
        reviews_to_analyze = eco_reviews_df['Review'].dropna().astype(str).tolist()
        if not reviews_to_analyze:
            continue
            
        sentiment_results = sentiment_analyzer(reviews_to_analyze)
        
        # 4-6. 감성 분석 결과를 점수로 변환 (긍정=1, 부정=-1)
        scores = []
        for result in sentiment_results:
            if result['label'] == 'positive':
                scores.append(1)
            elif result['label'] == 'negative':
                scores.append(-1)
            # beomi/kcbert-base-finetune-nsmc 모델은 중립(neutral)을 반환하지 않습니다.
        
        # 4-7. 공원의 최종 '생태경관성 점수' 계산
        if scores:
            final_score = sum(scores) / len(scores)
            final_park_scores[park_name] = {
                'Ecological_Scenic_Score': final_score,
                'Analyzed_Review_Count': len(scores)
            }

# --- 5. 최종 결과 정리 및 저장 ---

if final_park_scores:
    # 딕셔너리를 데이터프레임으로 변환
    final_scores_df = pd.DataFrame.from_dict(final_park_scores, orient='index')
    final_scores_df.index.name = 'Park_nm'
    final_scores_df.reset_index(inplace=True)
    
    # 점수가 높은 순으로 정렬
    final_scores_df_sorted = final_scores_df.sort_values(by='Ecological_Scenic_Score', ascending=False)
    
    print("\n" + "="*80)
    print("      🌳 최종 공원별 생태경관성 점수 순위 🌳")
    print("="*80)
    print(final_scores_df_sorted.to_string(index=False))
    
    # 최종 결과를 CSV 파일로 저장
    final_scores_df_sorted.to_csv(FINAL_SCORE_OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n✅ 최종 결과가 '{FINAL_SCORE_OUTPUT_PATH}' 파일로 저장되었습니다.")
else:
    print("\n분석할 데이터가 없어 점수를 계산하지 못했습니다. 파일 경로와 내용을 확인해주세요.")