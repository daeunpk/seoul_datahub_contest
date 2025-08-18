## 한강공원 축제 목록을 CSV 파일로 저장하는 스크립트
import pandas as pd

# 1. 사용자가 제공한 축제 정보 딕셔너리
# 각 축제 이름을 key로, 개최되는 공원 목록을 value로 정의합니다.
festival_data = {
    "한강페스티벌 봄축제": "여의도한강공원, 잠실한강공원, 뚝섬한강공원",
    "한강 서래섬 유채꽃 축제": "반포한강공원",
    "한강 멍때리기 대회": "반포한강공원",
    "여의도 봄꽃축제": "여의도한강공원",
    "한강 수영장&물놀이장": "뚝섬한강공원, 여의도한강공원, 잠원한강공원, 난지한강공원, 양화한강공원, 잠실한강공원",
    "한강 종이비행기 축제": "여의도한강공원",
    "한강 서래섬 메밀꽃축제": "반포한강공원",
    "서울세계불꽃축제": "여의도한강공원",
    "한강페스티벌 겨울축제": "여의도한강공원",
    "로맨틱 한강 크리스마스 마켓": "여의도한강공원",
    "한강 눈썰매장": "뚝섬, 잠원, 여의도한강공원",
    "차없는 잠수교 뚜벅뚜벅 축제": "반포한강공원",
    "한강불빛공연 드론라이트쇼": "뚝섬한강공원",
    "한강야경투어": "반포한강공원, 여의도한강공원",
    "한강생태프로그램": "뚝섬한강공원, 잠원한강공원, 이촌한강공원, 난지한강공원, 강서한강공원",
    "한강공원 조각작품 순환 전시": "잠원한강공원, 여의도한강공원, 반포한강공원, 망원한강공원, 잠실한강공원, 양화한강공원, 난지한강공원, 이촌한강공원, 광나루한강공원, 강서한강공원",
    "여의도 물빛무대 문화프로그램 운영": "여의도한강공원",
    "광진교8번가 체험&전시&공연": "광나루한강공원"
}

# 2. 데이터를 CSV 형식에 맞게 가공
# 최종 데이터를 담을 리스트를 생성합니다.
processed_data = []

for festival, parks_str in festival_data.items():
    # 쉼표(,)를 기준으로 공원 이름을 분리합니다.
    parks = [p.strip() for p in parks_str.split(',')]

    for park in parks:
        # '한강공원'이라는 이름이 빠진 경우 추가하여 데이터 일관성을 유지합니다.
        # (단, '노들섬', '여의샛강' 같은 특수 지명은 제외)
        if '한강공원' not in park and '섬' not in park and '샛강' not in park:
            normalized_park = park + "한강공원"
        else:
            normalized_park = park
        
        # '축제명'과 '공원명'을 짝지어 리스트에 추가합니다.
        processed_data.append({'festival_nm': festival, 'park_nm': normalized_park})

# 3. Pandas 데이터프레임으로 변환
df_hangang = pd.DataFrame(processed_data)

# 4. CSV 파일로 저장
output_filename = 'hangang_festival_list.csv'
df_hangang.to_csv(output_filename, encoding='utf-8-sig', index=False)

print(f"✅ 한강공원 축제 목록이 '{output_filename}' 파일로 성공적으로 저장되었습니다.")
print("\n--- 생성된 데이터 샘플 ---")
print(df_hangang.head())