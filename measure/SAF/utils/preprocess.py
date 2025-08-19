# 구 표준화, 주소 파싱 등
import re
import pandas as pd

def extract_gu_from_address(addr: str):
    if not isinstance(addr, str):
        return None
    m = re.search(r'([가-힣]+구)', addr)
    return m.group(1) if m else None

def standardize_gu(df: pd.DataFrame) -> pd.DataFrame:
    if '시군구명' in df.columns:
        df = df.rename(columns={'시군구명':'구'})
    elif '도로명주소' in df.columns:
        df['구'] = df['도로명주소'].apply(extract_gu_from_address)
    elif '지번주소' in df.columns:
        df['구'] = df['지번주소'].apply(extract_gu_from_address)
    elif '상세주소' in df.columns:
        df['구'] = df['상세주소'].apply(extract_gu_from_address)
    else:
        raise KeyError("구 정보 컬럼을 찾을 수 없습니다.")
    df['구'] = df['구'].astype(str).str.strip()
    return df[df['구'].notna()].copy()
