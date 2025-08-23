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

try:
    df = pd.read_csv('./measure/NAT/data/중랑_중랑캠핑숲중랑가족캠핑장_reviews_dic_cleaned.csv')
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

vectorizer = CountVectorizer(
    tokenizer=custom_tokenizer,
    max_features=5000,
    min_df=1,   # 무조건 허용
    max_df=1.0  # 무조건 허용
)

model = BERTopic(
    embedding_model="sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens",
    vectorizer_model=vectorizer,
    nr_topics='auto',  # 토픽 개수는 50개로 시작, 나중에 'auto'로 변경 가능
    top_n_words=10,
    calculate_probabilities=True,
    verbose=True
)

if docs:
    print("샘플 토큰 확인:", [custom_tokenizer(docs[i]) for i in range(min(5, len(docs)))])
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
