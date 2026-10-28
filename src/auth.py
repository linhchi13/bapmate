"""회원 기능: Google 로그인 + 회원 가입(닉네임) + 탈퇴.

- secrets.toml 에 [auth] 설정이 있으면 Google 로그인(st.login)을 쓴다.
- 없으면 '테스트 로그인'(닉네임만 입력)으로 동작한다. 내 컴퓨터에서 시연할 때만 쓰는 개발용이다.
- 개인정보 보호: 이메일·실명은 저장하지 않는다. Google 계정의 고유번호(sub)를
  SHA-256 으로 바꾼 값(user_id)과, 사용자가 정한 닉네임·국적만 저장한다.
"""
import hashlib

import pandas as pd
import streamlit as st

from src.i18n import NATIONALITY_CODES, nationality_label, t
from src.storage import append_row, delete_user_data, now, read_table, secret_section



def google_enabled() -> bool:
    return secret_section("auth") is not None


def dev_login_allowed() -> bool:
    """테스트 로그인은 내 컴퓨터(localhost)에서만. 인터넷에 배포된 앱에서는 막는다(다른 사람 사칭 방지)."""
    try:
        host = (st.context.headers.get("Host") or "").split(":")[0]
    except Exception:
        host = ""
    return host in ("", "localhost", "127.0.0.1")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def current_user_id() -> str | None:
    """로그인한 사람의 user_id. 로그인하지 않았으면 None."""
    if google_enabled():
        if not st.user.get("is_logged_in", False):
            return None
        return _hash("google:" + str(st.user.get("sub")))
    return st.session_state.get("dev_user_id") if dev_login_allowed() else None


def is_admin() -> bool:
    """관리자 여부.
    - Google 로그인: secrets.toml 의 [admin] emails 목록에 로그인한 Gmail 이 있으면 관리자
      (이메일은 비교에만 쓰고 저장하지 않는다)
    - 내 컴퓨터의 테스트 로그인: 시연을 위해 누구나 관리자
    """
    if google_enabled():
        if not st.user.get("is_logged_in", False):
            return False
        conf = secret_section("admin") or {}
        admins = {str(e).strip().lower() for e in conf.get("emails", [])}
        return str(st.user.get("email", "")).strip().lower() in admins
    return dev_login_allowed() and current_user_id() is not None


def get_member(user_id: str | None) -> dict | None:
    if not user_id:
        return None
    members = read_table("members")
    found = members[members["user_id"] == user_id]
    return found.iloc[-1].to_dict() if len(found) else None


def current_member() -> dict | None:
    return get_member(current_user_id())


def nickname_taken(nickname: str) -> bool:
    return nickname.strip().lower() in set(read_table("members")["nickname"].str.lower())


# ---------------------------------------------------------------- 화면
def login_button(key: str = "login") -> None:
    """로그인 버튼. Google 설정이 없으면 테스트 로그인 입력칸을 보여 준다."""
    if google_enabled():
        if st.button(t("auth.login_google"), key=key, type="primary", width="stretch"):
            st.login()
    elif not dev_login_allowed():
        st.caption(t("auth.not_ready"))
    else:
        with st.form(f"{key}_dev"):
            st.caption(t("auth.dev_notice"))
            name = st.text_input(t("auth.dev_name"), max_chars=20)
            if st.form_submit_button(t("auth.dev_login"), width="stretch") and name.strip():
                st.session_state["dev_user_id"] = _hash("dev:" + name.strip())
                st.rerun()


def logout() -> None:
    st.session_state.pop("dev_user_id", None)
    if google_enabled() and st.user.get("is_logged_in", False):
        st.logout()
    else:
        st.rerun()


def sidebar_account() -> None:
    """사이드바의 로그인 상태 표시."""
    with st.sidebar:
        st.divider()
        member = current_member()
        if member:
            st.markdown(t("auth.hello", name=member["nickname"]))
            if st.button(t("auth.logout"), key="sb_logout", width="stretch"):
                logout()
        elif current_user_id() is None:
            st.caption(t("auth.why_login"))
            login_button("sb_login")


def signup_form() -> None:
    """로그인은 했지만 아직 회원 정보가 없을 때 보여 주는 가입 화면."""
    st.markdown(f'<div class="bm-page-title">{t("auth.signup_title")}</div>'
                f'<div class="bm-page-sub">{t("auth.signup_sub")}</div>', unsafe_allow_html=True)
    with st.form("signup"):
        nickname = st.text_input(t("auth.nickname"), max_chars=20, placeholder=t("auth.nickname_ph"))
        nationality = st.selectbox(t("auth.nationality"), NATIONALITY_CODES, format_func=nationality_label)
        agree = st.checkbox(t("auth.agree"))
        st.caption(t("auth.privacy"))
        if st.form_submit_button(t("auth.signup_btn"), type="primary", width="stretch"):
            nickname = nickname.strip()
            if not (2 <= len(nickname) <= 20):
                st.error(t("auth.err_nickname_len"))
            elif nickname_taken(nickname):
                st.error(t("auth.err_nickname_taken"))
            elif not agree:
                st.error(t("auth.err_agree"))
            else:
                append_row("members", {"user_id": current_user_id(), "nickname": nickname,
                                       "nationality": nationality, "joined_at": now()})
                st.session_state["toast"] = t("auth.welcome", name=nickname)
                st.rerun()
    if st.button(t("auth.cancel")):
        logout()


def withdraw() -> None:
    """탈퇴: 이 사람의 회원 정보·평가·즐겨찾기를 모두 지운다."""
    uid = current_user_id()
    if uid:
        delete_user_data(uid)
    logout()


# ---------------------------------------------------------------- 즐겨찾기 (회원 전용)
def favorite_ids(user_id: str | None) -> list:
    if not user_id:
        return []
    fav = read_table("favorites")
    fav = fav[fav["user_id"] == user_id].drop_duplicates("store_id", keep="last")  # 가게별 마지막 동작
    return fav.loc[fav["action"] == "add", "store_id"].tolist()


def set_favorite(user_id: str, store_id: str, add: bool) -> None:
    append_row("favorites", {"user_id": user_id, "store_id": store_id,
                             "action": "add" if add else "remove", "created_at": now()})


def members_table() -> pd.DataFrame:
    return read_table("members").drop_duplicates("user_id", keep="last")
