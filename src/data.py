"""데이터 읽기·검사·결합.

- restaurants.csv : 03_build_dataset.py 가 만든 가게 목록 (읽기 전용)
- 평가(reviews)   : 회원이 남긴 평가. src/storage.py 를 통해 CSV 또는 Google Sheets 에 저장
"""
import uuid

import numpy as np
import pandas as pd
import streamlit as st

from src.config import MIN_VOTES, MIN_YES_RATIO, RESTAURANTS_CSV
from src.storage import TABLES, append_row, now, read_table

MAX_VALID_PRICE = 100_000

# 이 열이 없으면 앱이 동작할 수 없다
REQUIRED_COLUMNS = ["id", "name", "cuisine", "address", "lat", "lon", "distance_m"]
# 이 열은 없어도 된다(없으면 빈 값으로 채움)
OPTIONAL_COLUMNS = ["name_en", "category_mid", "category_sub", "area", "building_floor", "walk_min",
                    "good_price", "price_min", "price_max", "signature_menu", "signature_price", "menus",
                    "price_source", "open_hours", "hours_source", "image_path", "source", "data_date"]
REVIEW_COLUMNS = TABLES["reviews"]


class DataError(Exception):
    """데이터 파일이 없거나 형식이 맞지 않을 때."""


def _clean_price(s: pd.Series) -> pd.Series:
    """숫자로 바꾸고, 0 이하이거나 너무 큰 값은 NaN(정보 없음)으로."""
    s = pd.to_numeric(s, errors="coerce")
    return s.where((s > 0) & (s <= MAX_VALID_PRICE))


def load_restaurants() -> pd.DataFrame:
    if not RESTAURANTS_CSV.exists():
        raise DataError("missing")
    # 파일 수정 시각을 함께 넘겨서, CSV가 새로 만들어지면 캐시도 자동으로 새로 읽는다
    return _read_restaurants(RESTAURANTS_CSV.stat().st_mtime)


@st.cache_data
def _read_restaurants(mtime: float) -> pd.DataFrame:  # mtime 은 캐시 구분용
    df = pd.read_csv(RESTAURANTS_CSV, dtype={"id": str})

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataError(", ".join(missing))
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    for col in ("lat", "lon", "distance_m", "walk_min"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["lat", "lon", "distance_m"])  # 위치를 모르면 보여 줄 수 없음
    df["walk_min"] = df["walk_min"].fillna(np.ceil(df["distance_m"] * 1.3 / 75))

    for col in ("price_min", "price_max", "signature_price"):
        df[col] = _clean_price(df[col])
    df["good_price"] = df["good_price"].astype(str).str.lower().isin(["true", "1", "yes"])
    df["area"] = df["area"].fillna("기타")
    df["name_en"] = df["name_en"].astype("string")
    return df.reset_index(drop=True)


def load_reviews() -> pd.DataFrame:
    """유효한 평가만. 같은 회원이 같은 가게를 여러 번 평가했으면 마지막 평가만 남긴다."""
    df = read_table("reviews").copy()
    df = df.drop_duplicates(["user_id", "store_id"], keep="last")
    df["stars"] = pd.to_numeric(df["stars"], errors="coerce")
    df = df[df["stars"].between(1, 5)]  # 잘못된 별점은 무시
    df["price_paid"] = _clean_price(df["price_paid"])
    return df


def save_review(user_id: str, store_id: str, stars: int, solo_ok: str, group_ok: str,
                price_paid, comment: str) -> None:
    append_row("reviews", {
        "review_id": uuid.uuid4().hex[:12],
        "user_id": user_id,
        "store_id": store_id,
        "stars": int(stars),
        "solo_ok": solo_ok,
        "group_ok": group_ok,
        "price_paid": "" if price_paid is None else int(price_paid),
        "comment": comment.strip()[:200],
        "created_at": now(),
    })


def aggregate_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    """가게별 평가 요약: 평균 별점, 평가 수, 혼밥/모임 찬성 수, 학생 제보 가격."""
    if reviews.empty:
        return pd.DataFrame(columns=["id", "rating_avg", "rating_count", "solo_yes", "solo_votes",
                                     "group_yes", "group_votes", "student_price", "student_price_n"])
    r = reviews.assign(
        solo_yes=(reviews["solo_ok"] == "yes").astype(int),
        solo_vote=reviews["solo_ok"].isin(["yes", "no"]).astype(int),
        group_yes=(reviews["group_ok"] == "yes").astype(int),
        group_vote=reviews["group_ok"].isin(["yes", "no"]).astype(int),
    )
    return r.groupby("store_id").agg(
        rating_avg=("stars", "mean"),
        rating_count=("stars", "count"),
        solo_yes=("solo_yes", "sum"),
        solo_votes=("solo_vote", "sum"),
        group_yes=("group_yes", "sum"),
        group_votes=("group_vote", "sum"),
        student_price=("price_paid", "median"),
        student_price_n=("price_paid", "count"),
    ).reset_index().rename(columns={"store_id": "id"})


def _verified(yes: pd.Series, votes: pd.Series) -> pd.Series:
    """응답이 MIN_VOTES 이상이고 찬성 비율이 MIN_YES_RATIO 이상일 때만 True."""
    return (votes >= MIN_VOTES) & (yes / votes.where(votes > 0) >= MIN_YES_RATIO)


def get_data() -> pd.DataFrame:
    """가게 목록 + 학생 평가 요약을 합친 표. 화면은 모두 이 표를 쓴다."""
    df = load_restaurants().merge(aggregate_reviews(load_reviews()), on="id", how="left")
    for col in ("rating_count", "solo_yes", "solo_votes", "group_yes", "group_votes", "student_price_n"):
        df[col] = df[col].fillna(0).astype(int)
    df["solo_verified"] = _verified(df["solo_yes"], df["solo_votes"])
    df["group_verified"] = _verified(df["group_yes"], df["group_votes"])

    # 예산 검색에 쓰는 가격: 공공데이터/현장조사 가격 → 없으면 학생 제보(2건 이상) 중앙값
    student_ok = df["student_price_n"] >= 2
    df["budget_price"] = df["price_min"].where(df["price_min"].notna(), df["student_price"].where(student_ok))
    df["budget_price_basis"] = np.select(
        [df["price_min"].notna(), student_ok],
        [df["price_source"].fillna(""), "학생 제보"],
        default="",
    )
    return df
