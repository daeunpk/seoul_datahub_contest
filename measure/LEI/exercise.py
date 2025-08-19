## 한강공원 운동시설 여가도
import pandas as pd
import numpy as np
import json

# 분석할 운동시설 종류 9개로 정의
TARGET_LABELS = {
    "운동시설", "야구장", "론볼링장", "트랙구장", "롤러장",
    "자전거공원", "수영장/물놀이장", "강변물놀이장", "골프장"
}

input_filename = 'measure/LEI/data/monthly_hanriver.csv'

try:
    # 2. JSON 파일 읽기 및 데이터 구조화
    with open(input_filename, 'r', encoding='utf-8') as f:
        # f.readline() 대신 json.load(f)를 사용하여 파일 전체를 한 번에 읽어들이기
        data = json.load(f)

    # 시설 코드와 시설명을 매칭하는 딕셔너리 생성
    code_map = {k.lower(): v for k, v in data['DESCRIPTION'].items()}

    # 각 공원이 보유한 시설 목록을 담을 리스트
    facilities_list = []

    # 실제 데이터 부분(DATA)을 순회하며 공원별 시설을 추출
    for record in data['DATA']:
        park_name = record.get('park_nm')
        if not park_name:
            continue
        
        for code, value in record.items():
            if code.startswith('cnt') and isinstance(value, (int, float)) and value > 0:
                facility_name = code_map.get(code)
                if facility_name in TARGET_LABELS:
                    facilities_list.append({'공원명': park_name, '시설종류': facility_name})

    df_sports = pd.DataFrame(facilities_list)

    if df_sports.empty:
        print("분석 대상에 해당하는 운동시설 데이터를 찾을 수 없습니다.")
    else:
        # 3. 샤논 다양성 지수 계산 함수 정의
        def calculate_shannon_diversity(series):
            counts = series.value_counts()
            proportions = counts / counts.sum()
            shannon_index = -np.sum(proportions * np.log(proportions))
            return shannon_index

        # 4. 공원별 데이터 분석
        # 고유한 시설만 남겨서 공원별 보유 시설 목록을 만듭니다.
        df_unique_sports = df_sports.drop_duplicates()

        sport_analysis = df_unique_sports.groupby('공원명').agg(
            총_운동시설_수=('시설종류', 'count'),
            시설_다양성_지수=('시설종류', calculate_shannon_diversity)
        ).reset_index()

        # 5. 최종 '운동 여가도 점수' 산출
        sport_analysis['운동_여가도_점수'] = sport_analysis['총_운동시설_수'] * (1 + sport_analysis['시설_다양성_지수'])

        # 6. 결과 정렬 및 출력
        results_sorted = sport_analysis.sort_values(by='운동_여가도_점수', ascending=False).reset_index(drop=True)
        pd.options.display.float_format = '{:.2f}'.format

        print("--- 한강공원별 운동시설 여가도 분석 결과 ---")
        print(results_sorted)

        # 7. 결과 파일로 저장
        output_filename = 'hangang_sports_leisure_score.csv'
        results_sorted.to_csv(output_filename, encoding='utf-8-sig', index=False)
        print(f"\n✅ 운동 여가도 분석 결과가 '{output_filename}' 파일로 성공적으로 저장되었습니다.")


except FileNotFoundError:
    print(f"오류: '{input_filename}' 파일을 찾을 수 없습니다.")
except json.JSONDecodeError as e:
    print(f"JSON 파일 형식 오류: 파일 내용이 올바른 JSON 형식이 아닙니다. 오류: {e}")
except Exception as e:
    print(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")