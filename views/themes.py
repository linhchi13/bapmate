"""테마별 추천: 데이터로 확인된 조건만 사용한다."""
import streamlit as st

from src.config import CAMPUS_FRONT_M, DEFAULT_BUDGET_BANDS, MIN_VOTES, MIN_YES_RATIO
from src.data import get_data
from src.filters import sort_df
from src.i18n import t
from src.ui import empty_state, page_header, render_grid

df = get_data()
page_header(t("themes.title"), t("themes.subtitle"))

low = DEFAULT_BUDGET_BANDS[0]
ratio = int(MIN_YES_RATIO * 100)
# 테마 이름 → (설명, 조건에 맞는 가게, 정렬 기준)
THEMES = {
    "cheap": (t("themes.desc.cheap", a=f"{low:,}"), df[df["budget_price"] < low], "price"),
    "good_price": (t("themes.desc.good_price"), df[df["good_price"]], "distance"),
    "korean": (t("themes.desc.cuisine"), df[df["cuisine"].isin(["korean", "bunsik"])], "distance"),
    "vietnamese": (t("themes.desc.cuisine"), df[df["cuisine"] == "vietnamese"], "distance"),
    "japanese": (t("themes.desc.cuisine"), df[df["cuisine"] == "japanese"], "distance"),
    "chinese": (t("themes.desc.cuisine"), df[df["cuisine"] == "chinese"], "distance"),
    "solo": (t("themes.desc.solo", min=MIN_VOTES, ratio=ratio), df[df["solo_verified"]], "rating"),
    "group": (t("themes.desc.group", min=MIN_VOTES, ratio=ratio), df[df["group_verified"]], "rating"),
    "campus": (t("themes.desc.campus"), df[(df["area"] == "교내") & (df["cuisine"] != "cafe")], "name"),
    "front": (t("themes.desc.front", m=CAMPUS_FRONT_M),
              df[(df["distance_m"] <= CAMPUS_FRONT_M) & (df["cuisine"] != "cafe")], "distance"),
    "top": (t("themes.desc.top", min=MIN_VOTES), df[df["rating_count"] >= MIN_VOTES], "rating"),
}

theme = st.pills("theme", list(THEMES), default="cheap", label_visibility="collapsed",
                 format_func=lambda k: f"{t('themes.' + k)} {len(THEMES[k][1])}")
theme = theme or "cheap"
desc, items, sort_by = THEMES[theme]

st.markdown(f"### {t('themes.' + theme)}")
st.caption(desc)
if items.empty and theme in ("solo", "group", "top"):
    empty_state(t("themes.empty_votes"), "🗳️")
else:
    render_grid(sort_df(items, sort_by), "theme", reset_on=theme)
