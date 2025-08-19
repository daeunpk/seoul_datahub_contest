# minmax, 가중합, 소지수 계산 등
import pandas as pd

def minmax(series: pd.Series):
    mn, mx = series.min(), series.max()
    if pd.isna(mn) or pd.isna(mx) or mn == mx:
        return pd.Series(0, index=series.index)
    return (series - mn) / (mx - mn)

def weighted_index(df: pd.DataFrame, norm_cols: list[str], weights: dict[str, float]):
    """정규화된 컬럼(norm_cols)과 가중치(weights)로 종합지수 산출"""
    res = pd.Series(0, index=df.index, dtype=float)
    for col in norm_cols:
        w = weights.get(col, 1/len(norm_cols))
        res += df[col] * w
    return res
