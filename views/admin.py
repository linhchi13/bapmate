"""관리자 페이지: 회원·평가 현황 보기, 부적절한 후기 삭제, CSV 내려받기.

secrets.toml 의 [admin] emails 에 등록된 Gmail 로 로그인한 사람만 볼 수 있다.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from src.auth import is_admin
from src.data import load_restaurants
from src.i18n import t
from src.storage import delete_rows, get_storage, read_table
from src.ui import page_header

if not is_admin():  # 주소를 직접 입력해 들어와도 막는다
    st.error(t("admin.denied"))
    st.stop()

page_header(t("admin.title"), t("admin.subtitle", storage=get_storage().name))
if st.button(t("admin.refresh")):
    read_table.clear()
    st.rerun()

members = read_table("members").drop_duplicates("user_id", keep="last")
reviews = read_table("reviews").drop_duplicates(["user_id", "store_id"], keep="last")
fav = read_table("favorites").drop_duplicates(["user_id", "store_id"], keep="last")
fav = fav[fav["action"] == "add"]
names = load_restaurants().set_index("id")["name"]
today = pd.Timestamp.now().strftime("%Y-%m-%d")

# ---- 핵심 지표
k1, k2, k3, k4 = st.columns(4)
k1.metric(t("admin.members"), len(members))
k2.metric(t("admin.today"), int(members["joined_at"].str.startswith(today).sum()))
k3.metric(t("admin.reviews"), len(reviews))
k4.metric(t("admin.favorites"), len(fav))

if members.empty:
    st.info(t("admin.no_members"))
    st.stop()

# ---- 가입 추이 / 국적 분포
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"#### {t('admin.signup_trend')}")
    daily = members.assign(date=members["joined_at"].str[:10]).groupby("date").size().reset_index(name="n")
    daily["total"] = daily["n"].cumsum()
    fig = px.bar(daily, x="date", y="n", labels={"date": "", "n": t("admin.members")},
                 color_discrete_sequence=["#F26B3A"])
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
with c2:
    st.markdown(f"#### {t('admin.nationality')}")
    nat = members["nationality"].replace("", t("auth.no_answer")).value_counts().reset_index()
    nat.columns = ["nationality", "n"]
    fig = px.pie(nat, names="nationality", values="n", hole=.45)
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")

# ---- 회원 목록 (이메일 없음)
st.markdown(f"#### {t('admin.member_list')}")
per_user_reviews = reviews.groupby("user_id").size()
per_user_fav = fav.groupby("user_id").size()
table = pd.DataFrame({
    t("auth.nickname"): members["nickname"],
    t("auth.nationality"): members["nationality"],
    t("admin.joined"): members["joined_at"],
    t("admin.reviews"): members["user_id"].map(per_user_reviews).fillna(0).astype(int),
    t("admin.favorites"): members["user_id"].map(per_user_fav).fillna(0).astype(int),
}).sort_values(t("admin.joined"), ascending=False)
st.dataframe(table, hide_index=True, width="stretch")
st.download_button(t("admin.download_members"), table.to_csv(index=False).encode("utf-8-sig"),
                   "bapmate_members.csv", "text/csv")

# ---- 후기 관리
st.markdown(f"#### {t('admin.review_list')}")
if reviews.empty:
    st.caption(t("my.no_reviews"))
else:
    nick = members.set_index("user_id")["nickname"]
    rv = reviews.assign(store=reviews["store_id"].map(names), who=reviews["user_id"].map(nick)).iloc[::-1]
    for _, r in rv.head(50).iterrows():
        with st.container(border=True):
            a, b = st.columns([5, 1])
            stars = int(float(r["stars"])) if str(r["stars"]).replace(".", "").isdigit() else 0
            a.markdown(f"**{r['store']}** · {'⭐' * stars} · {r['who'] or '-'} · {str(r['created_at'])[:16]}  \n"
                       f"{r['comment'] or ''}")
            if b.button(t("admin.delete"), key=f"del_{r['review_id']}"):
                delete_rows("reviews", "review_id", r["review_id"])
                st.session_state["toast"] = t("admin.deleted")
                st.rerun()
    st.download_button(t("admin.download_reviews"),
                       rv[["store", "stars", "who", "comment", "price_paid", "created_at"]].to_csv(index=False).encode("utf-8-sig"),
                       "bapmate_reviews.csv", "text/csv")
