"""데이터 분석: 앱 데이터로 직접 계산한 통계 (pandas + Plotly)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import CUISINE_COLOR, CUISINE_ORDER, DEFAULT_BUDGET_BANDS, SEARCH_RADIUS_M
from src.data import get_data, load_reviews
from src.filters import price_band
from src.i18n import cuisine_label, t
from src.ui import page_header, render_map

MIN_GROUP = 3  # 평균을 낼 때 그룹당 최소 데이터 수

df = get_data()
page_header(t("stats.title"), t("stats.subtitle"))

# ---- 필터
f1, f2 = st.columns([2, 1])
cuisines = f1.multiselect(t("stats.filter_cuisine"), CUISINE_ORDER, default=CUISINE_ORDER, format_func=cuisine_label)
max_dist = f2.slider(t("stats.filter_distance"), 200, SEARCH_RADIUS_M, SEARCH_RADIUS_M, step=100)
data = df[df["cuisine"].isin(cuisines) & (df["distance_m"] <= max_dist)].copy()
data["cuisine_label"] = data["cuisine"].map(cuisine_label)
color_map = {cuisine_label(k): v for k, v in CUISINE_COLOR.items()}
reviews = load_reviews()
reviews = reviews[reviews["store_id"].isin(data["id"])]

if data.empty:
    st.warning(t("common.no_results"))
    st.stop()

# ---- 핵심 지표
k1, k2, k3, k4 = st.columns(4)
k1.metric(t("stats.kpi_total"), f"{len(data):,}")
k2.metric(t("stats.kpi_avg_dist"), f"{data['distance_m'].mean():,.0f}m")
k3.metric(t("stats.kpi_priced"), f"{int(data['budget_price'].notna().sum())}")
k4.metric(t("stats.kpi_reviews"), f"{len(reviews)}")


def style(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_traces(textangle=0, textposition="outside", cliponaxis=False, selector=dict(type="bar"))
    return fig


c1, c2 = st.columns(2)

# ① 음식 종류별 가게 수: value_counts
with c1:
    st.markdown(f"#### {t('stats.by_cuisine')}")
    counts = data["cuisine_label"].value_counts().reset_index()
    counts.columns = ["cuisine_label", "count"]
    fig = px.bar(counts, x="count", y="cuisine_label", orientation="h", color="cuisine_label",
                 color_discrete_map=color_map, text="count",
                 labels={"count": t("stats.axis.count"), "cuisine_label": t("stats.axis.cuisine")})
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(style(fig), width="stretch")

# ② 구역별 가게 수
with c2:
    st.markdown(f"#### {t('stats.by_area')}")
    area = data.groupby("area").size().reset_index(name="count").sort_values("count", ascending=False)
    fig = px.bar(area, x="area", y="count", text="count", color_discrete_sequence=["#F26B3A"],
                 labels={"count": t("stats.axis.count"), "area": t("stats.axis.area")})
    st.plotly_chart(style(fig), width="stretch")

c3, c4 = st.columns(2)
priced = data[data["budget_price"].notna()].copy()

# ③ 가격 구간별 가게 수 (가격이 확인된 가게만)
with c3:
    st.markdown(f"#### {t('stats.by_price', n=len(priced))}")
    if len(priced) < MIN_GROUP:
        st.info(t("stats.not_enough", n=MIN_GROUP))
    else:
        low, high = DEFAULT_BUDGET_BANDS
        names = {"low": t("budget.band.low", a=f"{low:,}"),
                 "mid": t("budget.band.mid", a=f"{low:,}", b=f"{high:,}"),
                 "high": t("budget.band.high", b=f"{high:,}")}
        priced["band"] = priced["budget_price"].map(lambda p: names[price_band(p, low, high)])
        band = priced["band"].value_counts().reindex(names.values(), fill_value=0).reset_index()
        band.columns = ["band", "count"]
        fig = px.bar(band, x="band", y="count", text="count", color_discrete_sequence=["#2B8A3E"],
                     labels={"count": t("stats.axis.count"), "band": t("stats.axis.band")})
        st.plotly_chart(style(fig), width="stretch")

# ④ 음식 종류별 평균 최저가 (그룹당 MIN_GROUP 개 이상일 때만)
with c4:
    st.markdown(f"#### {t('stats.avg_price')}")
    g = priced.groupby("cuisine_label")["budget_price"].agg(["mean", "count"]).reset_index()
    g = g[g["count"] >= MIN_GROUP]
    if g.empty:
        st.info(t("stats.not_enough", n=MIN_GROUP))
    else:
        g["mean"] = g["mean"].round(-1)
        fig = px.bar(g, x="cuisine_label", y="mean", text="mean", color="cuisine_label",
                     color_discrete_map=color_map, hover_data={"count": True},
                     labels={"mean": t("stats.axis.price"), "cuisine_label": t("stats.axis.cuisine"),
                             "count": t("stats.axis.count")})
        fig.update_traces(texttemplate="%{text:,.0f}원")
        st.plotly_chart(style(fig), width="stretch")

c5, c6 = st.columns(2)

# ⑤ 거리 분포 (히스토그램)
with c5:
    st.markdown(f"#### {t('stats.distance')}")
    fig = px.histogram(data, x="distance_m", nbins=15, color_discrete_sequence=["#1971C2"],
                       labels={"distance_m": t("stats.axis.distance")})
    fig.update_yaxes(title=t("stats.axis.count"))
    st.plotly_chart(style(fig), width="stretch")

# ⑥ 학생 평점 분포
with c6:
    st.markdown(f"#### {t('stats.rating')}")
    if len(reviews) < 5:
        st.info(t("stats.not_enough", n=5))
    else:
        stars = reviews["stars"].astype(int).value_counts().reindex(range(1, 6), fill_value=0).reset_index()
        stars.columns = ["stars", "count"]
        fig = px.bar(stars, x="stars", y="count", text="count", color_discrete_sequence=["#F59F00"],
                     labels={"stars": t("stats.axis.stars"), "count": t("stats.axis.reviews")})
        st.plotly_chart(style(fig), width="stretch")

st.markdown(f"#### {t('stats.map')}")
render_map(data, height=460)

with st.expander(t("stats.table")):
    cols = ["name", "cuisine_label", "category_sub", "area", "distance_m", "budget_price", "rating_avg", "rating_count"]
    st.dataframe(data[cols].sort_values("distance_m"), hide_index=True, width="stretch")
