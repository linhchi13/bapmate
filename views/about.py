"""데이터 출처·서비스 소개·팀 소개."""
import json

import pandas as pd
import streamlit as st

from src.config import QUALITY_REPORT, SOURCES_CSV
from src.i18n import t
from src.ui import page_header

TEAM = [
    ("수랩민먓", "25101784"),
    ("찐티린치", "25101811"),
    ("응웬티응옥한", "25101799"),
    ("응웬티단타오", "25101798"),
    ("따이띠뚜딴", "25101767"),
]

page_header(t("about.title"))

st.markdown(f"#### {t('about.purpose_title')}")
st.write(t("about.purpose"))

st.markdown(f"#### {t('about.sources_title')}")
if SOURCES_CSV.exists():
    src = pd.read_csv(SOURCES_CSV)
    st.dataframe(src, hide_index=True, width="stretch",
                 column_config={"url": st.column_config.LinkColumn("url")})
else:
    st.caption(t("common.no_info"))
st.caption(t("about.license"))

st.markdown(f"#### {t('about.quality_title')}")
if QUALITY_REPORT.exists():
    q = json.loads(QUALITY_REPORT.read_text(encoding="utf-8"))
    steps = pd.DataFrame([
        ("서울 전체 상가 수", q.get("raw_rows_seoul")),
        ("음식점(술집 제외)", q.get("food_rows_seoul")),
        ("학교 반경 안", q.get("within_radius")),
        ("중복 제거 수", q.get("duplicates_removed")),
        ("최종 가게 수", q.get("output_rows")),
        ("착한가격업소 연결", (q.get("good_price") or {}).get("matched") if isinstance(q.get("good_price"), dict) else None),
        ("OSM 정보 연결", (q.get("osm") or {}).get("matched") if isinstance(q.get("osm"), dict) else None),
    ], columns=["단계", "건수"])
    st.dataframe(steps, hide_index=True, width="stretch")
    st.caption(f"처리 시각: {q.get('built_at', '')}")

st.markdown(f"#### {t('about.limits_title')}")
st.markdown(t("about.limits"))

st.markdown(f"#### {t('about.team_title')}")
st.dataframe(pd.DataFrame(TEAM, columns=[t("about.name"), t("about.student_id")]), hide_index=True)
