"""화면 문구 관리 (다국어).

화면에 보이는 글자는 코드에 직접 쓰지 않고 locales/<언어>.json 에서 불러온다.
- 지원 언어는 LANGUAGES 에 있고, 사용자가 화면 위쪽에서 고른 언어가 st.session_state["lang"] 에 저장된다.
- 번역 파일에 없는 문구는 한국어(ko.json)로 대신 보여 준다.
- 새 언어 추가: locales/<코드>.json 을 만들고 LANGUAGES 에 한 줄 추가하면 끝.
"""
import json
from functools import lru_cache

import streamlit as st

from src.config import ROOT

DEFAULT_LANG = "ko"
LANGUAGES = {  # 코드 → 언어 전환 버튼에 보일 이름 (국기 이모지는 Windows 에서 글자로 보여서 쓰지 않음)
    "ko": "한국어",
    "en": "EN",
}


@lru_cache(maxsize=32)
def _load(lang: str, mtime: float) -> dict:  # mtime: 파일이 바뀌면 다시 읽기 위한 값
    return json.loads((ROOT / "locales" / f"{lang}.json").read_text(encoding="utf-8"))


def _strings(lang: str) -> dict:
    path = ROOT / "locales" / f"{lang}.json"
    if not path.exists():
        return {}
    return _load(lang, path.stat().st_mtime)


def current_lang() -> str:
    """지금 화면 언어. (사용자 선택 → 주소의 ?lang= → 기본 한국어)"""
    try:
        lang = st.session_state.get("lang") or st.query_params.get("lang", DEFAULT_LANG)
    except Exception:  # Streamlit 밖(스크립트)에서 부를 때
        lang = DEFAULT_LANG
    return lang if lang in LANGUAGES else DEFAULT_LANG


def t(key: str, **kwargs) -> str:
    """t("common.walk", min=5) → '도보 약 5분'. 현재 언어에 없으면 한국어, 그것도 없으면 키 이름."""
    text = _strings(current_lang()).get(key) or _strings(DEFAULT_LANG).get(key, key)
    return text.format(**kwargs) if kwargs else text


def lang_key(name: str) -> str:
    """번역된 글자를 보여 주는 선택 위젯의 key. 언어가 바뀌면 key 도 바뀌어 선택이 깔끔하게 초기화된다."""
    return f"{name}_{current_lang()}"


def cuisine_label(key: str) -> str:
    return t(f"cuisine.{key}")


# ---------------------------------------------------------------- 데이터 값(한국어) → 화면 표시
STATION_KEYS = {"공릉역": "gongneung", "태릉입구역": "taereung", "하계역": "hagye",
                "화랑대역": "hwarangdae", "중계역": "junggye", "먹골역": "meokgol"}


def area_label(area: str) -> str:
    """데이터의 구역 값('교내', '학교 앞', '공릉역 주변', '기타')을 현재 언어로."""
    area = str(area)
    if area == "교내":
        return t("area.campus")
    if area == "학교 앞":
        return t("area.front")
    if area.endswith(" 주변"):
        station = area.removesuffix(" 주변")
        return t("area.near", station=t(f"station.{STATION_KEYS.get(station, station)}"))
    return t("area.etc")


SOURCE_KEYS = [("착한가격업소(행정안전부)", "src.good_price"), ("현장 조사", "src.field"), ("회원 제보", "src.member"),
               ("학생 제보", "src.student"), ("웹 조사", "src.web"), ("다이닝코드 블로그 후기", "src.diningcode_blog"),
               ("다이닝코드", "src.diningcode"), ("테이블링", "src.tabling")]


def source_label(text) -> str:
    """'웹 조사: 다이닝코드(2026-10-28)' 같은 출처 문구의 한국어 부분을 현재 언어로 바꾼다."""
    text = str(text)
    if current_lang() == DEFAULT_LANG:
        return text
    for ko, key in SOURCE_KEYS:
        text = text.replace(ko, t(key))
    return text


NATIONALITY_CODES = ["", "vn", "cn", "mn", "uz", "kz", "ru", "mm", "id", "np", "jp", "us", "fr", "kr", "etc"]


def nationality_label(code) -> str:
    code = str(code or "")
    return t(f"nat.{code}") if code else t("auth.no_answer")
