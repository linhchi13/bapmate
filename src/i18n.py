"""화면 문구 관리.

화면에 보이는 글자는 코드에 직접 쓰지 않고 locales/<언어>.json 에서 불러온다.
나중에 locales/vi.json, locales/en.json 을 같은 키로 만들고 LANG 만 바꾸면 다국어가 된다.
"""
import json
from functools import lru_cache

from src.config import ROOT

LANG = "ko"


@lru_cache(maxsize=8)
def _load(lang: str, mtime: float) -> dict:  # mtime: 파일이 바뀌면 다시 읽기 위한 값
    return json.loads((ROOT / "locales" / f"{lang}.json").read_text(encoding="utf-8"))


def t(key: str, **kwargs) -> str:
    """t("common.walk", min=5) → '도보 약 5분'. 키가 없으면 키 이름을 그대로 보여 준다."""
    path = ROOT / "locales" / f"{LANG}.json"
    text = _load(LANG, path.stat().st_mtime).get(key, key)
    return text.format(**kwargs) if kwargs else text


def cuisine_label(key: str) -> str:
    return t(f"cuisine.{key}")
