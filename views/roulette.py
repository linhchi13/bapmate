"""룰렛 '오늘 뭐 먹지?': 먹고 싶은 음식을 2~5개 고르고 돌리면 하나를 뽑아 주고, 그 음식을 파는 가까운 가게를 보여 준다."""
import base64
import math
import random
import time

import streamlit as st

from src.config import DISHES, ROULETTE_MAX
from src.data import get_data
from src.i18n import lang_key, t
from src.ui import page_header, render_grid

COLORS = ["#F26B3A", "#F59F00", "#2B8A3E", "#1971C2", "#AE3EC9"]
SPIN_SECONDS = 4

df = get_data()
counts = {k: int(df["category_sub"].isin(subs).sum()) for k, (_, subs) in DISHES.items()}
dishes = [k for k in DISHES if counts[k] > 0]  # 학교 주변에 실제로 파는 가게가 있는 음식만


def label(key: str) -> str:
    return f"{DISHES[key][0]} {t(f'dish.{key}')}"


def wheel_svg(items: list) -> str:
    """룰렛 판 그림(SVG). 0번 칸이 12시 방향에서 시작해 시계 방향으로 놓인다."""
    size, r = 320, 150
    c = size / 2
    seg = 360 / len(items)
    parts = []
    for i, key in enumerate(items):
        a0, a1 = math.radians(i * seg), math.radians((i + 1) * seg)
        x0, y0 = c + r * math.sin(a0), c - r * math.cos(a0)
        x1, y1 = c + r * math.sin(a1), c - r * math.cos(a1)
        large = 1 if seg > 180 else 0
        parts.append(f'<path d="M{c},{c} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" '
                     f'fill="{COLORS[i % len(COLORS)]}" stroke="#fff" stroke-width="3"/>')
        mid = (i + 0.5) * seg
        # 왼쪽 절반의 글자는 뒤집혀 보이므로 180도 돌려서 바로 읽히게 한다
        rot, x = (mid - 90, c + r * 0.58) if mid <= 180 else (mid + 90, c - r * 0.58)
        parts.append(f'<g transform="rotate({rot:.1f} {c} {c})"><text x="{x:.1f}" y="{c}" '
                     f'text-anchor="middle" dominant-baseline="middle" font-size="17" font-weight="700" '
                     f'fill="#fff" font-family="sans-serif">{label(key)}</text></g>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="26" fill="#fff" stroke="#F26B3A" stroke-width="4"/>')
    parts.append(f'<text x="{c}" y="{c + 1}" text-anchor="middle" dominant-baseline="middle" font-size="22">🍚</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(parts)}</svg>'
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def show_wheel(items: list, angle: float, nonce: str, animate: bool) -> None:
    """룰렛 판을 angle 만큼(시계 방향) 돌린 모습. animate 면 SPIN_SECONDS 동안 돌아가는 애니메이션."""
    anim = (f"animation: bm-spin-{nonce} {SPIN_SECONDS}s cubic-bezier(.15,.65,.1,1) forwards;" if animate
            else f"transform: rotate({angle:.1f}deg);")
    st.markdown(f"""
<style>
@keyframes bm-spin-{nonce} {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate({angle:.1f}deg); }} }}
.bm-wheel-box {{ position: relative; width: 320px; max-width: 100%; margin: 10px auto 4px; }}
.bm-wheel-box img {{ width: 100%; display: block; {anim} }}
.bm-pointer {{ position: absolute; top: -6px; left: 50%; transform: translateX(-50%); z-index: 2;
  width: 0; height: 0; border-left: 16px solid transparent; border-right: 16px solid transparent;
  border-top: 30px solid #3B2A20; filter: drop-shadow(0 2px 2px rgba(0,0,0,.25)); }}
</style>
<div class="bm-wheel-box"><div class="bm-pointer"></div><img src="{wheel_svg(items)}" alt=""></div>
""", unsafe_allow_html=True)


page_header(f"🎡 {t('roulette.title')}", t("roulette.subtitle", n=ROULETTE_MAX))

# ---- ① 음식 고르기 (최대 ROULETTE_MAX 개)
pick_key = lang_key("roulette_pick")
if st.button(f"🎲 {t('roulette.random_pick', n=ROULETTE_MAX)}"):
    st.session_state[pick_key] = random.sample(dishes, min(ROULETTE_MAX, len(dishes)))
picked = st.pills(t("roulette.pick"), dishes, selection_mode="multi", key=pick_key,
                  format_func=lambda k: f"{label(k)} · {t('roulette.stores', n=counts[k])}")
too_many = len(picked) > ROULETTE_MAX
if too_many:
    st.warning(t("roulette.too_many", n=ROULETTE_MAX))
elif len(picked) < 2:
    st.caption(t("roulette.need_two"))

# ---- ② 돌리기: 결과는 서버에서 먼저 뽑고, 판은 그 칸이 12시(바늘)에 오도록 돌린다
if st.button(f"🎡 {t('roulette.spin')}", type="primary", width="stretch", disabled=too_many or len(picked) < 2):
    winner = random.randrange(len(picked))
    seg = 360 / len(picked)
    jitter = random.uniform(-0.3, 0.3) * seg  # 칸 한가운데만 걸리지 않게
    st.session_state["roulette"] = {"items": list(picked), "winner": picked[winner], "nonce": f"{time.time_ns()}",
                                    "angle": 360 * 6 - (winner + 0.5) * seg + jitter, "animate": True}

spin = st.session_state.get("roulette")
if spin and spin["items"] == list(picked):
    show_wheel(spin["items"], spin["angle"], spin["nonce"], spin["animate"])
    if spin["animate"]:  # 판이 다 돈 뒤에 결과를 보여 준다 (다시 그릴 때는 애니메이션 없이)
        spin["animate"] = False
        time.sleep(SPIN_SECONDS + 0.3)
    key = spin["winner"]
    st.markdown(f'<div style="text-align:center;font-size:1.7rem;font-weight:800;margin:8px 0;">'
                f'{t("roulette.result", dish=label(key))}</div>', unsafe_allow_html=True)
    if spin.get("celebrate", True):  # 풍선은 돌린 직후 한 번만
        st.balloons()
        spin["celebrate"] = False

    stores = df[df["category_sub"].isin(DISHES[key][1])].sort_values("distance_m")
    st.markdown(f"#### 📍 {t('roulette.nearby', dish=t(f'dish.{key}'), n=len(stores))}")
    render_grid(stores, "roulette", page_size=6, reset_on=spin["nonce"])
elif 2 <= len(picked) <= ROULETTE_MAX:  # 돌리기 전: 고른 음식으로 만든 판 미리 보기
    show_wheel(list(picked), 0, "idle", False)
