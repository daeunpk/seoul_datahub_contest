from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer
from konlpy.tag import Mecab
from bertopic import BERTopic
from gensim.models.coherencemodel import CoherenceModel
import pandas as pd
import stopwordsiso as stopwords
import os

print("현재 작업 디렉토리:", os.getcwd())

# 한국어 불용어 가져오기
stopwords_ko = stopwords.stopwords("ko")
# 도메인 특화 불용어 추가
# domain_stopwords = {"한강", "공원", "잠원", "서울", "강변", "자전거"}
# stopwords_ko = stopwords_ko.union(domain_stopwords)

class CustomTokenizer:
    def __init__(self, tagger, stopwords, allowed_pos=None):
        self.tagger = tagger
        self.stopwords = stopwords
        self.allowed_pos = allowed_pos if allowed_pos else ["NNG", "NNP", "VV", "VA"]

    def __call__(self, sent):
<<<<<<< HEAD
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
=======
        sent = sent[:1000000]
        word_tokens = self.tagger.morphs(sent)
        result = [word for word in word_tokens if len(word) > 1]
        return result

# 서버로 돌릴 때
# custom_tokenizer = CustomTokenizer(Mecab())
    
# 로컬에서 돌릴 떄: 경로 지정 (dicrc 파일이 들어있는 곳을 가리켜야 함)
mecab_path = "/opt/homebrew/Cellar/mecab-ko-dic/2.1.1-20180720/lib/mecab/dic/mecab-ko-dic"

custom_tokenizer = CustomTokenizer(Mecab(dicpath=mecab_path))

vectorizer = CountVectorizer(tokenizer=custom_tokenizer, max_features=3000)
>>>>>>> 1faec8cdb9895bcef56581e862e5dc0959c16250

model = BERTopic(embedding_model="sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens", \
                 vectorizer_model=vectorizer,
                 nr_topics=50, # 토픽 개수는 50개로 시작, 나중에 'auto'로 변경 가능
                 top_n_words=10,
                 calculate_probabilities=True,
                 verbose=True) # verbose=True 추가: 모델 학습 진행 상황을 볼 수 있어 유용

# 1. CSV 파일에서 리뷰 데이터 불러오기
try:
    df = pd.read_csv('../GoogleMap_Crawling/data/한강_잠원한강공원_reviews_dic.csv')
    # '내용' 컬럼에 비어있는 값(NaN)이 있으면 제거하고, 문자열로 변환
    df.dropna(subset=['내용'], inplace=True)
    docs = df['내용'].astype(str).tolist()
    print(f"데이터 로드 완료: 총 {len(docs)}개의 리뷰를 분석합니다.")

except FileNotFoundError:
    print("오류: '강서한강공원_reviews_dic.csv' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
    docs = []

if docs:
    # 2. BERTopic 모델 학습 및 토픽 추출 실행
    # 이 단계는 데이터 양에 따라 몇 분 정도 소요될 수 있습니다.
    topics, probs = model.fit_transform(docs)

    # 3. 결과 확인: 생성된 토픽 정보 전체 출력
    print("\n" + "="*80)
    print("BERTopic 모델링 결과: 토픽 정보")
    print("="*80)
    topic_info = model.get_topic_info()
    print(topic_info)
    
    # 1. docs 토큰화 결과 (Mecab 사용)
    tokenized_docs = [custom_tokenizer(doc) for doc in docs]

    # 2. BERTopic 토픽별 단어 추출
    topics = model.get_topics()
    topic_words = []
    for topic_num, words in topics.items():
        if topic_num != -1:  # 노이즈 제외
            topic_words.append([w for w, _ in words])

    # 3. Coherence 계산
    cm = CoherenceModel(
        topics=topic_words,
        texts=tokenized_docs,
        coherence='c_v'
    )
    coherence_score = cm.get_coherence()
    print("Topic Coherence Score:", coherence_score)
        
    # 원본 df 대신, 모델이 반환한 'topics' 변수에서 토픽 번호를 가져옵니다.
    unique_topics = sorted(list(set(topics)))

    # 4. 결과 확인: 각 토픽별 키워드 확인
    print("\n" + "="*80)
    print("각 토픽별 상위 키워드")
    print("="*80)
    for topic_num in unique_topics:
        if topic_num != -1:  # -1번 토픽(노이즈)은 제외
            # model.get_topic()을 사용하여 해당 토픽의 키워드를 가져옵니다.
            keywords = model.get_topic(topic_num)
            # 키워드(단어)만 예쁘게 출력
            print(f"Topic {topic_num}: {[word for word, prob in keywords]}")