"""예산으로 찾기: 가격이 확인된 가게만 대상으로 한다."""
import streamlit as st

from src.config import DEFAULT_BUDGET_BANDS
from src.data import get_data
from src.filters import apply_filters, price_band, sort_df
from src.i18n import t
from src.ui import page_header, render_grid

df = get_data()
page_header(t("budget.title"), t("budget.subtitle"))

budget = st.number_input(t("budget.input"), min_value=1000, max_value=100_000,
                         value=10_000, step=1000, format="%d")

with st.expander(f"⚙️ {t('budget.bands')}"):
    b1, b2 = st.columns(2)
    low = b1.number_input(t("budget.band_low"), 1000, 100_000, DEFAULT_BUDGET_BANDS[0], 500, format="%d")
    high = b2.number_input(t("budget.band_high"), 1000, 100_000, DEFAULT_BUDGET_BANDS[1], 500, format="%d")
    if low >= high:  # 잘못된 구간이면 자동으로 순서를 바꿔 쓴다
        low, high = min(low, high), max(low, high) + 500

priced = df[df["budget_price"].notna()]
st.info(t("budget.coverage", total=f"{len(df):,}", n=len(priced)), icon="ℹ️")

bands = priced["budget_price"].map(lambda p: price_band(p, low, high)).value_counts()
m1, m2, m3 = st.columns(3)
m1.metric(t("budget.band.low", a=f"{low:,}"), t("common.results", n=int(bands.get("low", 0))))
m2.metric(t("budget.band.mid", a=f"{low:,}", b=f"{high:,}"), t("common.results", n=int(bands.get("mid", 0))))
m3.metric(t("budget.band.high", b=f"{high:,}"), t("common.results", n=int(bands.get("high", 0))))

result = sort_df(apply_filters(df, max_price=budget), "price")
st.markdown(f"#### {t('budget.result', budget=f'{budget:,}')} · {t('common.results', n=len(result))}")
render_grid(result, "budget", reset_on=budget)
st.caption("💡 " + t("budget.help_more"))
