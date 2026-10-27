"""과기대 밥친구 (SeoulTech BapMate) — 서울과기대 유학생을 위한 맛집 탐험 웹

실행:  streamlit run app.py
"""
import streamlit as st

from src.auth import current_member, current_user_id, is_admin, sidebar_account, signup_form
from src.data import DataError, load_restaurants
from src.i18n import t
from src.ui import inject_css, show_pending_toast

st.set_page_config(page_title=f"{t('app.name')} · {t('app.name_en')}", page_icon="🍚", layout="wide")
inject_css()

# 데이터 파일 검사: 없거나 형식이 틀리면 안내를 보여 주고 멈춘다
try:
    load_restaurants()
except DataError as e:
    st.error(t("data.missing_title") if str(e) == "missing" else t("data.bad_columns", cols=e))
    st.write(t("data.missing_body"))
    st.code("python scripts/01_download_public_data.py\n"
            "python scripts/02_fetch_osm.py\n"
            "python scripts/03_build_dataset.py", language="bash")
    st.stop()

# 메뉴: 3개 묶음. (about 페이지 주소 /about 은 Google 에 개인정보 처리방침 링크로 등록되어 있으니 바꾸지 말 것)
pages = {
    t("nav.section_food"): [
        st.Page("views/home.py", title=t("nav.home"), icon="🔎", default=True),
        st.Page("views/themes.py", title=t("nav.themes"), icon="📂"),
    ],
    t("nav.section_me"): [
        st.Page("views/mypage.py", title=t("nav.mypage"), icon="👤"),
    ],
    t("nav.section_info"): [
        st.Page("views/stats.py", title=t("nav.stats"), icon="📊"),
        st.Page("views/about.py", title=t("nav.about"), icon="ℹ️"),
    ],
}
if is_admin():  # 관리자에게만 메뉴가 보인다
    pages[t("nav.section_admin")] = [st.Page("views/admin.py", title=t("nav.admin"), icon="🛠️")]
nav = st.navigation(pages)
st.sidebar.markdown(f"### 🍚 {t('app.name')}\n{t('app.name_en')}")
st.sidebar.caption(t("app.tagline"))
sidebar_account()
show_pending_toast()

# 로그인은 했지만 아직 가입(닉네임 등록)을 안 했으면 가입 화면부터
if current_user_id() and not current_member():
    signup_form()
    st.stop()

nav.run()
