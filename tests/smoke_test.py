"""자동 점검: 모든 페이지가 열리는지, 검색·필터·회원 기능(가입·즐겨찾기·평가·탈퇴)이 동작하는지 확인한다.

실행:  python tests/smoke_test.py
회원·평가 데이터는 임시 폴더(data/_test_storage)에 쓰고, 끝나면 지운다. 실제 데이터는 건드리지 않는다.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from src import config, storage  # noqa: E402
from src.filters import apply_filters, price_band, search  # noqa: E402

APP = str(ROOT / "app.py")
PAGES = ["views/home.py", "views/themes.py", "views/stats.py", "views/mypage.py", "views/about.py"]
failures = []

# 테스트용 임시 저장소로 바꿔치기
TMP = ROOT / "data" / "_test_storage"
shutil.rmtree(TMP, ignore_errors=True)
TMP.mkdir(parents=True)
storage.get_storage = lambda: storage.CsvStorage(TMP)
storage.read_table.clear()


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        failures.append(name)


def run_app():
    return AppTest.from_file(APP, default_timeout=60).run()


def button(at, label):
    return next(b for b in at.button if b.label == label)


try:
    # 1) 모든 페이지 열기 (로그인 안 한 상태)
    for page in PAGES:
        at = AppTest.from_file(APP, default_timeout=60)
        at.switch_page(page).run()
        check(f"page opens: {page}", not at.exception, [e.value for e in at.exception])

    # 2) 홈 검색
    at = run_app()
    at.text_input(key="home_q").input("국수").run()
    md = " ".join(m.value for m in at.markdown)
    check("search '국수' shows results", "곳**" in md and not at.exception)
    at.text_input(key="home_q").input("zzzz없는가게").run()
    md = " ".join(m.value for m in at.markdown)
    check("search no result shows empty state", "조건에 맞는 가게가 없어요" in md)
    at.text_input(key="home_q").input("").run()
    at.pills(key="home_budget").set_value("low").run()
    md = " ".join(m.value for m in at.markdown)
    from src.data import get_data as _gd  # noqa: E402
    _d = _gd()
    expected = int(((_d["budget_price"] <= 8000) & (_d["cuisine"] != "cafe")).sum())  # 홈은 기본으로 카페 제외
    check("home budget filter (8,000원 이하, 카페 제외)", f"**{expected}곳**" in md and not at.exception,
          [m.value for m in at.markdown if "곳**" in m.value])

    # 3) 필터 함수
    from src.data import _clean_price, get_data, load_reviews, save_review  # noqa: E402
    df = get_data()
    check("data has rows", len(df) > 0, f"{len(df)} rows")
    check("vietnamese filter", (apply_filters(df, cuisines=["vietnamese"])["cuisine"] == "vietnamese").all())
    cheap = apply_filters(df, max_price=8000)
    check("budget filter <= 8000", (cheap["budget_price"] <= 8000).all(), f"{len(cheap)} rows")
    check("search empty query returns all", len(search(df, "")) == len(df))
    check("synonym search 'pho' finds vietnamese", (search(df, "pho")["cuisine"] == "vietnamese").any())
    check("price_band", price_band(7000, 8000, 12000) == "low" and price_band(12000, 8000, 12000) == "mid"
          and price_band(float("nan"), 8000, 12000) is None)
    cleaned = _clean_price(pd.Series(["7000", "-5", "abc", "999999", None]))
    check("invalid prices become NaN", cleaned.notna().tolist() == [True, False, False, False, False])

    # 4) 회원 가입 흐름 (개발용 테스트 로그인)
    at = run_app()
    at.sidebar.text_input[0].input("tester")
    button(at, "테스트 로그인").click().run()
    check("after login, signup form shown", any("회원 가입" in m.value for m in at.markdown))
    at.text_input[0].input("공릉먹방러")
    at.checkbox[0].check()
    button(at, "가입하고 시작하기").click().run()
    members = storage.read_table("members")
    check("member saved", len(members) == 1 and members.iloc[0]["nickname"] == "공릉먹방러")
    check("sidebar greets member", any("공릉먹방러" in m.value for m in at.sidebar.markdown))

    # 5) 즐겨찾기 (홈 카드의 ♡ 저장 버튼)
    first_save = next(b for b in at.button if b.label == "♡ 저장")
    first_save.click().run()
    fav = storage.read_table("favorites")
    check("favorite saved", len(fav) == 1 and fav.iloc[0]["action"] == "add")
    at.switch_page("views/mypage.py").run()
    check("mypage favorites tab lists store", not at.exception and any(m.label == "즐겨찾기" and m.value == "1" for m in at.metric),
          [e.value for e in at.exception])

    # 6) 평가: 같은 회원이 같은 가게를 다시 평가하면 마지막 것만 반영
    uid = members.iloc[0]["user_id"]
    sid = df["id"].iloc[0]
    save_review(uid, sid, 2, "no", "no", None, "first")
    save_review(uid, sid, 5, "yes", "yes", 6000, "second")
    rv = load_reviews()
    check("one review per member per store", len(rv) == 1 and rv.iloc[0]["comment"] == "second")
    for i in range(2):
        save_review(f"other{i}", sid, 4, "yes", "no", 6000, "")
    row = get_data().set_index("id").loc[sid]
    check("review aggregate", row["rating_count"] == 3 and abs(row["rating_avg"] - 13 / 3) < 1e-9)
    check("solo verified after 3 yes votes", bool(row["solo_verified"]) and not bool(row["group_verified"]))

    # 7) 관리자 페이지: 현황 표시 + 후기 삭제
    at.switch_page("views/admin.py").run()
    check("admin page opens", not at.exception and any(m.label == "전체 회원" and m.value == "1" for m in at.metric),
          [e.value for e in at.exception])
    button(at, "삭제").click().run()
    check("admin deletes a review", len(load_reviews()) == 2)

    # 8) 마이페이지 → 탈퇴하면 이 회원의 기록이 모두 지워짐
    at.switch_page("views/mypage.py").run()
    check("mypage opens for member", not at.exception and any(m.value == "공릉먹방러" for m in at.metric))
    button(at, "네, 탈퇴할게요").click().run()
    left = [storage.read_table(tb) for tb in ("members", "favorites")]
    rv_left = storage.read_table("reviews")
    check("withdraw deletes member data", all(x.empty for x in left) and (rv_left["user_id"] != uid).all())

    # 8) 데이터 파일이 없을 때 안내 화면
    real_csv = config.RESTAURANTS_CSV
    backup = real_csv.with_suffix(".bak")
    real_csv.rename(backup)
    try:
        st.cache_data.clear()
        at = run_app()
        check("missing data file shows error", any("찾을 수 없어요" in e.value for e in at.error))
    finally:
        backup.rename(real_csv)
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
