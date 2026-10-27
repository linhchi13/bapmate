"""화면 구성 요소: 스타일, 가게 카드, 상세 창, 지도 링크, 즐겨찾기."""
import base64
import html
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

from src.auth import current_member, current_user_id, favorite_ids, login_button, members_table, set_favorite
from src.config import CUISINE_COLOR, IMAGES_DIR, MIN_VOTES, MIN_YES_RATIO
from src.data import get_data, load_reviews, save_review
from src.i18n import cuisine_label, t
from src.illustrations import illustration_key, illustration_uri

PRIMARY = "#F26B3A"

CSS = f"""
<style>
.block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
.bm-hero {{
  background: linear-gradient(135deg, {PRIMARY} 0%, #FF9A5A 60%, #FFC56E 100%);
  border-radius: 22px; padding: 26px 28px; color: #fff; margin-bottom: 18px;
  box-shadow: 0 10px 30px rgba(242,107,58,.25);
}}
.bm-hero h1 {{ color: #fff; font-size: 2rem; margin: 0; padding: 0; font-weight: 800; }}
.bm-hero p {{ margin: 6px 0 0; opacity: .95; font-size: 1rem; }}
.bm-hero .bm-stats {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }}
.bm-hero .bm-stat {{ background: rgba(255,255,255,.2); border-radius: 12px; padding: 6px 12px; font-size: .9rem; }}
.bm-hero .bm-stat b {{ font-size: 1.1rem; }}
.bm-page-title {{ font-size: 1.7rem; font-weight: 800; margin: 0 0 2px; }}
.bm-page-sub {{ color: #6B7280; margin-bottom: 14px; }}
.st-key-home_q div[data-baseweb="input"] {{
  background: #fff; border: 2px solid {PRIMARY}55; border-radius: 16px;
  box-shadow: 0 6px 18px rgba(242,107,58,.12);
}}
.st-key-home_q input {{ height: 3.3rem; font-size: 1.05rem; background: #fff; padding-left: 14px; }}
@media (max-width: 640px) {{
  .block-container {{ padding-top: 3.6rem; }}
  .bm-hero {{ padding: 18px 18px; border-radius: 18px; }}
  .bm-hero h1 {{ font-size: 1.55rem; }}
  .bm-hero .bm-stat {{ font-size: .8rem; }}
}}
.bm-sample {{
  position: absolute; bottom: 6px; right: 8px; background: rgba(0,0,0,.45); color: #fff;
  font-size: .66rem; padding: 1px 7px; border-radius: 999px;
}}
.bm-thumb {{
  height: 128px; border-radius: 14px; display: flex; align-items: center; justify-content: center;
  font-size: 44px; position: relative; overflow: hidden;
}}
.bm-thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
.bm-badge {{
  position: absolute; top: 8px; left: 8px; background: #2B8A3E; color: #fff;
  font-size: .72rem; padding: 3px 8px; border-radius: 999px; font-weight: 700;
}}
.bm-fav {{ position: absolute; top: 6px; right: 10px; font-size: 1.1rem; }}
.bm-chips {{ margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }}
.bm-chip {{
  font-size: .74rem; padding: 2px 8px; border-radius: 999px; font-weight: 600;
  background: #F3F4F6; color: #374151;
}}
.bm-name {{
  font-size: 1.04rem; font-weight: 750; margin: 6px 0 0; color: #111827;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.bm-sub {{ font-size: .78rem; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.bm-price {{ font-size: 1.2rem; font-weight: 800; color: {PRIMARY}; margin-top: 6px; }}
.bm-price small {{ font-size: .78rem; color: #6B7280; font-weight: 500; }}
.bm-price.na {{ font-size: .88rem; color: #9CA3AF; font-weight: 500; }}
.bm-meta {{ font-size: .84rem; color: #4B5563; margin-top: 2px; }}
.bm-empty {{ text-align: center; padding: 40px 10px; color: #6B7280; }}
.bm-empty div {{ font-size: 2.6rem; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="bm-page-title">{html.escape(title)}</div>'
                f'<div class="bm-page-sub">{html.escape(subtitle)}</div>', unsafe_allow_html=True)


def empty_state(message: str, icon: str = "🍽️") -> None:
    st.markdown(f'<div class="bm-empty"><div>{icon}</div>{html.escape(message)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- 표시용 도우미
def fmt_won(value) -> str:
    return f"{int(value):,}{t('common.won')}"


def has(value) -> bool:
    return value is not None and not (isinstance(value, float) and pd.isna(value)) and value is not pd.NA and str(value).strip() != ""


def map_links(r: pd.Series) -> dict:
    """무료 지도 URL. 좌표·주소가 실제 데이터에 있을 때만 만든다."""
    name = str(r["name"])
    links = {}
    if has(r.get("address")):
        links["naver"] = "https://map.naver.com/p/search/" + quote(f"{r['address']} {name}")
    if has(r.get("lat")) and has(r.get("lon")):
        links["kakao"] = f"https://map.kakao.com/link/to/{quote(name)},{r['lat']},{r['lon']}"
        links["google"] = f"https://www.google.com/maps/search/?api=1&query={r['lat']},{r['lon']}"
    return links


@lru_cache(maxsize=256)
def _img_data_uri(path: str) -> str:
    """이미지 파일 → HTML 에 바로 넣을 수 있는 data URI (같은 사진은 한 번만 읽음)."""
    p = Path(path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def _thumb_html(r: pd.Series) -> str:
    """사진 우선순위: ① 팀이 직접 찍은 가게 사진 → ② 음식 종류·세부 업종별 일러스트(예시 이미지)."""
    color = CUISINE_COLOR.get(r["cuisine"], "#6B7280")
    own = IMAGES_DIR / str(r["image_path"]) if has(r.get("image_path")) else None
    if own is not None and own.exists():
        inner = f'<img src="{_img_data_uri(str(own))}" alt="">'
    else:
        key = illustration_key(r["cuisine"], r.get("category_sub"))
        inner = (f'<img src="{illustration_uri(key)}" alt="">'
                 f'<span class="bm-sample">{t("common.sample_image")}</span>')
    badge = f'<span class="bm-badge">{t("common.good_price")}</span>' if r["good_price"] else ""
    fav = '<span class="bm-fav">❤️</span>' if r["id"] in favorites() else ""
    return (f'<div class="bm-thumb" style="background: linear-gradient(135deg, {color}22, {color}55);">'
            f'{inner}{badge}{fav}</div>')


def _price_html(r: pd.Series) -> str:
    if pd.notna(r["budget_price"]):
        note = " · 학생 제보" if r["budget_price_basis"] == "학생 제보" else ""
        return f'<div class="bm-price">{fmt_won(r["budget_price"])}{t("common.from")} <small>{html.escape(str(r["signature_menu"]) if has(r.get("signature_menu")) else "")}{note}</small></div>'
    return f'<div class="bm-price na">{t("common.no_price")}</div>'


def _rating_text(r: pd.Series) -> str:
    if r["rating_count"] > 0:
        return f"⭐ {r['rating_avg']:.1f} · {t('common.reviews', n=r['rating_count'])}"
    return t("common.no_rating")


def _distance_text(r: pd.Series) -> str:
    if r["area"] == "교내":
        return "🏫 " + t("common.on_campus")
    return f'🚶 {t("common.walk", min=int(r["walk_min"]))} · {t("common.meters", m=int(r["distance_m"]))}'


def card_html(r: pd.Series) -> str:
    color = CUISINE_COLOR.get(r["cuisine"], "#6B7280")
    sub = r["name_en"] if has(r.get("name_en")) else (r["category_sub"] if has(r.get("category_sub")) else "")
    return (
        _thumb_html(r)
        + '<div class="bm-chips">'
        + f'<span class="bm-chip" style="background:{color}1A;color:{color}">{cuisine_label(r["cuisine"])}</span>'
        + f'<span class="bm-chip">{html.escape(str(r["area"]))}</span></div>'
        + f'<div class="bm-name">{html.escape(str(r["name"]))}</div>'
        + f'<div class="bm-sub">{html.escape(str(sub))}&nbsp;</div>'
        + _price_html(r)
        + f'<div class="bm-meta">{_distance_text(r)}</div>'
        + f'<div class="bm-meta">{_rating_text(r)}</div>'
    )


# ---------------------------------------------------------------- 즐겨찾기 (회원 전용)
def favorites() -> list:
    return favorite_ids(current_user_id()) if current_member() else []


def toggle_favorite(store_id: str) -> None:
    if not current_member():
        st.session_state["toast"] = t("auth.need_login_fav")
        return
    set_favorite(current_user_id(), store_id, add=store_id not in favorites())


# ---------------------------------------------------------------- 카드 목록
def render_grid(df: pd.DataFrame, key: str, page_size: int = 12, cols: int = 3, reset_on=None) -> None:
    """가게 카드를 cols 열로 보여 주고, '더 보기'로 page_size 개씩 늘린다.
    reset_on 값(검색 조건)이 바뀌면 다시 처음 page_size 개만 보여 준다."""
    shown_key = f"{key}_shown"
    if st.session_state.get(f"{key}_sig") != reset_on:
        st.session_state[f"{key}_sig"] = reset_on
        st.session_state[shown_key] = page_size
    if df.empty:
        empty_state(t("common.no_results"), "🔍")
        return
    shown = min(st.session_state.get(shown_key, page_size), len(df))
    rows = df.head(shown)
    columns = st.columns(cols)
    for i, (_, r) in enumerate(rows.iterrows()):
        with columns[i % cols]:
            with st.container(border=True):
                st.markdown(card_html(r), unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button(t("common.detail"), key=f"{key}_d_{r['id']}", width="stretch"):
                    show_detail(r["id"])
                saved = r["id"] in favorites()
                if b2.button(t("common.saved") if saved else t("common.save"), key=f"{key}_f_{r['id']}",
                             width="stretch", type="primary" if saved else "secondary"):
                    toggle_favorite(r["id"])
                    st.rerun()
    if shown < len(df):
        if st.button(t("common.more", shown=shown, total=len(df)), key=f"{key}_more", width="stretch"):
            st.session_state[shown_key] = shown + page_size
            st.rerun()


# ---------------------------------------------------------------- 지도
def render_map(df: pd.DataFrame, height: int = 520, key: str = "map") -> None:
    """Plotly 지도(무료 Carto 배경지도, API 키 불필요). 색은 음식 종류별.
    가게 점을 누르면 그 가게의 상세 창이 열린다."""
    import plotly.graph_objects as go

    from src.config import CAMPUS_LAT, CAMPUS_LON, CUISINE_ORDER

    fig = go.Figure()
    for key in CUISINE_ORDER:
        part = df[df["cuisine"] == key]
        if part.empty:
            continue
        price = part["budget_price"].map(lambda p: fmt_won(p) if pd.notna(p) else t("common.no_price"))
        fig.add_trace(go.Scattermap(
            lat=part["lat"], lon=part["lon"], mode="markers",
            marker=dict(size=11, color=CUISINE_COLOR[key], opacity=.85),
            selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=.85)),  # 누른 뒤에도 흐려지지 않게
            name=cuisine_label(key),
            customdata=list(zip(part["name"], part["distance_m"], price, part["id"])),
            hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[1]}m · %{customdata[2]}"
                           f"<br><i>{t('common.map_click')}</i><extra></extra>"),
        ))
    fig.add_trace(go.Scattermap(
        lat=[CAMPUS_LAT], lon=[CAMPUS_LON], mode="markers+text", name=t("stats.campus"),
        marker=dict(size=18, color="#111827"), text=["🏫 " + t("stats.campus")], textposition="top center",
        hoverinfo="name",
    ))
    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=CAMPUS_LAT - 0.004, lon=CAMPUS_LON - 0.002), zoom=14),
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,.85)"),
    )
    fig.update_layout(clickmode="event+select")
    # 상세 창을 연 뒤에는 지도 key 를 바꿔 선택 상태를 초기화한다 → 같은 점을 다시 눌러도 또 열림
    version = st.session_state.get(f"{key}_v", 0)
    event = st.plotly_chart(fig, width="stretch", config={"scrollZoom": True, "displayModeBar": False},
                            on_select="rerun", selection_mode="points", key=f"{key}_{version}")

    # 점을 누르면 그 가게의 상세 창 열기
    points = event.get("selection", {}).get("points", []) if event else []
    store_id = next((str(p["customdata"][3]) for p in points
                     if p.get("customdata") and len(p["customdata"]) >= 4), None)
    if store_id:
        st.session_state[f"{key}_v"] = version + 1
        show_detail(store_id)


# ---------------------------------------------------------------- 상세 창
def _vote_text(yes: int, votes: int) -> str:
    if votes < MIN_VOTES:
        return t("detail.vote_few", n=votes, min=MIN_VOTES)
    return t("detail.vote_yes" if yes / votes >= MIN_YES_RATIO else "detail.vote_no", yes=yes, n=votes)


@st.dialog("🍽️", width="large")
def show_detail(store_id: str) -> None:
    df = get_data()
    match = df[df["id"] == store_id]
    if match.empty:
        st.error(t("common.no_results"))
        return
    r = match.iloc[0]
    color = CUISINE_COLOR.get(r["cuisine"], "#6B7280")

    st.markdown(_thumb_html(r), unsafe_allow_html=True)
    st.subheader(r["name"])
    if has(r.get("name_en")):
        st.caption(r["name_en"])
    st.markdown(
        f'<span class="bm-chip" style="background:{color}1A;color:{color}">{cuisine_label(r["cuisine"])}</span> '
        f'<span class="bm-chip">{html.escape(str(r["category_sub"]) if has(r.get("category_sub")) else "")}</span> '
        f'<span class="bm-chip">{html.escape(str(r["area"]))}</span>'
        + (f' <span class="bm-chip" style="background:#2B8A3E;color:#fff">{t("common.good_price")}</span>' if r["good_price"] else ""),
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**📍 {t('detail.address')}**  \n{r['address']}"
                    + (f" {r['building_floor']}" if has(r.get("building_floor")) else ""))
        dist = (t("common.on_campus") if r["area"] == "교내"
                else t("detail.distance_value", m=int(r["distance_m"]), min=int(r["walk_min"])))
        st.markdown(f"**🚶 {t('detail.distance')}**  \n{dist}")
        hours = r["open_hours"] if has(r.get("open_hours")) else t("common.no_info")
        src = f" _({r['hours_source']})_" if has(r.get("hours_source")) else ""
        st.markdown(f"**🕒 {t('detail.hours')}**  \n{hours}{src}")
    with c2:
        st.markdown(f"**⭐ {t('detail.rating')}**  \n{_rating_text(r)}")
        st.markdown(f"**🙋 {t('detail.solo')}**  \n{_vote_text(r['solo_yes'], r['solo_votes'])}")
        st.markdown(f"**👥 {t('detail.group')}**  \n{_vote_text(r['group_yes'], r['group_votes'])}")

    st.markdown(f"**🧾 {t('detail.menu')}**")
    if has(r.get("menus")):
        items = [m.rsplit(":", 1) for m in str(r["menus"]).split(";") if ":" in m]
        st.dataframe(pd.DataFrame([(m, fmt_won(float(p))) for m, p in items], columns=["메뉴", "가격"]),
                     hide_index=True, width="stretch")
        st.caption(t("detail.price_source", src=r["price_source"]))
    else:
        st.caption(t("common.no_price"))
    if r["student_price_n"] > 0:
        st.caption(t("detail.student_price", price=f"{int(r['student_price']):,}", n=r["student_price_n"]))

    links = map_links(r)
    if links:
        st.markdown(f"**🗺️ {t('detail.map')}**")
        lc = st.columns(len(links))
        for col, (k, url) in zip(lc, links.items()):
            col.link_button(t(f"detail.{k}"), url, width="stretch")

    st.caption(t("detail.source", src=r["source"], date=r["data_date"]))

    _recent_reviews(r["id"])

    with st.expander(f"✍️ {t('detail.review_title')}"):
        if current_member():
            _review_form(r["id"])
        else:
            st.info(t("auth.need_login_review"))
            login_button("detail_login")


def _recent_reviews(store_id: str, limit: int = 5) -> None:
    """이 가게의 최근 후기 (닉네임·국적은 회원 정보에서 가져옴)."""
    rv = load_reviews()
    rv = rv[(rv["store_id"] == store_id) & (rv["comment"].fillna("").str.strip() != "")]
    if rv.empty:
        return
    rv = rv.merge(members_table()[["user_id", "nickname", "nationality"]], on="user_id", how="left")
    st.markdown(f"**💬 {t('detail.recent_reviews')}**")
    for _, x in rv.iloc[::-1].head(limit).iterrows():
        nat = f" · {x['nationality']}" if has(x.get("nationality")) else ""
        who = x["nickname"] if has(x.get("nickname")) else t("detail.unknown_user")
        st.markdown(f"{'⭐' * int(x['stars'])} **{html.escape(str(who))}**{html.escape(nat)}  \n"
                    f"{html.escape(str(x['comment']))}")


def _review_form(store_id: str) -> None:
    uid = current_user_id()
    mine = load_reviews()
    if ((mine["user_id"] == uid) & (mine["store_id"] == store_id)).any():
        st.caption(t("review.already"))
    opts = {"yes": t("review.yes"), "no": t("review.no"), "skip": t("review.skip")}
    with st.form(f"review_{store_id}", clear_on_submit=True):
        stars = st.feedback("stars", key=f"stars_{store_id}")
        c1, c2 = st.columns(2)
        solo = c1.radio(t("review.solo"), list(opts), format_func=opts.get, index=2, horizontal=True)
        group = c2.radio(t("review.group"), list(opts), format_func=opts.get, index=2, horizontal=True)
        price = st.text_input(t("review.price_paid"))
        comment = st.text_input(t("review.comment"), max_chars=200)
        st.caption(t("review.privacy"))
        if st.form_submit_button(t("review.submit"), type="primary"):
            if stars is None:
                st.error(t("review.need_stars"))
                return
            price_value = None
            if price.strip():
                digits = price.replace(",", "").replace("원", "").strip()
                if not digits.isdigit() or not (0 < int(digits) <= 100_000):
                    st.error(t("review.invalid_price"))
                    return
                price_value = int(digits)
            save_review(uid, store_id, stars + 1, solo, group, price_value, comment)
            st.session_state["toast"] = t("review.saved")
            st.rerun()


def show_pending_toast() -> None:
    if "toast" in st.session_state:
        st.toast(st.session_state.pop("toast"), icon="✅")
