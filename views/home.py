"""홈: 검색 + 필터 + 가게 카드/지도."""
import streamlit as st

from src.config import CUISINE_ORDER
from src.data import get_data
from src.filters import apply_filters, search, sort_df
from src.i18n import cuisine_label, t
from src.ui import render_grid, render_map

df = get_data()

st.markdown(f"""
<div class="bm-hero">
  <h1>🍚 {t('app.name')}</h1>
  <p>{t('app.tagline')}</p>
  <div class="bm-stats">
    <span class="bm-stat">{t('home.stat_total')} <b>{len(df):,}</b></span>
    <span class="bm-stat">{t('home.stat_priced')} <b>{int(df['budget_price'].notna().sum())}</b></span>
    <span class="bm-stat">{t('home.stat_rated')} <b>{int(df['rating_count'].sum())}</b></span>
  </div>
</div>
""", unsafe_allow_html=True)

query = st.text_input("search", placeholder=t("home.search_placeholder"), key="home_q",
                      label_visibility="collapsed")
cuisines = st.pills(t("home.filter_cuisine"), CUISINE_ORDER, format_func=cuisine_label,
                    selection_mode="multi", key="home_cuisine")

with st.expander(f"⚙️ {t('home.more_filters')}"):
    c1, c2, c3 = st.columns([1.2, 1.2, 1])
    area_order = {"교내": 0, "학교 앞": 1}
    areas = [""] + sorted(df["area"].unique(), key=lambda a: (area_order.get(a, 2), a))
    area = c1.selectbox(t("home.filter_area"), areas, format_func=lambda a: a or t("home.filter_area_all"))
    max_walk = c2.slider(t("home.filter_walk"), 3, int(df["walk_min"].max()), int(df["walk_min"].max()))
    sort_opts = ["distance", "price", "rating", "name"]
    sort_by = c3.selectbox(t("home.sort"), sort_opts, format_func=lambda k: t(f"home.sort.{k}"))
    c4, c5 = st.columns(2)
    include_cafe = c4.toggle(t("home.include_cafe"), value=False)
    only_priced = c5.toggle(t("home.only_priced"), value=False)

view = st.segmented_control("view", ["list", "map"], default="list", label_visibility="collapsed",
                            format_func=lambda v: "📋 " + t("home.view_list") if v == "list" else "🗺️ " + t("home.view_map"))

result = search(df, query)
result = apply_filters(result, cuisines=cuisines, area=area or None, max_walk=max_walk,
                       include_cafe=include_cafe, only_priced=only_priced)
result = sort_df(result, sort_by)

st.markdown(f"**{t('common.results', n=len(result))}**")
if view == "map":
    render_map(result)
else:
    render_grid(result, "home", reset_on=(query, tuple(cuisines), area, max_walk, sort_by, include_cafe, only_priced))
