"""검색·필터·정렬 함수 (pandas)."""
import pandas as pd

from src.i18n import cuisine_label

SEARCH_COLUMNS = ["name", "name_en", "category_mid", "category_sub", "signature_menu", "menus", "address"]

# 유학생이 자주 쓰는 검색어 → 데이터에 있는 업종 이름 (둘 중 하나만 맞아도 검색됨)
SYNONYMS = {
    "쌀국수": "베트남", "pho": "베트남", "phở": "베트남", "vietnam": "베트남", "banhmi": "베트남",
    "sushi": "초밥", "스시": "초밥", "ramen": "라멘", "burger": "버거", "pizza": "피자",
    "chicken": "치킨", "coffee": "카페", "cafe": "카페", "noodle": "국수", "korean": "한식",
    "chinese": "중식", "japanese": "일식", "malatang": "마라", "tteokbokki": "떡볶이", "gimbap": "김밥",
}


def search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """가게 이름·영어 이름·업종·메뉴·주소 중 하나라도 검색어를 포함하면 결과에 넣는다.
    '한식', '분식' 같은 음식 종류 이름으로도 찾을 수 있다."""
    query = (query or "").strip().lower()
    if not query:
        return df
    words = query.split()
    text = df[SEARCH_COLUMNS].fillna("").astype(str).agg(" ".join, axis=1)
    text = (text + " " + df["cuisine"].map(cuisine_label)).str.lower()
    text_nospace = text.str.replace(" ", "", regex=False)
    mask = pd.Series(True, index=df.index)
    for w in words:  # 모든 단어가 들어 있어야 함 (띄어쓰기 차이는 무시)
        hit = text.str.contains(w, regex=False) | text_nospace.str.contains(w, regex=False)
        if w in SYNONYMS:
            hit |= text.str.contains(SYNONYMS[w], regex=False)
        mask &= hit
    return df[mask]


def apply_filters(df: pd.DataFrame, cuisines=None, area=None, max_walk=None,
                  include_cafe=True, only_priced=False, max_price=None) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if cuisines:
        mask &= df["cuisine"].isin(cuisines)
    elif not include_cafe:
        mask &= df["cuisine"] != "cafe"
    if area:
        mask &= df["area"] == area
    if max_walk:
        mask &= df["walk_min"] <= max_walk
    if only_priced:
        mask &= df["budget_price"].notna()
    if max_price is not None:
        mask &= df["budget_price"] <= max_price
    return df[mask]


def sort_df(df: pd.DataFrame, by: str) -> pd.DataFrame:
    if by == "price":
        return df.sort_values(["budget_price", "distance_m"], na_position="last")
    if by == "rating":
        return df.sort_values(["rating_avg", "rating_count", "distance_m"],
                              ascending=[False, False, True], na_position="last")
    if by == "name":
        return df.sort_values("name")
    return df.sort_values("distance_m")


def price_band(price, low: int, high: int) -> str | None:
    """가격 → 구간 이름(low/mid/high). 가격이 없으면 None."""
    if pd.isna(price):
        return None
    if price < low:
        return "low"
    if price <= high:
        return "mid"
    return "high"
