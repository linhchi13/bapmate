"""마이페이지: 즐겨찾기, 내가 쓴 평가, 계정(로그아웃·탈퇴)."""
import pandas as pd
import streamlit as st

from src.auth import current_member, current_user_id, login_button, logout, withdraw
from src.data import get_data, load_reviews
from src.i18n import nationality_label, t
from src.ui import empty_state, favorites, page_header, render_grid

page_header(t("my.title"), t("my.subtitle"))

member = current_member()
if not member:
    empty_state(t("my.need_login"), "👤")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        login_button("my_login")
    st.stop()

df = get_data()
uid = current_user_id()
mine = load_reviews()
mine = mine[mine["user_id"] == uid]
fav_ids = favorites()

c1, c2, c3 = st.columns(3)
c1.metric(t("my.nickname"), member["nickname"])
c2.metric(t("my.favorites"), len(fav_ids))
c3.metric(t("my.reviews"), len(mine))

tab_fav, tab_rev, tab_acc = st.tabs([f"❤️ {t('my.favorites')}", f"✍️ {t('my.review_list')}", f"⚙️ {t('my.account')}"])

with tab_fav:
    fav_df = df[df["id"].isin(fav_ids)]
    if fav_df.empty:
        empty_state(t("fav.empty"), "🤍")
    else:
        render_grid(fav_df.sort_values("distance_m"), "fav")

with tab_rev:
    if mine.empty:
        st.caption(t("my.no_reviews"))
    else:
        names = df.set_index("id")["name"]
        table = pd.DataFrame({
            t("my.col_store"): mine["store_id"].map(names),
            t("my.col_stars"): mine["stars"].astype(int).map(lambda s: "⭐" * s),
            t("my.col_comment"): mine["comment"],
            t("my.col_date"): mine["created_at"].str[:10],
        }).iloc[::-1]
        st.dataframe(table, hide_index=True, width="stretch")

with tab_acc:
    st.caption(t("my.joined", date=member["joined_at"][:10], nat=nationality_label(member["nationality"])))
    b1, b2 = st.columns(2)
    if b1.button(t("auth.logout"), width="stretch"):
        logout()
    with b2.popover(t("my.withdraw"), width="stretch"):
        st.warning(t("my.withdraw_warn"))
        if st.button(t("my.withdraw_confirm"), type="primary"):
            withdraw()
