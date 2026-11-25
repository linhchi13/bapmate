"""프로젝트 소개 (최종 발표용): 조회수 현황, 팀원 역할, 홍보 방법, 비즈니스 모델 분석."""
import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import CHANNELS, visits
from src.config import QR_IMAGE
from src.data import get_data
from src.i18n import t
from src.storage import read_table
from src.ui import page_header

# (이름, 학번, 역할 키) — 역할 문구는 locales 의 team.role.<키>, team.task.<키>
TEAM = [
    ("찐티린치", "25101811", "linhchi"),
    ("따이띠뚜딴", "25101767", "tan"),
    ("응웬티단타오", "25101798", "thao"),
    ("수랩민먓", "25101784", "minmyat"),
    ("응웬티응옥한", "25101799", "ngochan"),
]


def style(fig, vmax: int, height=300):
    """vmax: 가장 큰 조회수. 눈금이 0.5 처럼 소수로 나오지 않게 정수 간격으로 맞춘다."""
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, bargap=0.5,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    step = max(1, -(-vmax // 5))  # 눈금 5개 정도
    fig.for_each_xaxis(lambda a: a.update(dtick=step) if a.type != "category" else None)
    fig.for_each_yaxis(lambda a: a.update(dtick=step) if a.type != "category" else None)
    fig.update_traces(textposition="outside", cliponaxis=False, selector=dict(type="bar"))
    return fig


page_header(t("project.title"), t("project.subtitle"))

# ---- ① 조회수 (실시간)
v = visits()
today = pd.Timestamp.now().strftime("%Y-%m-%d")
members = read_table("members").drop_duplicates("user_id", keep="last")
reviews = read_table("reviews").drop_duplicates(["user_id", "store_id"], keep="last")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(t("project.kpi_views"), f"{len(v):,}")
k2.metric(t("project.kpi_today"), f"{int((v['date'] == today).sum()):,}")
k3.metric(t("project.kpi_members"), f"{len(members):,}")
k4.metric(t("project.kpi_reviews"), f"{len(reviews):,}")
k5.metric(t("project.kpi_stores"), f"{len(get_data()):,}")
st.caption(t("project.views_note"))

if not v.empty:
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"#### {t('project.daily_views')}")
        daily = v.groupby("date").size().reset_index(name="n")
        fig = px.bar(daily, x="date", y="n", text="n", color_discrete_sequence=["#F26B3A"],
                     labels={"date": "", "n": t("project.kpi_views")})
        fig.update_xaxes(type="category")
        st.plotly_chart(style(fig, int(daily["n"].max())), width="stretch")
    with c2:
        st.markdown(f"#### {t('project.by_channel')}")
        ch = v["channel"].map(lambda c: t(f"channel.{c}") if c in CHANNELS else t("channel.etc"))
        ch = ch.value_counts().reset_index()
        ch.columns = ["channel", "n"]
        fig = px.bar(ch, x="n", y="channel", orientation="h", text="n", color_discrete_sequence=["#2B8A3E"],
                     labels={"channel": "", "n": t("project.kpi_views")})
        fig.update_yaxes(type="category", categoryorder="total ascending")
        st.plotly_chart(style(fig, int(ch["n"].max())), width="stretch")

# ---- ② 팀원 역할
st.markdown(f"#### 👥 {t('project.team_title')}")
st.dataframe(pd.DataFrame([(name, sid, t(f"team.role.{key}"), t(f"team.task.{key}")) for name, sid, key in TEAM],
                          columns=[t("about.name"), t("about.student_id"), t("project.role"), t("project.task")]),
             hide_index=True, width="stretch")

# ---- ③ 홍보 방법
st.markdown(f"#### 📣 {t('project.promo_title')}")
p1, p2 = st.columns([3, 1])
p1.markdown(t("project.promo"))
if QR_IMAGE.exists():
    p2.image(str(QR_IMAGE), width=200)

# ---- ④ 비즈니스 모델 분석
st.markdown(f"#### 💼 {t('project.bm_title')}")
st.write(t("project.bm_intro"))
blocks = ["customer", "problem", "value", "channels", "revenue", "cost", "metrics", "advantage", "partners"]
cols = st.columns(3)
for i, b in enumerate(blocks):
    with cols[i % 3].container(border=True):
        st.markdown(f"**{t(f'bm.{b}.title')}**")
        st.markdown(t(f"bm.{b}.body"))
st.markdown(f"##### {t('project.bm_roadmap_title')}")
st.markdown(t("project.bm_roadmap"))
