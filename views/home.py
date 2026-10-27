"""홈: 검색 + 필터 + 가게 카드/지도."""
import streamlit as st

from src.config import CUISINE_ORDER, DEFAULT_BUDGET_BANDS
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

# 예산: 선택하면 가격이 확인된 가게 중에서만 찾는다
low, high = DEFAULT_BUDGET_BANDS
budget_opts = {"low": t("home.budget_upto", won=f"{low:,}"), "high": t("home.budget_upto", won=f"{high:,}"),
               "custom": t("home.budget_custom")}
b1, b2 = st.columns([3, 1])
budget_choice = b1.pills(t("home.filter_budget"), list(budget_opts), format_func=budget_opts.get, key="home_budget")
budget = {"low": low, "high": high}.get(budget_choice)
if budget_choice == "custom":
    budget = b2.number_input(t("home.budget_input"), 1000, 100_000, 10_000, 1000, format="%d")

with st.expander(f"⚙️ {t('home.more_filters')}"):
    c1, c2, c3 = st.columns([1.2, 1.2, 1])
    area_order = {"교내": 0, "학교 앞": 1}
    areas = [""] + sorted(df["area"].unique(), key=lambda a: (area_order.get(a, 2), a))
    area = c1.selectbox(t("home.filter_area"), areas, format_func=lambda a: a or t("home.filter_area_all"))
    max_walk = c2.slider(t("home.filter_walk"), 3, int(df["walk_min"].max()), int(df["walk_min"].max()))
    sort_opts = ["distance", "price", "rating", "name"]
    sort_by = c3.selectbox(t("home.sort"), sort_opts, format_func=lambda k: t(f"home.sort.{k}"),
                           index=1 if budget else 0)
    include_cafe = st.toggle(t("home.include_cafe"), value=False)

view = st.segmented_control("view", ["list", "map"], default="list", label_visibility="collapsed",
                            format_func=lambda v: "📋 " + t("home.view_list") if v == "list" else "🗺️ " + t("home.view_map"))

result = search(df, query)
result = apply_filters(result, cuisines=cuisines, area=area or None, max_walk=max_walk,
                       include_cafe=include_cafe, max_price=budget)
result = sort_df(result, sort_by)

st.markdown(f"**{t('common.results', n=len(result))}**")
if budget:
    st.caption("💡 " + t("home.budget_note", n=int(df["budget_price"].notna().sum())))
if view == "map":
    render_map(result, key="home_map")
else:
    render_grid(result, "home", reset_on=(query, tuple(cuisines), budget, area, max_walk, sort_by, include_cafe))
