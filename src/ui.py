"""화면 구성 요소: 스타일, 가게 카드, 상세 창, 지도 링크, 즐겨찾기."""
import base64
import html
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

from src.auth import (current_member, current_user_id, favorite_ids, is_admin, login_button, members_table,
                      set_favorite)
from src.config import CUISINE_COLOR, IMAGES_DIR, MIN_VOTES, MIN_YES_RATIO
from src.data import encode_menus, get_data, load_reviews, parse_menus, save_review, save_store_update
from src.i18n import area_label, cuisine_label, current_lang, nationality_label, source_label, t
from src.illustrations import illustration_key, illustration_uri

PRIMARY = "#F26B3A"

CSS = f"""
<style>
.block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
/* ---- 언어 전환: 화면 위쪽 헤더 줄에 떠 있는 작은 알약 모양 버튼 */
.st-key-langbar {{
  position: fixed; top: 12px; right: 170px; z-index: 1000001;
  width: auto !important; gap: 2px !important; padding: 3px;
  background: #fff; border: 1px solid #FFD2B8; border-radius: 999px;
  box-shadow: 0 3px 10px rgba(242,107,58,.15);
}}
.st-key-langbar [data-testid="stElementContainer"], .st-key-langbar .stButton {{ width: auto !important; }}
.st-key-langbar button {{
  min-height: 0 !important; height: 30px; padding: 0 14px !important; border-radius: 999px !important;
  font-size: .8rem !important; font-weight: 700; border: none !important; box-shadow: none !important;
}}
.st-key-langbar button[kind="secondary"] {{ background: transparent !important; color: #8A6450 !important; }}
.st-key-langbar button[kind="secondary"]:hover {{ background: #FFF1E8 !important; color: {PRIMARY} !important; }}
.st-key-langbar button p {{ font-size: .8rem !important; }}

/* ---- 홈 배너 (밝은 크림·피치 배경) */
.st-key-hero {{
  position: relative; overflow: hidden;
  background:
    radial-gradient(circle at 12% 110%, rgba(255,255,255,.55) 0 90px, transparent 91px),
    radial-gradient(circle at 92% -10%, rgba(255,255,255,.35) 0 120px, transparent 121px),
    linear-gradient(120deg, #FFE4D0 0%, #FFCFAE 55%, #FFBE93 100%);
  border-radius: 26px; padding: 22px 26px 18px; margin-bottom: 6px;
  box-shadow: 0 10px 26px rgba(242,107,58,.18);
}}
/* 스티커: 배너 빈 곳에 흩어 놓기 (스티커가 든 칸은 높이 0) */
.st-key-hero [data-testid="stElementContainer"]:has(.bm-stk) {{ height: 0; margin: 0; position: static; }}
.st-key-hero [data-testid="stMarkdown"]:has(.bm-stk), .st-key-hero [data-testid="stMarkdownContainer"]:has(.bm-stk) {{ position: static; }}
.bm-stk {{ position: absolute; z-index: 0; filter: drop-shadow(0 3px 4px rgba(160,70,20,.25)); pointer-events: none; }}
.bm-stk-onigiri  {{ width: 58px; left: 52%; top: 16px; transform: rotate(-12deg); }}
.bm-stk-star     {{ width: 40px; left: 59%; top: 44%; transform: rotate(14deg); }}
.bm-stk-boba     {{ width: 56px; left: 57%; bottom: 8px; transform: rotate(8deg); }}
.bm-stk-heart    {{ width: 30px; left: 47%; top: 50%; transform: rotate(-10deg); }}
.bm-stk-skewer   {{ width: 56px; right: 10px; bottom: 6px; transform: rotate(28deg); }}
.bm-stk-dumpling {{ width: 54px; right: 14px; top: 12px; transform: rotate(10deg); }}
.st-key-hero [data-testid="stHorizontalBlock"] {{ position: relative; z-index: 1; }}
.bm-hero-right {{ position: relative; }}
.bm-bubble {{
  position: absolute; left: -6px; top: 4px; z-index: 2;
  background: #fff; color: {PRIMARY}; font-weight: 800; font-size: .92rem;
  padding: 8px 14px; border-radius: 18px; box-shadow: 0 4px 12px rgba(160,70,20,.15);
}}
.bm-bubble::after {{
  content: ""; position: absolute; right: 18px; bottom: -9px;
  border-width: 10px 8px 0 8px; border-style: solid; border-color: #fff transparent transparent transparent;
}}
.bm-hero-badge {{
  display: inline-block; background: #fff; color: {PRIMARY}; border: 1px solid #FFD2B8;
  border-radius: 999px; padding: 2px 12px; font-size: .74rem; font-weight: 800; letter-spacing: .3px;
}}
.bm-hero-title {{ font-size: 2.4rem; font-weight: 900; color: #3B2A20; line-height: 1.15; margin-top: 8px;
  display: flex; align-items: center; gap: 8px; }}
.bm-hero-mini {{ display: none; width: 52px; }}
.bm-hero-sub {{ color: #8A6450; font-size: 1.02rem; margin: 6px 0 14px; }}
.bm-stats {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }}
.bm-stat {{
  background: #fff; color: #7A4A30; border-radius: 12px; padding: 5px 12px; font-size: .82rem;
  border: 1px solid #FFE1CD;
}}
.bm-stat b {{ color: {PRIMARY}; font-size: 1rem; margin-left: 2px; }}
.bm-hero-img {{ width: 100%; max-width: 380px; display: block; margin: 0 auto;
  filter: drop-shadow(0 8px 12px rgba(200,110,60,.18)); }}
.bm-page-title {{ font-size: 1.7rem; font-weight: 800; margin: 0 0 2px; }}
.bm-page-sub {{ color: #6B7280; margin-bottom: 14px; }}
.st-key-home_q div[data-baseweb="input"] {{
  background: #fff; border: 2px solid {PRIMARY}55; border-radius: 16px;
  box-shadow: 0 6px 18px rgba(242,107,58,.12);
}}
.st-key-home_q input {{ height: 3.3rem; font-size: 1.05rem; background: #fff; padding-left: 14px; }}
@media (max-width: 640px) {{
  .block-container {{ padding-top: 3.6rem; }}
  .st-key-langbar {{ top: 10px; right: auto; left: 50%; transform: translateX(-50%); }}
  .st-key-langbar button {{ height: 28px; padding: 0 10px !important; }}
  .st-key-hero {{ padding: 16px 14px 12px; border-radius: 20px; }}
  .bm-hero-title {{ font-size: 1.75rem; }}
  .bm-hero-mini {{ display: inline-block; }}   /* 휴대폰: 큰 마스코트 대신 제목 옆 작은 마스코트 */
  .bm-hero-img, .bm-bubble {{ display: none; }}
  .bm-stat {{ font-size: .76rem; padding: 4px 9px; }}
  .bm-stk-onigiri, .bm-stk-star, .bm-stk-boba, .bm-stk-heart {{ display: none; }}
  .bm-stk-dumpling {{ width: 40px; right: 10px; top: 10px; }}
  .bm-stk-skewer {{ width: 38px; right: 8px; bottom: 6px; }}
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
.bm-cta {{ color: {PRIMARY}; font-weight: 600; }}
.bm-naver {{ color: #03C75A !important; font-weight: 700; text-decoration: none; }}
.bm-naver:hover {{ text-decoration: underline; }}.bm-empty {{ text-align: center; padding: 40px 10px; color: #6B7280; }}
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


def naver_url(r: pd.Series) -> str:
    """네이버 지도 검색 링크. '구 이름 + 가게 이름'으로 찾으면 정확도가 가장 높다."""
    area = r["district"] if has(r.get("district")) else "노원구"
    return "https://map.naver.com/p/search/" + quote(f"{area} {r['name']}")


def map_links(r: pd.Series) -> dict:
    """무료 지도 URL. 좌표·주소가 실제 데이터에 있을 때만 만든다.
    한국에서는 구글 지도의 길찾기가 제한되므로 네이버 지도·카카오맵만 쓴다."""
    name = str(r["name"])
    links = {}
    if has(r.get("address")):
        links["naver"] = naver_url(r)
    if has(r.get("lat")) and has(r.get("lon")):
        links["kakao"] = f"https://map.kakao.com/link/to/{quote(name)},{r['lat']},{r['lon']}"
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
        note = f" · {t('src.student')}" if r["budget_price_basis"] == "학생 제보" else ""
        return f'<div class="bm-price">{fmt_won(r["budget_price"])}{t("common.from")} <small>{html.escape(str(r["signature_menu"]) if has(r.get("signature_menu")) else "")}{note}</small></div>'
    return (f'<div class="bm-price na">{t("common.no_price")} · '
            f'<a class="bm-naver" href="{naver_url(r)}" target="_blank" rel="noopener">{t("common.see_naver")}</a></div>')


def _rating_text(r: pd.Series) -> str:
    if r["rating_count"] > 0:
        return f"⭐ {r['rating_avg']:.1f} · {t('common.reviews', n=r['rating_count'])}"
    return t("common.no_rating")


def _rating_html(r: pd.Series) -> str:
    """카드용: 평가가 없으면 첫 평가를 부탁하는 문구."""
    if r["rating_count"] > 0:
        return f'<div class="bm-meta">{_rating_text(r)}</div>'
    return f'<div class="bm-meta bm-cta">{t("common.first_review")}</div>'


def _category_sub(r: pd.Series) -> str:
    """세부 업종(공공데이터 원문, 한국어)은 한국어 화면에서만 보여 준다."""
    if current_lang() == "ko" and has(r.get("category_sub")):
        return str(r["category_sub"])
    return ""


def _distance_text(r: pd.Series) -> str:
    if r["area"] == "교내":
        return "🏫 " + t("common.on_campus")
    return f'🚶 {t("common.walk", min=int(r["walk_min"]))} · {t("common.meters", m=int(r["distance_m"]))}'


def card_html(r: pd.Series) -> str:
    color = CUISINE_COLOR.get(r["cuisine"], "#6B7280")
    sub = r["name_en"] if has(r.get("name_en")) else _category_sub(r)
    return (
        _thumb_html(r)
        + '<div class="bm-chips">'
        + f'<span class="bm-chip" style="background:{color}1A;color:{color}">{cuisine_label(r["cuisine"])}</span>'
        + f'<span class="bm-chip">{html.escape(area_label(r["area"]))}</span></div>'
        + f'<div class="bm-name">{html.escape(str(r["name"]))}</div>'
        + f'<div class="bm-sub">{html.escape(str(sub))}&nbsp;</div>'
        + _price_html(r)
        + f'<div class="bm-meta">{_distance_text(r)}</div>'
        + _rating_html(r)
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
        + (f'<span class="bm-chip">{html.escape(_category_sub(r))}</span> ' if _category_sub(r) else "")
        + f'<span class="bm-chip">{html.escape(area_label(r["area"]))}</span>'
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
        src = f" _({source_label(r['hours_source'])})_" if has(r.get("hours_source")) else ""
        st.markdown(f"**🕒 {t('detail.hours')}**  \n{hours}{src}")
    with c2:
        st.markdown(f"**⭐ {t('detail.rating')}**  \n{_rating_text(r)}")
        # 혼밥·모임 추천은 응답이 충분히 모였을 때만 보여 준다
        if r["solo_votes"] >= MIN_VOTES:
            st.markdown(f"**🙋 {t('detail.solo')}**  \n{_vote_text(r['solo_yes'], r['solo_votes'])}")
        if r["group_votes"] >= MIN_VOTES:
            st.markdown(f"**👥 {t('detail.group')}**  \n{_vote_text(r['group_yes'], r['group_votes'])}")

    st.markdown(f"**🧾 {t('detail.menu')}**")
    items = parse_menus(r.get("menus"))
    if items:
        st.dataframe(pd.DataFrame([(m, fmt_won(p)) for m, p in items], columns=[t("edit.menu"), t("edit.price")]),
                     hide_index=True, width="stretch")
        st.caption(t("detail.price_source", src=source_label(r["price_source"])))
    else:
        st.caption(t("common.no_price"))
    if not items or not has(r.get("open_hours")):  # 모르는 정보는 네이버에서 바로 확인
        st.link_button(t("detail.naver_info"), naver_url(r), type="primary", width="stretch")
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

    # 평가가 하나도 없으면 평가 창을 펼쳐 두어 첫 평가를 유도한다
    with st.expander(f"✍️ {t('detail.review_title')}", expanded=r["rating_count"] == 0):
        if current_member():
            _review_form(r["id"])
        else:
            st.info(t("auth.need_login_review"))
            login_button("detail_login")

    with st.expander(f"📝 {t('edit.title_admin') if is_admin() else t('edit.title_member')}"):
        if current_member():
            _store_update_form(r)
        else:
            st.info(t("edit.need_login"))
            login_button("edit_login")


def _recent_reviews(store_id: str, limit: int = 5) -> None:
    """이 가게의 최근 후기 (닉네임·국적은 회원 정보에서 가져옴)."""
    rv = load_reviews()
    rv = rv[(rv["store_id"] == store_id) & (rv["comment"].fillna("").str.strip() != "")]
    if rv.empty:
        return
    rv = rv.merge(members_table()[["user_id", "nickname", "nationality"]], on="user_id", how="left")
    st.markdown(f"**💬 {t('detail.recent_reviews')}**")
    for _, x in rv.iloc[::-1].head(limit).iterrows():
        nat = f" · {nationality_label(x['nationality'])}" if has(x.get("nationality")) else ""
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


def _store_update_form(r: pd.Series) -> None:
    """메뉴·가격·영업시간 입력.
    - 관리자(팀): '현장 조사'로 저장하면 바로 반영
    - 일반 회원: '회원 제보'로 저장 → 관리자 페이지에서 승인하면 반영
    """
    admin = is_admin()
    st.caption(t("edit.help_admin") if admin else t("edit.help_member"))
    current = parse_menus(r.get("menus"))
    start = pd.DataFrame(current or [("", None)], columns=["menu", "price"])
    with st.form(f"edit_{r['id']}", clear_on_submit=False):
        table = st.data_editor(
            start, num_rows="dynamic", hide_index=True, width="stretch", key=f"edit_tbl_{r['id']}",
            column_config={
                "menu": st.column_config.TextColumn(t("edit.menu"), max_chars=30),
                "price": st.column_config.NumberColumn(t("edit.price"), min_value=500, max_value=100_000,
                                                       step=500, format="%d" + t("common.won")),
            })
        hours = st.text_input(t("edit.hours"), value=str(r["open_hours"]) if has(r.get("open_hours")) else "",
                              placeholder=t("edit.hours_ph"), max_chars=120)
        confirm = st.checkbox(t("edit.confirm_admin") if admin else t("edit.confirm_member"))
        if st.form_submit_button(t("edit.submit"), type="primary"):
            rows = table.dropna(subset=["menu", "price"])
            rows = rows[rows["menu"].astype(str).str.strip() != ""]
            menus = encode_menus(zip(rows["menu"], rows["price"]))
            if not menus and not hours.strip():
                st.error(t("edit.err_empty"))
                return
            if not confirm:
                st.error(t("edit.err_confirm"))
                return
            save_store_update(current_user_id(), r["id"], menus, hours,
                              source="현장 조사" if admin else "회원 제보",
                              status="approved" if admin else "pending")
            st.session_state["toast"] = t("edit.saved_admin") if admin else t("edit.saved_member")
            st.rerun()


def show_pending_toast() -> None:
    if "toast" in st.session_state:
        st.toast(st.session_state.pop("toast"), icon="✅")
