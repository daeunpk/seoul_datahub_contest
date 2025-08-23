import os
import subprocess
import pandas as pd
from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer
from konlpy.tag import Mecab
from bertopic import BERTopic
import stopwordsiso as stopwords

# ✨ IMPROVEMENT: 모든 로직을 main 함수로 묶어 코드 구조 개선
def main():
    """
    메인 토픽 모델링 파이프라인을 실행하는 함수
    """
    # --- 1. 불용어 준비 ---
    print("1. 불용어 목록을 준비합니다...")
    stopwords_ko_base = stopwords.stopwords("ko")
    extra_stopwords = {
        "아요", "어요", "입니다", "예요", "네요", "같아요", "거에요", "거예요", "습니다",
        "그리고", "가장", "정말", "진짜", "너무", "는데", "어서", "다는", "이렇게",
        "여소", "달리", "^^", "~^^", "거나", "합니다", "로운", "끼리", "면서",
        "to", "1988", "88", "마다", "지요", "중국", "시킬", "아닌", "한때",
        "신영복", "든다", "원하", "비축", "기지", "마시", "면서", "방사장", "어서",
        "다면", "나갈", "터도", "이러", "군요", "아서", "01", "으러", "인데",
        "은데", "아주"
    }
    domain_stopwords = {"한강", "공원", "서울"}
    final_stopwords = stopwords_ko_base.union(extra_stopwords).union(domain_stopwords)
    print(f"   - 총 {len(final_stopwords)}개의 불용어를 사용합니다.")

    # --- 2. 토크나이저 및 벡터라이저 준비 ---
    print("2. 사용자 정의 토크나이저와 벡터라이저를 준비합니다...")

    # ✨ IMPROVEMENT: 하드코딩된 경로 대신 동적으로 경로 찾기
    try:
        mecab_path_process = subprocess.run(
            ["bash", "-c", "echo $(brew --prefix)/lib/mecab/dic/mecab-ko-dic"],
            capture_output=True, text=True, check=True
        )
        mecab_dic_path = mecab_path_process.stdout.strip()
        print(f"   - MeCab 사전 경로를 성공적으로 찾았습니다: {mecab_dic_path}")
    except Exception:
        print("   - ⚠️ MeCab 사전 경로를 자동으로 찾지 못했습니다. 수동 경로를 사용합니다.")
        mecab_dic_path = "/opt/homebrew/lib/mecab/dic/mecab-ko-dic" # Fallback 경로

    class CustomTokenizer:
        def __init__(self, tagger, stopwords):
            self.tagger = tagger
            self.stopwords = stopwords
            # 🐛 BUG FIX: 허용할 품사(POS) 리스트를 __init__에 정의
            # 명사(NNG, NNP), 동사(VV), 형용사(VA)를 주로 사용
            self.allowed_pos = {'NNG', 'NNP', 'VV', 'VA'}

        def __call__(self, text):
            tokens = []
            for word, pos in self.tagger.pos(text):
                # 길이가 1 이상이고, 허용된 품사이면서, 불용어가 아닌 단어만 추출
                if len(word) > 1 and pos in self.allowed_pos and word not in self.stopwords:
                    tokens.append(word)
            return tokens

    # 🐛 BUG FIX: 일부 불용어(extra_stopwords)가 아닌 전체 불용어(final_stopwords) 사용
    tokenizer = CustomTokenizer(Mecab(dicpath=mecab_dic_path), stopwords=final_stopwords)

    vectorizer = CountVectorizer(tokenizer=tokenizer,
                                 max_features=5000,
                                 min_df=5,
                                 max_df=0.5)

    # --- 3. BERTopic 모델 준비 ---
    print("3. BERTopic 모델을 초기화합니다...")
    model = BERTopic(
        embedding_model="sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens",
        vectorizer_model=vectorizer,
        nr_topics=50,
        top_n_words=10,
        calculate_probabilities=True,
        verbose=True
    )

    # --- 4. 데이터 로드 ---
    print("4. 리뷰 데이터를 로드합니다...")
    # ✨ IMPROVEMENT: 여러 CSV 파일을 읽는 로직을 함수로 분리 (주석 처리)
    # data_dir = "../measure/NAT/data/"
    # docs = load_all_reviews(data_dir)
    
    # 단일 파일 로드
    try:
        df = pd.read_csv('measure/NAT/data/강남_율현공원_reviews_dic_cleaned.csv')
        df.dropna(subset=['내용'], inplace=True)
        docs = df['내용'].astype(str).tolist()
        print(f"   - 데이터 로드 완료: 총 {len(docs)}개의 리뷰를 분석합니다.")
    except FileNotFoundError:
        print("   - ❌ 오류: 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        docs = []

    # --- 5. 모델 학습 및 결과 출력 ---
    if not docs:
        print("   - 분석할 데이터가 없습니다. 프로그램을 종료합니다.")
        return

    print("\n5. BERTopic 모델 학습을 시작합니다...")
    topics, probs = model.fit_transform(docs)

    print("\n" + "="*80)
    print("✅ BERTopic 모델링 결과: 토픽 정보")
    print("="*80)
    print(model.get_topic_info())

    print("\n" + "="*80)
    print("✅ 각 토픽별 상위 키워드")
    print("="*80)
    for topic_num in sorted(model.get_topics().keys()):
        if topic_num != -1:  # -1번 토픽(노이즈)은 제외
            keywords = [word for word, prob in model.get_topic(topic_num)]
            print(f"Topic {topic_num}: {keywords}")

def load_all_reviews(data_dir: str) -> list:
    """지정된 디렉토리의 모든 CSV 파일에서 '내용' 컬럼을 읽어 리스트로 반환합니다."""
    all_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")]
    df_list = []
    print(f"   - 총 {len(all_files)}개의 CSV 파일을 읽습니다...")
    for file in tqdm(all_files, desc="CSV 파일 로딩 중"):
        try:
            tmp = pd.read_csv(file)
            if "내용" in tmp.columns:
                tmp.dropna(subset=['내용'], inplace=True)
                df_list.append(tmp[['내용']])
        except Exception as e:
            print(f"   - ⚠️ {file} 읽기 실패: {e}")
    
    if not df_list:
        return []
    
    df = pd.concat(df_list, ignore_index=True)
    return df['내용'].astype(str).tolist()

if __name__ == "__main__":
    main()