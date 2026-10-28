"""데이터 출처·서비스 소개·팀 소개."""
import json

import pandas as pd
import streamlit as st

from src.config import QR_IMAGE, QUALITY_REPORT, SOURCES_CSV
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
        (t("about.step.raw"), q.get("raw_rows_seoul")),
        (t("about.step.food"), q.get("food_rows_seoul")),
        (t("about.step.radius"), q.get("within_radius")),
        (t("about.step.dup"), q.get("duplicates_removed")),
        (t("about.step.final"), q.get("output_rows")),
        (t("about.step.good_price"), (q.get("good_price") or {}).get("matched") if isinstance(q.get("good_price"), dict) else None),
        (t("about.step.osm"), (q.get("osm") or {}).get("matched") if isinstance(q.get("osm"), dict) else None),
    ], columns=[t("about.step"), t("about.count")])
    st.dataframe(steps, hide_index=True, width="stretch")
    st.caption(t("about.built_at", time=q.get("built_at", "")))

st.markdown(f"#### {t('about.limits_title')}")
st.markdown(t("about.limits"))

st.markdown(f"#### {t('about.images_title')}")
st.write(t("about.images"))

st.markdown(f"#### {t('about.privacy_title')}")
st.markdown(t("about.privacy"))

if QR_IMAGE.exists():
    st.markdown(f"#### {t('about.qr_title')}")
    st.caption(t("about.qr"))
    st.image(str(QR_IMAGE), width=220)

st.markdown(f"#### {t('about.team_title')}")
st.dataframe(pd.DataFrame(TEAM, columns=[t("about.name"), t("about.student_id")]), hide_index=True)
