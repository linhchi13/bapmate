"""조회수 기록.

- 브라우저 세션 하나 = 조회 1회. 누구인지(이메일·IP 등)는 저장하지 않고 시각·유입 경로·언어·회원 여부만 남긴다.
- 유입 경로(channel)는 주소의 ?src= 값. 홍보 링크마다 다른 값을 붙이면 어느 홍보가 효과 있었는지 알 수 있다.
  예) QR 코드 → ?src=qr, 인스타그램 → ?src=insta, 카카오톡 → ?src=kakao
- 방문할 때마다 저장소(Hugging Face)에 올리면 너무 잦으므로, 서버 메모리에 모았다가 몇 건씩 한꺼번에 저장한다.
"""
import re
import threading
import time

import pandas as pd
import streamlit as st

from src.storage import append_rows, now, read_table

FLUSH_EVERY = 5         # 이만큼 모이면 저장
FLUSH_SECONDS = 180     # 또는 마지막 저장 후 이만큼 지나면 저장
CHANNELS = ["qr", "insta", "kakao", "everytime", "poster", "direct"]  # 홍보 경로 (그 밖의 값은 'etc')


@st.cache_resource
def _buffer() -> dict:
    """아직 저장하지 않은 방문 기록 (서버 하나에서 모든 사용자가 같이 씀)."""
    return {"rows": [], "last": time.time(), "lock": threading.Lock()}


def _channel() -> str:
    src = str(st.query_params.get("src", "direct")).lower()
    if not re.fullmatch(r"[a-z0-9_-]{1,20}", src):
        return "etc"
    return src if src in CHANNELS else "etc"


def track_visit(lang: str, member: bool) -> None:
    """이 세션의 첫 화면에서 한 번만 기록한다."""
    if st.session_state.get("_visit_logged"):
        return
    st.session_state["_visit_logged"] = True
    buf = _buffer()
    with buf["lock"]:
        buf["rows"].append({"visited_at": now(), "channel": _channel(), "lang": lang, "member": "y" if member else "n"})
        due = len(buf["rows"]) >= FLUSH_EVERY or time.time() - buf["last"] > FLUSH_SECONDS
    if due:
        flush()


def flush() -> None:
    buf = _buffer()
    with buf["lock"]:
        rows, buf["rows"], buf["last"] = buf["rows"], [], time.time()
    if not rows:
        return
    try:
        append_rows("visits", rows)
    except Exception:  # 저장에 실패해도 화면은 계속 보여 주고, 다음 기회에 다시 저장
        with buf["lock"]:
            buf["rows"] = rows + buf["rows"]


def visits() -> pd.DataFrame:
    """저장된 기록 + 아직 저장 전인 기록."""
    saved = read_table("visits")
    pending = pd.DataFrame(_buffer()["rows"], columns=saved.columns)
    df = pd.concat([saved, pending], ignore_index=True)
    df["date"] = df["visited_at"].str[:10]
    return df
