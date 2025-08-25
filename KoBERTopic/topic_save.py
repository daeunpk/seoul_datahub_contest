## 환경설정 이슈...
## 
from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer
from konlpy.tag import Mecab
from bertopic import BERTopic
from umap import UMAP
import pandas as pd
import stopwordsiso as stopwords  # ✅ 불용어 패키지
import os

# 1. 한국어 불용어 불러오기
stopwords_ko = stopwords.stopwords("ko")

# 2. 추가 불용어 (존댓말, 의미 없는 단어 등)
extra_stopwords = {
    "아요", "어요","입니다","예요","네요","같아요","거에요","거예요","습니다",
    "그리고","가장","정말","진짜","너무", "는데", "어서", "다는", "이렇게",
    "여소", "달리", "^^", "~^^", "거나", "합니다", "로운", "끼리", "면서",
    "to", "1988", "88", "마다", "지요", "중국", "시킬", "아닌", "한때",
    "신영복", "든다", "원하", "비축", "기지", "마시", "면서", "방사장", "어서",
    "다면", "나갈", "터도", "이러", "군요", "아서", "01", "으러", "인데",
    "은데", "아주", "데리", "나오", "", "정도", "요즘", "오랜만", "자체",
    "짱개", "듬뿍", "울산", "매우", "많이", "그렇", "가운데", "레이", "그냥", "슬슬",
    "직접", "활짝", "시작", "이파", "신발", "포원", "물끼", "무소", "메기", "접이식", "차시", "우동", "더불",
    "당시", "배우", "제일", "아직", "도중", "그리", "리모", "취하",
    '비올', '수많', '해치', '사울', '너무나', '중간', '가끔', '한눈',
    '그나마'
}

# 3. 도메인 불용어 (리뷰마다 반복되는 단어)
domain_stopwords = {"한강","공원", "서울", "서울시", "도산", "율현", "길동", "허브천문", "북서울꿈의숲", "방화", "서울식물원",
                    "우장산", "관악산", "서울대공원", "아차산", "어린이대공원", "고척", "푸른수목원", "금천체육공원", "금천폭포공원",
                    "불암산", "수락산", "서울창포원", "배봉산근린공원", "용두근린공원", "국립서울현충원", "보라매공원", "경의선숲길공원", "문화비축기지",
                    "서대문독립공원", "매헌시민의숲", "청계산매봉", "달맞이공원", "서울숲공원", "천장산", "석촌호수공원", "올림픽공원", "서서울호수공원",
                    "파리공원", "선유도공원", "여의도공원", "용산가족공원", "효창공원", "구파발폭포", "낙산공원", "인왕산", "남산공원",
                    "서울로7017", "사가정공원", "중랑캠핑숲", "중랑가족캠핑장", "강서한강공원", "광나루한강공원", "난지한강공원", "뚝섬한강공원", "망원한강공원",
                    "반포한강공원", "양화한강공원", "여의도한강공원", "이촌한강공원", "잠실한강공원", "잠원한강공원", "북한산국립공원", "북한산",
                    "구로구", "식생", "라떼", "더욱", "항동", "히기", "시대", "살짝", "고리", "수지"}

# 4. 최종 불용어 집합
stopwords_ko = stopwords_ko.union(extra_stopwords).union(domain_stopwords)


# --- 토크나이저 ---
class CustomTokenizer:
    def __init__(self, tagger, stopwords):
        self.tagger = tagger
        self.stopwords = stopwords
        # allowed_pos를 조금 넓혀봄 (형용사, 부사까지 추가 가능)
        self.allowed_pos = {"NNG", "NNP", "VV", "VA", "MAG"}  # 일반부사(MAG) 추가

    def __call__(self, sent):
        tokens = []
        for word, pos in self.tagger.pos(sent):
            if pos in self.allowed_pos and word not in self.stopwords and len(word) > 1:
                tokens.append(word)
        return tokens


mecab_path = "/opt/homebrew/Cellar/mecab-ko-dic/2.1.1-20180720/lib/mecab/dic/mecab-ko-dic"

custom_tokenizer = CustomTokenizer(Mecab(dicpath=mecab_path), stopwords=stopwords_ko)

# vectorizer = CountVectorizer(
#     tokenizer=custom_tokenizer,
#     max_features=5000,
#     min_df=2,
#     max_df=0.9
# )



# 1. CSV 파일에서 리뷰 데이터 불러오기
## 전체 파일 분석 돌리기
# # 1. 분석할 파일 목록 가져오기
# data_dir = "./measure/NAT/data/"
# output_dir = "./bertopic_results/"
# os.makedirs(output_dir, exist_ok=True) # 결과 저장 폴더 생성

# try:
#     all_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")]
#     print(f"총 {len(all_files)}개의 공원 데이터를 분석합니다.")
# except FileNotFoundError:
#     print(f"오류: '{data_dir}' 폴더를 찾을 수 없습니다. 경로를 확인해주세요.")
#     all_files = []


# # 2. 각 파일을 순회하며 개별적으로 분석 수행
# for file_path in tqdm(all_files, desc="전체 공원 분석 진행률"):
    
#     # 파일명에서 공원 이름 추출 (예: '중랑_중랑캠핑숲.csv' -> '중랑_중랑캠핑숲')
#     park_name = os.path.basename(file_path).replace('_reviews_dic_cleaned.csv', '')
    
#     print(f"\n{'='*25} {park_name} 분석 시작 {'='*25}")

#     # 3. 개별 공원 데이터 불러오기
#     try:
#         df = pd.read_csv(file_path)
#         df.dropna(subset=['내용'], inplace=True)
#         docs = df['내용'].astype(str).tolist()
        
#         # 리뷰 수가 너무 적으면 토픽 모델링이 의미 없으므로 건너뛰기
#         if len(docs) < 100:
#             print(f"⚠️ 리뷰 수가 100개 미만이므로 분석을 건너뜁니다. (리뷰 수: {len(docs)}개)")
#             continue
#         print(f"데이터 로드 완료: 총 {len(docs)}개 리뷰")

#     except Exception as e:
#         print(f"⚠️ 파일 읽기 실패: {e}")
#         continue # 다음 파일로 넘어감

#     # 4. BERTopic 모델 설정 (매번 새로운 모델로 분석)
#     #    - 모든 공원에 동일한 하이퍼파라미터를 적용하여 일관성 유지
#     vectorizer = CountVectorizer(tokenizer=custom_tokenizer, max_features=3000, min_df=2, max_df=0.85)
    
#     umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
#                       metric='cosine', random_state=42, n_jobs=1)
    
#     model = BERTopic(
#         embedding_model="sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens",
#         vectorizer_model=vectorizer,
#         umap_model=umap_model,
#         nr_topics='auto',
#         top_n_words=10,
#         calculate_probabilities=True,
#         verbose=False # 루프 안에서는 진행 로그를 끄는 것이 깔끔함
#     )

#     # 5. 모델 학습 및 토픽 추출 실행
#     try:
#         topics, probs = model.fit_transform(docs)
#         print("BERTopic 모델링 완료.")
#     except Exception as e:
#         print(f"⚠️ 모델 학습 중 오류 발생: {e}")
#         continue

#     # 6. 결과 저장 (이전 답변의 저장 로직 활용)
#     # 6-1. 토픽 요약 정보 저장
#     try:
#         topic_summary_df = model.get_topic_info()
#         summary_filepath = os.path.join(output_dir, f"{park_name}_topic_summary.csv")
#         topic_summary_df.to_csv(summary_filepath, index=False, encoding='utf-8-sig')
#         print(f"✅ 토픽 요약 정보 저장 완료: {summary_filepath}")
        
#         # 콘솔에도 간단히 결과 출력
#         print("\n[생성된 토픽 요약]")
#         print(topic_summary_df)

#     except Exception as e:
#         print(f"⚠️ 토픽 요약 정보 저장 실패: {e}")

#     # 6-2. 원본 리뷰 + 할당된 토픽 ID 저장
#     try:
#         doc_topic_df = pd.DataFrame({'Review': docs, 'Topic_ID': topics})
#         detailed_filepath = os.path.join(output_dir, f"{park_name}_document_topics.csv")
#         doc_topic_df.to_csv(detailed_filepath, index=False, encoding='utf-8-sig')
#         print(f"✅ 문서별 토픽 할당 결과 저장 완료: {detailed_filepath}")
#     except Exception as e:
#         print(f"⚠️ 문서별 토픽 할당 결과 저장 실패: {e}")
        
#     # 6-3. (선택) 학습된 모델 자체 저장
#     try:
#         model_filepath = os.path.join(output_dir, f"{park_name}.bertopic")
#         model.save(model_filepath, serialization="safetensors")
#         print(f"✅ BERTopic 모델 저장 완료: {model_filepath}")
#     except Exception as e:
#         print(f"⚠️ 모델 저장 실패: {e}")

# print(f"\n{'='*25} 모든 공원 분석 완료 {'='*25}")


# =================================================
# 1. 분석할 개별 파일 지정 및 폴더 생성
target_file_path = "./measure/NAT/data/한강_강서한강공원_reviews_dic_cleaned.csv"

output_dir = "./bertopic_results/"
os.makedirs(output_dir, exist_ok=True) # 결과 저장 폴더 생성


# 2. 파일 존재 여부 확인
if not os.path.exists(target_file_path):
    print(f"오류: '{target_file_path}' 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
else:
    # 파일명에서 공원 이름 추출
    park_name = os.path.basename(target_file_path).replace('_reviews_dic_cleaned.csv', '')
    
    print(f"\n{'='*25} {park_name} 분석 시작 {'='*25}")

    # 3. 개별 공원 데이터 불러오기
    try:
        df = pd.read_csv(target_file_path)
        df.dropna(subset=['내용'], inplace=True)
        docs = df['내용'].astype(str).tolist()
        
        # 리뷰 수가 너무 적으면 토픽 모델링이 의미 없으므로 실행 중단
        if len(docs) < 10:
            print(f"⚠️ 리뷰 수가 10개 미만으로 분석을 중단합니다. (리뷰 수: {len(docs)}개)")
        else:
            print(f"데이터 로드 완료: 총 {len(docs)}개 리뷰")

            # 4. BERTopic 모델 설정
            vectorizer = CountVectorizer(tokenizer=custom_tokenizer, max_features=3000, min_df=1, max_df=0.85)
            umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
                              metric='cosine', random_state=42, n_jobs=1)
            model = BERTopic(
                embedding_model="sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens",
                vectorizer_model=vectorizer,
                umap_model=umap_model,
                nr_topics='auto',
                top_n_words=10,
                calculate_probabilities=True,
                verbose=True # 단일 파일 분석 시에는 진행 과정을 보는 것이 좋음
            )

            # 5. 모델 학습 및 토픽 추출 실행
            topics, probs = model.fit_transform(docs)
            print("BERTopic 모델링 완료.")

            # 6. 결과 저장
            # 6-1. 토픽 요약 정보 저장
            topic_summary_df = model.get_topic_info()
            summary_filepath = os.path.join(output_dir, f"{park_name}_topic_summary.csv")
            topic_summary_df.to_csv(summary_filepath, index=False, encoding='utf-8-sig')
            print(f"✅ 토픽 요약 정보 저장 완료: {summary_filepath}")
            print("\n[생성된 토픽 요약]")
            print(topic_summary_df)

            # 6-2. 원본 리뷰 + 할당된 토픽 ID 저장
            doc_topic_df = pd.DataFrame({'Review': docs, 'Topic_ID': topics})
            detailed_filepath = os.path.join(output_dir, f"{park_name}_document_topics.csv")
            doc_topic_df.to_csv(detailed_filepath, index=False, encoding='utf-8-sig')
            print(f"✅ 문서별 토픽 할당 결과 저장 완료: {detailed_filepath}")
            
            # 6-3. (선택) 학습된 모델 자체 저장
            model_filepath = os.path.join(output_dir, f"{park_name}.bertopic")
            model.save(model_filepath, serialization="safensors")
            print(f"✅ BERTopic 모델 저장 완료: {model_filepath}")
            
            print(f"\n{'='*25} {park_name} 분석 완료 {'='*25}")

    except Exception as e:
        print(f"⚠️ 파일 처리 중 오류 발생: {e}")