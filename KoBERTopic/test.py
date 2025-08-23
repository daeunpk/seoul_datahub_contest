from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer
from konlpy.tag import Mecab
from bertopic import BERTopic
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
    "은데", "아주"
}

# 3. 도메인 불용어 (리뷰마다 반복되는 단어)
domain_stopwords = {"한강","공원","서울"}

# 4. 최종 불용어 집합
stopwords_ko = stopwords_ko.union(extra_stopwords).union(domain_stopwords)


# --- 토크나이저 ---
class CustomTokenizer:
    def __init__(self, tagger, stopwords):
        self.tagger = tagger
        self.stopwords = stopwords
    def __call__(self, sent):
        tokens = []
        for word, pos in self.tagger.pos(sent):
            if pos in self.allowed_pos and word not in self.stopwords and len(word) > 1:
                tokens.append(word)
        return tokens
    

mecab = Mecab()
custom_tokenizer = CustomTokenizer(mecab, stopwords=stopwords_ko)

vectorizer = CountVectorizer(tokenizer=custom_tokenizer,
                             max_features=5000,
                             min_df=5,
                             max_df=0.5)

model = BERTopic(
    embedding_model="sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens",
    vectorizer_model=vectorizer,
    nr_topics=50,  # 토픽 개수는 50개로 시작, 나중에 'auto'로 변경 가능
    top_n_words=10,
    calculate_probabilities=True,
    verbose=True
)

# 1. CSV 파일에서 리뷰 데이터 불러오기

try:
    df = pd.read_csv('../measure/NAT/data/강남_율현공원_reviews_dic_cleaned.csv')
    df.dropna(subset=['내용'], inplace=True)
    docs = df['내용'].astype(str).tolist()
    print(f"데이터 로드 완료: 총 {len(docs)}개의 리뷰를 분석합니다.")
except FileNotFoundError:
    print("오류: 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
    docs = []

# # 데이터 폴더 경로
# data_dir = "../measure/NAT/data/"

# # CSV 파일 모으기
# all_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")]

# # 모든 파일 읽어서 하나의 DataFrame으로 합치기
# df_list = []
# for file in all_files:
#     try:
#         tmp = pd.read_csv(file)
#         if "내용" in tmp.columns:
#             tmp.dropna(subset=['내용'], inplace=True)
#             df_list.append(tmp[['내용']])  # '내용' 컬럼만 가져오기
#     except Exception as e:
#         print(f"⚠️ {file} 읽기 실패: {e}")

# # 전체 데이터 합치기
# if df_list:
#     df = pd.concat(df_list, ignore_index=True)
#     docs = df['내용'].astype(str).tolist()
#     print(f"총 {len(docs)}개의 리뷰를 분석합니다. ({len(all_files)}개 CSV 파일 합침)")
# else:
#     docs = []
#     print("CSV 파일에서 데이터를 불러오지 못했습니다.")

if docs:
    # 2. BERTopic 모델 학습 및 토픽 추출 실행
    topics, probs = model.fit_transform(docs)

    # 3. 결과 확인: 생성된 토픽 정보 전체 출력
    print("\n" + "="*80)
    print("BERTopic 모델링 결과: 토픽 정보")
    print("="*80)
    topic_info = model.get_topic_info()
    print(topic_info)
    
    # 4. 결과 확인: 각 토픽별 키워드 확인
    unique_topics = sorted(list(set(topics)))
    print("\n" + "="*80)
    print("각 토픽별 상위 키워드")
    print("="*80)
    for topic_num in unique_topics:
        if topic_num != -1:  # -1번 토픽(노이즈)은 제외
            keywords = model.get_topic(topic_num)
            print(f"Topic {topic_num}: {[word for word, prob in keywords]}")
