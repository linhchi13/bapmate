"""즐겨찾기: 회원 전용. 저장소(CSV/Google Sheets)에 저장되어 언제 어디서나 다시 볼 수 있다."""
import streamlit as st

from src.auth import current_member, login_button
from src.data import get_data
from src.i18n import t
from src.ui import empty_state, favorites, page_header, render_grid

page_header(t("fav.title"), t("fav.subtitle"))

if not current_member():
    empty_state(t("auth.need_login_fav"), "🔐")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        login_button("fav_login")
    st.stop()

df = get_data()
fav_df = df[df["id"].isin(favorites())]
if fav_df.empty:
    empty_state(t("fav.empty"), "🤍")
else:
    st.markdown(f"**{t('common.results', n=len(fav_df))}**")
    render_grid(fav_df.sort_values("distance_m"), "fav")
