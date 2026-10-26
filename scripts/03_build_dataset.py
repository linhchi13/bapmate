"""3단계: 내려받은 원본 데이터를 정제·결합해서 앱이 쓰는 data/restaurants.csv 를 만든다.

처리 순서
  1. 상가(상권)정보 읽기 → 음식점만 남기기(술집 제외)
  2. 학교와의 거리 계산(하버사인 공식) → 반경 안의 가게만 남기기
  3. 이름·주소 정규화, 중복 제거
  4. 업종 → 음식 종류(한식/분식/일식 …) 표준화, 구역(학교 앞/OO역 주변) 계산
  5. 착한가격업소 메뉴·가격 결합 (잘못된 가격은 버림)
  6. OpenStreetMap 영어 이름·영업시간 결합
  7. 팀이 직접 조사한 자료(data/manual/) 결합
  8. 품질 보고서(data/quality_report.json) 저장

실행:  python scripts/03_build_dataset.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import (  # noqa: E402
    CAMPUS_FRONT_M, CAMPUS_LAT, CAMPUS_LON, CUISINE_BY_MID, CUISINE_BY_SUB, EXCLUDED_MID,
    MANUAL_DIR, QUALITY_REPORT, RESTAURANTS_CSV, SEARCH_RADIUS_M, STATIONS, WALK_DETOUR, WALK_M_PER_MIN,
)

RAW_DIR = ROOT / "data" / "raw"
STORES_CSV = RAW_DIR / "stores_seoul.csv"
GOOD_PRICE_CSV = RAW_DIR / "good_price.csv"
OSM_JSON = RAW_DIR / "osm_food.json"

MAX_VALID_PRICE = 100_000  # 한 끼 메뉴 가격으로 이보다 크면 잘못된 값으로 본다
NON_FOOD_GOOD_PRICE = {"미용업", "이용업", "세탁업", "숙박업", "목욕업"}

report: dict = {"built_at": datetime.now().strftime("%Y-%m-%d %H:%M")}


# ---------------------------------------------------------------- 도우미 함수
def haversine_m(lat1, lon1, lat2, lon2):
    """두 좌표 사이의 직선거리(m). numpy 배열도 한 번에 계산된다."""
    r = 6_371_000
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2) - np.radians(lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def normalize_name(name) -> str:
    """비교용 이름: 공백·특수문자 제거, 소문자. 예) '사나이 뚝배기(과기대점)' → '사나이뚝배기과기대점'"""
    if not isinstance(name, str):
        return ""
    return re.sub(r"[^0-9a-z가-힣]", "", name.lower())


def road_name(address) -> str:
    """주소에서 도로명만 꺼냄. 예) '서울특별시 노원구 공릉로 227 (공릉동)' → '공릉로'"""
    if not isinstance(address, str):
        return ""
    address = re.sub(r"(로|길)\s+(\d+[가-힣]?길)", r"\1\2", address)  # '동일로 190길' → '동일로190길'
    m = re.search(r"([가-힣0-9]+(?:로|길))\s*\d", address)
    return m.group(1) if m else ""


def clean_price(value):
    """'7,000원' 같은 값을 숫자로. 숫자가 아니거나 범위를 벗어나면 NaN."""
    if pd.isna(value):
        return np.nan
    digits = re.sub(r"[^0-9.]", "", str(value))
    if not digits:
        return np.nan
    price = float(digits)
    if price <= 0 or price > MAX_VALID_PRICE:
        return np.nan
    return price


def find_store(stores: pd.DataFrame, name: str, address: str):
    """이름 + 도로명으로 상가정보의 가게를 찾는다. 확실히 하나로 정해질 때만 id를 돌려준다."""
    key = normalize_name(name)
    if len(key) < 2:
        return None
    same_name = stores[(stores["name_norm"] == key) | (stores["name_norm"].str.startswith(key) & (len(key) >= 3))]
    road = road_name(address)
    if road:
        same_name = same_name[same_name["road"] == road]
    return same_name["id"].iloc[0] if len(same_name) == 1 else None


# ---------------------------------------------------------------- 1~4. 상가정보
def load_stores() -> pd.DataFrame:
    if not STORES_CSV.exists():
        raise SystemExit(f"{STORES_CSV} 가 없습니다. 먼저 scripts/01_download_public_data.py 를 실행하세요.")
    cols = ["상가업소번호", "상호명", "지점명", "상권업종대분류명", "상권업종중분류명", "상권업종소분류명",
            "시군구명", "행정동명", "도로명주소", "건물명", "층정보", "경도", "위도"]
    df = pd.read_csv(STORES_CSV, usecols=cols, dtype=str, low_memory=False)
    report["raw_rows_seoul"] = len(df)

    # 1. 음식점만 (술집 제외)
    df = df[(df["상권업종대분류명"] == "음식") & (~df["상권업종중분류명"].isin(EXCLUDED_MID))].copy()
    report["food_rows_seoul"] = len(df)

    # 2. 좌표 숫자 변환 → 거리 계산 → 반경 안만
    df["lat"] = pd.to_numeric(df["위도"], errors="coerce")
    df["lon"] = pd.to_numeric(df["경도"], errors="coerce")
    report["missing_coordinates"] = int(df[["lat", "lon"]].isna().any(axis=1).sum())
    df = df.dropna(subset=["lat", "lon"])
    df["distance_m"] = haversine_m(CAMPUS_LAT, CAMPUS_LON, df["lat"], df["lon"]).round().astype(int)
    df = df[df["distance_m"] <= SEARCH_RADIUS_M].copy()
    report["within_radius"] = len(df)

    # 3. 정규화 + 중복 제거 (같은 이름 + 같은 도로명주소 = 같은 가게)
    df["상호명"] = df["상호명"].str.strip()
    df["지점명"] = df["지점명"].fillna("").str.strip()
    df["name"] = np.where(df["지점명"] != "", df["상호명"] + " " + df["지점명"], df["상호명"])
    df["name_norm"] = df["상호명"].map(normalize_name)
    before = len(df)
    df = df.drop_duplicates(subset=["name_norm", "도로명주소"])
    report["duplicates_removed"] = before - len(df)

    # 4. 음식 종류 표준화
    df["cuisine"] = df["상권업종소분류명"].map(CUISINE_BY_SUB).fillna(df["상권업종중분류명"].map(CUISINE_BY_MID)).fillna("etc")

    # 4. 구역: 학교 앞 / 가장 가까운 역
    station_names = list(STATIONS)
    dists = np.column_stack([haversine_m(df["lat"], df["lon"], la, lo) for la, lo in STATIONS.values()])
    nearest = np.array(station_names)[dists.argmin(axis=1)]
    df["area"] = np.where(df["distance_m"] <= CAMPUS_FRONT_M, "학교 앞", np.char.add(nearest.astype(str), " 주변"))
    df["walk_min"] = np.ceil(df["distance_m"] * WALK_DETOUR / WALK_M_PER_MIN).astype(int)

    df["address"] = df["도로명주소"].fillna("").str.strip()
    # 학교 주소(공릉로 232)를 쓰는 가게 = 캠퍼스 안의 식당·카페
    df.loc[df["address"].str.contains(r"공릉로\s*232$", regex=True), "area"] = "교내"
    floor = df["층정보"].fillna("").str.strip()
    df["building_floor"] = (df["건물명"].fillna("").str.strip() + " " + np.where(floor != "", floor + "층", "")).str.strip()
    df["road"] = df["address"].map(road_name)

    return df.rename(columns={
        "상가업소번호": "id", "상권업종중분류명": "category_mid", "상권업종소분류명": "category_sub",
        "시군구명": "district", "행정동명": "dong",
    })


# ---------------------------------------------------------------- 5. 착한가격업소
def attach_good_price(stores: pd.DataFrame, menus: list) -> set:
    if not GOOD_PRICE_CSV.exists():
        report["good_price"] = "파일 없음"
        return set()
    gp = pd.read_csv(GOOD_PRICE_CSV, encoding="utf-8-sig", dtype=str)
    gp = gp[(gp["시도"] == "서울특별시") & (gp["시군"].isin(stores["district"].unique()))]
    gp = gp[~gp["업종"].isin(NON_FOOD_GOOD_PRICE)]  # 미용실·세탁소 등은 제외
    matched, unmatched, invalid = set(), [], 0
    for _, row in gp.iterrows():
        sid = find_store(stores, row["업소명"], row["주소"])
        if sid is None:
            unmatched.append(row["업소명"])
            continue
        matched.add(sid)
        for i in range(1, 5):
            menu, raw_price = row.get(f"메뉴{i}"), row.get(f"가격{i}")
            if pd.isna(menu) and pd.isna(raw_price):
                continue
            price = clean_price(raw_price)
            if pd.isna(price) or pd.isna(menu):
                invalid += 1
                continue
            menus.append({"id": sid, "menu": str(menu).strip(), "price": price, "price_source": "착한가격업소(행정안전부)"})
    report["good_price"] = {"rows_in_districts": len(gp), "matched": len(matched),
                            "unmatched": unmatched, "invalid_or_empty_prices": invalid}
    return matched


# ---------------------------------------------------------------- 6. OpenStreetMap
def attach_osm(stores: pd.DataFrame) -> pd.DataFrame:
    stores["name_en"] = pd.NA
    stores["open_hours"] = pd.NA
    stores["hours_source"] = pd.NA
    if not OSM_JSON.exists():
        report["osm"] = "파일 없음"
        return stores
    elements = json.loads(OSM_JSON.read_text(encoding="utf-8"))
    matched = 0
    for e in elements:
        tags = e.get("tags", {})
        name = tags.get("name:ko") or tags.get("name")
        lat = e.get("lat", e.get("center", {}).get("lat"))
        lon = e.get("lon", e.get("center", {}).get("lon"))
        key = normalize_name(name)
        if not key or lat is None:
            continue
        cand = stores[(stores["name_norm"] == key) | stores["name_norm"].str.startswith(key)]
        if cand.empty:
            continue
        d = haversine_m(lat, lon, cand["lat"], cand["lon"])
        cand = cand[d <= 150]  # 150m 안에 있을 때만 같은 가게로 본다
        if len(cand) != 1:
            continue
        idx = cand.index[0]
        matched += 1
        if tags.get("name:en"):
            stores.loc[idx, "name_en"] = tags["name:en"]
        if tags.get("opening_hours"):
            stores.loc[idx, "open_hours"] = tags["opening_hours"]
            stores.loc[idx, "hours_source"] = "OpenStreetMap"
    report["osm"] = {"elements": len(elements), "matched": matched}
    return stores


# ---------------------------------------------------------------- 7. 팀 현장 조사
def attach_manual(stores: pd.DataFrame, menus: list) -> pd.DataFrame:
    """data/manual/ 의 직접 조사 자료가 있으면 공공데이터보다 우선 적용한다."""
    stores["image_path"] = pd.NA
    stores["checked_date"] = pd.NA
    info_csv, price_csv = MANUAL_DIR / "store_info.csv", MANUAL_DIR / "menu_prices.csv"
    n_info = n_price = 0
    if info_csv.exists():
        info = pd.read_csv(info_csv, dtype=str).dropna(subset=["store_id"])
        for _, r in info.iterrows():
            mask = stores["id"] == r["store_id"]
            if not mask.any():
                continue
            n_info += 1
            for col in ("name_en", "open_hours", "image_path", "checked_date"):
                if pd.notna(r.get(col)):
                    stores.loc[mask, col] = r[col]
            if pd.notna(r.get("open_hours")):
                stores.loc[mask, "hours_source"] = "현장 조사"
    if price_csv.exists():
        mp = pd.read_csv(price_csv, dtype=str).dropna(subset=["store_id", "menu"])
        surveyed = set()
        for _, r in mp.iterrows():
            price = clean_price(r.get("price"))
            if r["store_id"] not in set(stores["id"]) or pd.isna(price):
                continue
            surveyed.add(r["store_id"])
            menus.append({"id": r["store_id"], "menu": r["menu"].strip(), "price": price,
                          "price_source": f"현장 조사({r.get('checked_date', '')})"})
            n_price += 1
        # 현장 조사한 가게는 공공데이터 가격보다 현장 가격을 쓴다
        menus[:] = [m for m in menus if m["id"] not in surveyed or m["price_source"].startswith("현장")]
    report["manual"] = {"store_info_rows": n_info, "menu_price_rows": n_price}
    return stores


# ---------------------------------------------------------------- 실행
def main() -> None:
    stores = load_stores()
    menus: list = []
    good_ids = attach_good_price(stores, menus)
    stores["good_price"] = stores["id"].isin(good_ids)
    stores = attach_osm(stores)
    stores = attach_manual(stores, menus)

    # 메뉴 표 → 가게별 가격 요약
    menu_df = pd.DataFrame(menus, columns=["id", "menu", "price", "price_source"])
    if not menu_df.empty:
        summary = menu_df.groupby("id").agg(
            price_min=("price", "min"),
            price_max=("price", "max"),
            signature_menu=("menu", "first"),
            signature_price=("price", "first"),
            menus=("menu", lambda s: ";".join(f"{m}:{int(p)}" for m, p in zip(s, menu_df.loc[s.index, "price"]))),
            price_source=("price_source", "first"),
        ).reset_index()
        stores = stores.merge(summary, on="id", how="left")
    else:
        for col in ("price_min", "price_max", "signature_menu", "signature_price", "menus", "price_source"):
            stores[col] = pd.NA

    stores["source"] = "소상공인시장진흥공단_상가(상권)정보"
    stores["data_date"] = "2026-06-30"
    stores["collected_at"] = datetime.now().strftime("%Y-%m-%d")

    cols = ["id", "name", "name_en", "cuisine", "category_mid", "category_sub", "district", "dong", "area",
            "address", "building_floor", "lat", "lon", "distance_m", "walk_min",
            "good_price", "price_min", "price_max", "signature_menu", "signature_price", "menus", "price_source",
            "open_hours", "hours_source", "image_path", "checked_date", "source", "data_date", "collected_at"]
    out = stores[cols].sort_values("distance_m")
    RESTAURANTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(RESTAURANTS_CSV, index=False, encoding="utf-8-sig")

    report["output_rows"] = len(out)
    report["by_cuisine"] = out["cuisine"].value_counts().to_dict()
    report["missing_values"] = {c: int(out[c].isna().sum()) for c in ["name_en", "price_min", "open_hours", "image_path"]}
    QUALITY_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n저장 완료 → {RESTAURANTS_CSV.relative_to(ROOT)} ({len(out)}곳)")


if __name__ == "__main__":
    main()
