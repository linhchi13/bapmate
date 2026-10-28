"""과기대 밥친구 전용 음식 일러스트 (SVG 로 직접 그림 → 저작권 걱정 없음).

- 가게 카드에 '예시 이미지'로 쓰인다. 실제 가게 음식 사진이 아니다.
- 음식 종류(cuisine) + 세부 업종(category_sub)에 맞는 그림을 고른다.
- 모든 그림은 640×320 크기, 같은 스타일(파스텔 배경 + 귀여운 얼굴)로 통일했다.
"""
import base64
from functools import lru_cache

INK = "#3B2A20"


# ---------------------------------------------------------------- 공통 부품
def face(cx, cy, s=1.0):
    """눈 2개 + 웃는 입 + 볼터치."""
    return (
        f'<ellipse cx="{cx - 36 * s}" cy="{cy + 10 * s}" rx="{10 * s}" ry="{5.5 * s}" fill="#FF8FA3" opacity=".6"/>'
        f'<ellipse cx="{cx + 36 * s}" cy="{cy + 10 * s}" rx="{10 * s}" ry="{5.5 * s}" fill="#FF8FA3" opacity=".6"/>'
        f'<circle cx="{cx - 20 * s}" cy="{cy}" r="{7 * s}" fill="{INK}"/>'
        f'<circle cx="{cx + 20 * s}" cy="{cy}" r="{7 * s}" fill="{INK}"/>'
        f'<circle cx="{cx - 17.5 * s}" cy="{cy - 2.5 * s}" r="{2.4 * s}" fill="#fff"/>'
        f'<circle cx="{cx + 22.5 * s}" cy="{cy - 2.5 * s}" r="{2.4 * s}" fill="#fff"/>'
        f'<path d="M{cx - 8 * s} {cy + 9 * s} Q{cx} {cy + 18 * s} {cx + 8 * s} {cy + 9 * s}" '
        f'stroke="{INK}" stroke-width="{3.2 * s}" fill="none" stroke-linecap="round"/>'
    )


def bowl(cx, top, w, depth, body, inside, rim_ry=None):
    """옆에서 본 그릇: 받침 + 몸통 + 안쪽(음식 면)."""
    rim_ry = rim_ry or w * 0.1
    x1, x2 = cx - w / 2, cx + w / 2
    return (
        f'<rect x="{cx - w * .17}" y="{top + depth - 8}" width="{w * .34}" height="18" rx="7" fill="{body}" opacity=".85"/>'
        f'<path d="M{x1} {top} A{w / 2} {depth} 0 0 0 {x2} {top} Z" fill="{body}"/>'
        f'<ellipse cx="{cx}" cy="{top}" rx="{w / 2}" ry="{rim_ry}" fill="{inside}" stroke="{body}" stroke-width="7"/>'
    )


def steam(xs, y, color="#fff"):
    return "".join(
        f'<path d="M{x} {y} c-10 -14 10 -22 0 -36 c-10 -14 10 -22 0 -36" stroke="{color}" stroke-width="7" '
        f'fill="none" stroke-linecap="round" opacity=".85"/>' for x in xs)


def chopsticks(x, y):
    return (f'<rect x="{x}" y="{y}" width="12" height="190" rx="5" fill="#C8955C" transform="rotate(28 {x} {y})"/>'
            f'<rect x="{x + 22}" y="{y - 4}" width="12" height="190" rx="5" fill="#B07A45" transform="rotate(34 {x + 22} {y - 4})"/>')


def frame(c1, c2, body):
    """640×320 배경(그라데이션 + 장식 점) 안에 그림을 넣는다."""
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity=".35"/>'
                   for x, y, r in [(60, 60, 18), (590, 70, 12), (95, 270, 9), (560, 260, 20), (520, 40, 6), (140, 30, 7)])
    sparkles = "".join(
        f'<path d="M{x} {y - 10} L{x + 3} {y - 3} L{x + 10} {y} L{x + 3} {y + 3} L{x} {y + 10} L{x - 3} {y + 3} '
        f'L{x - 10} {y} L{x - 3} {y - 3} Z" fill="#fff" opacity=".8"/>' for x, y in [(110, 120), (535, 150), (480, 285)])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 320" width="640" height="320">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<rect width="640" height="320" fill="url(#g)"/>{dots}{sparkles}'
            f'<ellipse cx="320" cy="292" rx="170" ry="16" fill="#000" opacity=".08"/>{body}</svg>')


# ---------------------------------------------------------------- 그림들
def bibimbap():
    top = 140
    toppings = (
        '<ellipse cx="258" cy="140" rx="34" ry="14" fill="#F08C00"/>'      # 당근
        '<ellipse cx="300" cy="126" rx="30" ry="12" fill="#2F9E44"/>'      # 시금치
        '<ellipse cx="350" cy="126" rx="30" ry="12" fill="#8B5A2B"/>'      # 고기
        '<ellipse cx="388" cy="142" rx="30" ry="12" fill="#FCC419"/>'      # 콩나물
        '<ellipse cx="322" cy="150" rx="34" ry="13" fill="#E03131" opacity=".9"/>'  # 고추장
        '<ellipse cx="322" cy="136" rx="26" ry="11" fill="#fff"/><circle cx="322" cy="135" r="9" fill="#FAB005"/>'
    )
    return frame("#FFE8CC", "#FFC9A0", bowl(320, top, 270, 120, "#5C5F66", "#FFF8E7") + toppings + face(320, 205))


def stew():
    pot = ('<rect x="170" y="128" width="40" height="18" rx="9" fill="#A61E1E"/>'
           '<rect x="430" y="128" width="40" height="18" rx="9" fill="#A61E1E"/>'
           '<path d="M190 140 L450 140 L436 262 Q320 284 204 262 Z" fill="#C92A2A"/>'
           '<ellipse cx="320" cy="140" rx="130" ry="24" fill="#F03E3E" stroke="#A61E1E" stroke-width="7"/>'
           '<rect x="262" y="128" width="26" height="20" rx="4" fill="#fff"/>'
           '<rect x="340" y="132" width="26" height="20" rx="4" fill="#fff"/>'
           '<circle cx="305" cy="148" r="6" fill="#51CF66"/><circle cx="380" cy="142" r="5" fill="#51CF66"/>'
           '<circle cx="240" cy="142" r="5" fill="#51CF66"/>')
    return frame("#FFE3E3", "#FFB8A8", steam([270, 320, 370], 112) + pot + face(320, 205))


def noodle():
    noodles = "".join(f'<path d="M{x} 130 q10 -10 20 0 t20 0 t20 0" stroke="#FFF3BF" stroke-width="6" fill="none" '
                      f'stroke-linecap="round"/>' for x in (232, 262, 300, 338))
    extra = ('<ellipse cx="380" cy="138" rx="22" ry="12" fill="#fff"/><circle cx="380" cy="137" r="8" fill="#FAB005"/>'
             '<circle cx="270" cy="146" r="5" fill="#51CF66"/><circle cx="300" cy="150" r="5" fill="#51CF66"/>')
    body = bowl(320, 140, 270, 120, "#F8F9FA", "#F4D19B") + noodles + extra
    body += '<rect x="196" y="190" width="248" height="12" fill="#4DABF7" opacity=".8"/>'  # 그릇 무늬
    return frame("#E7F5FF", "#B9E0FF", chopsticks(410, 40) + body + face(320, 224))


def bbq():
    grill = ('<ellipse cx="320" cy="180" rx="190" ry="92" fill="#343A40"/>'
             '<ellipse cx="320" cy="172" rx="172" ry="80" fill="#495057"/>'
             + "".join(f'<line x1="{x}" y1="104" x2="{x}" y2="240" stroke="#868E96" stroke-width="4"/>'
                       for x in range(190, 460, 30)))
    meat = "".join(
        f'<g transform="rotate(-8 {x} {y})"><rect x="{x - 48}" y="{y - 16}" width="96" height="32" rx="12" fill="#F7A399"/>'
        f'<rect x="{x - 48}" y="{y - 4}" width="96" height="7" fill="#FFF0EC"/>'
        f'<rect x="{x - 40}" y="{y - 14}" width="10" height="28" fill="#C2410C" opacity=".5"/></g>'
        for x, y in [(250, 150), (390, 140), (330, 200)])
    garlic = '<circle cx="250" cy="210" r="10" fill="#FFF9DB"/><circle cx="420" cy="205" r="10" fill="#FFF9DB"/>'
    return frame("#FFF0F6", "#FFC9DE", steam([230, 410], 92) + grill + meat + garlic + face(250, 152, .7))


def tteokbokki():
    plate = ('<ellipse cx="320" cy="190" rx="200" ry="78" fill="#fff"/>'
             '<ellipse cx="320" cy="182" rx="170" ry="62" fill="#E8590C"/>')
    cakes = "".join(f'<rect x="{x}" y="{y}" width="70" height="22" rx="11" fill="#FFF4E6" stroke="#D9480F" '
                    f'stroke-width="3" transform="rotate({a} {x + 35} {y + 11})"/>'
                    for x, y, a in [(190, 160, -12), (250, 190, 8), (380, 160, 14), (300, 140, -4), (360, 200, -10)])
    egg = '<ellipse cx="420" cy="182" rx="36" ry="30" fill="#fff"/>'
    return frame("#FFF4E6", "#FFC078", plate + cakes + egg + face(420, 178, .62))


def chicken():
    def stick(x, y, a):
        """닭다리: 뼈가 위로 비스듬히 나오도록 회전."""
        return (f'<g transform="rotate({a} {x} {y})">'
                f'<rect x="{x - 10}" y="{y - 110}" width="20" height="70" rx="9" fill="#FFF8F0"/>'
                f'<circle cx="{x - 13}" cy="{y - 112}" r="14" fill="#FFF8F0"/><circle cx="{x + 13}" cy="{y - 112}" r="14" fill="#FFF8F0"/>'
                f'<ellipse cx="{x}" cy="{y}" rx="64" ry="72" fill="#E8890C"/>'
                f'<ellipse cx="{x - 20}" cy="{y - 26}" rx="18" ry="11" fill="#FFC078" opacity=".8"/></g>')
    box = ('<path d="M160 214 L480 214 L462 290 L178 290 Z" fill="#F03E3E"/>'
           '<rect x="154" y="206" width="332" height="20" rx="6" fill="#C92A2A"/>'
           '<path d="M240 240 h160" stroke="#fff" stroke-width="10" stroke-linecap="round" opacity=".9"/>')
    return frame("#FFF9DB", "#FFD8A8", stick(250, 178, -22) + stick(390, 178, 22) + box + face(390, 168, .8))


def burger():
    b = ('<path d="M190 150 Q320 40 450 150 Z" fill="#F59F00"/>'
         + "".join(f'<ellipse cx="{x}" cy="{y}" rx="6" ry="3.5" fill="#FFF3BF"/>' for x, y in
                   [(270, 110), (320, 92), (370, 110), (300, 128), (350, 128), (240, 135), (400, 135)])
         + '<path d="M180 152 q20 18 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0" fill="#51CF66" stroke="#51CF66" stroke-width="8"/>'
           '<path d="M190 166 L450 166 L410 196 L320 176 L230 196 Z" fill="#FCC419"/>'
           '<rect x="186" y="170" width="268" height="40" rx="18" fill="#7B4A2A"/>'
           '<rect x="190" y="210" width="260" height="56" rx="20" fill="#F59F00"/>')
    fries = ('<g transform="rotate(10 520 220)">'
             + "".join(f'<rect x="{x}" y="{170 + (x % 3) * 6}" width="12" height="60" rx="3" fill="#FFD43B"/>'
                       for x in range(492, 552, 13))
             + '<path d="M484 210 L560 210 L550 290 L494 290 Z" fill="#E03131"/></g>')
    return frame("#FFF3BF", "#FFD8A8", fries + b + face(320, 236, .8))


def pizza():
    s = ('<path d="M190 90 L470 90 L330 290 Z" fill="#FFD43B"/>'
         '<path d="M180 80 Q330 50 480 80 L470 102 Q330 74 190 102 Z" fill="#D9822B"/>'
         '<circle cx="270" cy="128" r="18" fill="#E03131"/><circle cx="390" cy="130" r="18" fill="#E03131"/>'
         '<circle cx="330" cy="210" r="15" fill="#E03131"/><circle cx="300" cy="170" r="6" fill="#343A40"/>'
         '<circle cx="372" cy="182" r="6" fill="#343A40"/><path d="M350 112 l14 8 l-14 8 z" fill="#40C057"/>')
    return frame("#FFF5F5", "#FFC9C9", s + face(330, 160, .75))


def bread():
    loaf = ('<path d="M200 260 L200 170 Q200 100 300 100 L340 100 Q440 100 440 170 L440 260 Z" fill="#E8A24A"/>'
            '<path d="M214 170 Q214 116 300 116 L340 116 Q426 116 426 170 Z" fill="#F5C77E"/>'
            + "".join(f'<path d="M{x} 120 q16 14 32 0" stroke="#C97B2A" stroke-width="5" fill="none" stroke-linecap="round"/>'
                      for x in (262, 304, 346)))
    sprinkles = "".join(f'<rect x="{x}" y="{y}" width="10" height="4" rx="2" fill="{c}" transform="rotate({a} {x} {y})"/>'
                        for x, y, a, c in [(476, 196, 30, "#4DABF7"), (510, 186, -20, "#FFD43B"), (530, 214, 60, "#69DB7C"),
                                           (470, 228, -40, "#fff"), (500, 240, 10, "#4DABF7"), (538, 240, -30, "#FFD43B")])
    donut = ('<circle cx="505" cy="222" r="52" fill="#E8A24A"/>'
             '<path d="M455 214 a50 46 0 0 1 100 0 q-8 18 -18 8 q-10 16 -20 4 q-12 16 -24 2 q-12 14 -22 0 q-10 12 -16 -14z" fill="#F783AC"/>'
             + sprinkles + '<circle cx="505" cy="222" r="16" fill="#FFE066"/>')
    return frame("#FFF9DB", "#FFE066", loaf + donut + face(320, 200))


def sushi():
    board = '<rect x="140" y="200" width="360" height="40" rx="10" fill="#C8955C"/><rect x="170" y="240" width="40" height="22" fill="#A0703F"/><rect x="430" y="240" width="40" height="22" fill="#A0703F"/>'

    def nigiri(x, fish, stripe):
        return (f'<rect x="{x - 50}" y="160" width="100" height="44" rx="20" fill="#fff"/>'
                f'<path d="M{x - 58} 168 Q{x} 120 {x + 58} 168 Q{x} 150 {x - 58} 168 Z" fill="{fish}"/>'
                f'<path d="M{x - 30} 152 l12 -10 M{x - 6} 146 l12 -10 M{x + 18} 150 l12 -10" stroke="{stripe}" stroke-width="4" stroke-linecap="round"/>')
    return frame("#E6FCF5", "#A5E9D6", board + nigiri(220, "#FF8A5B", "#FFD8C8") + nigiri(330, "#FF8A5B", "#FFD8C8")
                 + nigiri(440, "#E03131", "#FFA8A8") + face(330, 180, .65))


def jjajang():
    body = bowl(320, 140, 270, 120, "#F8F9FA", "#3D2817")
    top = ('<path d="M240 140 q15 -12 30 0 t30 0 t30 0 t30 0 t30 0" stroke="#FFF3BF" stroke-width="5" fill="none"/>'
           + "".join(f'<rect x="{x}" y="118" width="40" height="6" rx="3" fill="#69DB7C" transform="rotate({a} {x} 118)"/>'
                     for x, a in [(300, -20), (318, -10), (336, 0), (354, 10)])
           + '<ellipse cx="272" cy="128" rx="20" ry="11" fill="#fff"/><circle cx="272" cy="127" r="7" fill="#FAB005"/>')
    pattern = '<path d="M210 192 h220" stroke="#E03131" stroke-width="8" stroke-dasharray="18 10"/>'
    return frame("#F3F0FF", "#D0BFFF", chopsticks(410, 40) + body + top + pattern + face(320, 226))


def pho():
    body = bowl(320, 140, 270, 120, "#fff", "#F2C46B")
    top = ('<ellipse cx="268" cy="136" rx="30" ry="12" fill="#C2785B"/><ellipse cx="320" cy="128" rx="30" ry="12" fill="#B5694D"/>'
           '<path d="M350 132 q12 -16 24 0 q12 -16 24 0" fill="#40C057"/><path d="M228 140 q10 -14 20 0" fill="#40C057"/>'
           '<circle cx="300" cy="150" r="7" fill="none" stroke="#E03131" stroke-width="4"/>'
           '<path d="M380 150 a24 24 0 0 1 40 0 z" fill="#94D82D"/>')
    pattern = '<path d="M206 186 h228" stroke="#E03131" stroke-width="6"/><path d="M210 198 h220" stroke="#E03131" stroke-width="3"/>'
    return frame("#EBFBEE", "#B2F2BB", steam([280, 360], 104, "#fff") + chopsticks(410, 40) + body + top + pattern + face(320, 228))


def curry():
    plate = '<ellipse cx="320" cy="200" rx="210" ry="74" fill="#fff"/><ellipse cx="320" cy="196" rx="186" ry="60" fill="#F8F9FA"/>'
    rice = '<path d="M180 210 Q190 120 300 130 Q330 170 320 238 Q230 246 180 210 Z" fill="#fff" stroke="#E9ECEF" stroke-width="3"/>'
    sauce = ('<path d="M300 130 Q420 120 460 196 Q430 246 320 238 Q330 170 300 130 Z" fill="#F59F00"/>'
             '<rect x="360" y="170" width="26" height="22" rx="6" fill="#E8590C"/><rect x="410" y="190" width="22" height="20" rx="6" fill="#FFF3BF"/>'
             '<circle cx="380" cy="214" r="8" fill="#51CF66"/>')
    return frame("#FFF9DB", "#FFD43B", plate + rice + sauce + face(240, 186, .7))


def pasta():
    plate = '<ellipse cx="320" cy="196" rx="210" ry="80" fill="#fff"/><ellipse cx="320" cy="192" rx="170" ry="60" fill="#F8F9FA"/>'
    swirl = "".join(f'<ellipse cx="320" cy="180" rx="{r}" ry="{r * .55}" fill="none" stroke="#FFD43B" stroke-width="9"/>'
                    for r in (110, 84, 58, 32))
    top = ('<circle cx="320" cy="168" r="30" fill="#E03131"/><circle cx="270" cy="200" r="13" fill="#C92A2A"/>'
           '<circle cx="380" cy="204" r="13" fill="#C92A2A"/><path d="M330 140 q22 -16 34 4 q-20 10 -34 -4z" fill="#40C057"/>')
    fork = '<g transform="rotate(30 480 120)"><rect x="474" y="80" width="12" height="150" rx="5" fill="#ADB5BD"/><rect x="462" y="60" width="36" height="34" rx="6" fill="#ADB5BD"/></g>'
    return frame("#FFF0F6", "#FCC2D7", fork + plate + swirl + top + face(320, 168, .55))


def tray():
    t = ('<rect x="150" y="100" width="340" height="180" rx="24" fill="#63E6BE"/>'
         '<rect x="166" y="116" width="150" height="70" rx="14" fill="#fff"/>'
         '<rect x="326" y="116" width="148" height="70" rx="14" fill="#fff"/>'
         '<rect x="166" y="196" width="96" height="70" rx="14" fill="#fff"/>'
         '<rect x="272" y="196" width="96" height="70" rx="14" fill="#fff"/>'
         '<rect x="378" y="196" width="96" height="70" rx="14" fill="#fff"/>'
         '<ellipse cx="240" cy="150" rx="56" ry="24" fill="#F8F9FA" stroke="#E9ECEF" stroke-width="3"/>'
         '<ellipse cx="400" cy="150" rx="56" ry="24" fill="#FF8787"/>'
         '<circle cx="200" cy="230" r="14" fill="#69DB7C"/><circle cx="228" cy="236" r="12" fill="#51CF66"/>'
         '<rect x="296" y="218" width="48" height="26" rx="8" fill="#FFA94D"/>'
         '<circle cx="410" cy="226" r="12" fill="#FFD43B"/><circle cx="440" cy="238" r="12" fill="#FFD43B"/>')
    return frame("#E6FCF5", "#96F2D7", t + face(240, 146, .55))


def coffee():
    c = ('<ellipse cx="320" cy="262" rx="150" ry="24" fill="#fff"/><ellipse cx="320" cy="256" rx="110" ry="14" fill="#E9ECEF"/>'
         '<path d="M420 160 a40 40 0 1 1 0 64" stroke="#fff" stroke-width="18" fill="none"/>'
         '<path d="M210 140 L430 140 L410 240 Q320 270 230 240 Z" fill="#fff"/>'
         '<ellipse cx="320" cy="140" rx="110" ry="24" fill="#A47148" stroke="#fff" stroke-width="8"/>'
         '<path d="M320 152 c-24 -14 -24 -30 -8 -30 c6 0 8 6 8 6 c0 0 2 -6 8 -6 c16 0 16 16 -8 30 z" fill="#FFF8F0"/>')
    return frame("#F8F0E3", "#E6CBA8", steam([290, 350], 104) + c + face(320, 196))


def cloche():
    c = ('<ellipse cx="320" cy="250" rx="190" ry="26" fill="#fff"/>'
         '<path d="M170 246 Q170 110 320 110 Q470 110 470 246 Z" fill="#CED4DA"/>'
         '<path d="M200 220 Q200 140 290 126" stroke="#fff" stroke-width="12" fill="none" stroke-linecap="round" opacity=".8"/>'
         '<circle cx="320" cy="100" r="16" fill="#ADB5BD"/>')
    return frame("#F1F3F5", "#D0EBFF", c + face(320, 196))


# ---------------------------------------------------------------- 홈 배너 마스코트 '밥친구'
def mascot_svg() -> str:
    """밥그릇 마스코트 + 주변에 떠 있는 음식들 (배경 투명, 420×260)."""
    grains = "".join(f'<ellipse cx="{x}" cy="{y}" rx="5" ry="3" fill="#F1E9D8" transform="rotate({a} {x} {y})"/>'
                     for x, y, a in [(170, 100, 20), (205, 88, -15), (245, 98, 35), (190, 122, -30), (232, 120, 10),
                                     (262, 128, -20), (152, 130, 15)])
    rice = ('<path d="M108 150 Q110 66 210 66 Q310 66 312 150 Z" fill="#FFFDF7"/>' + grains)
    bowl_body = ('<path d="M100 150 A110 100 0 0 0 320 150 Z" fill="#fff" stroke="#F5C9AE" stroke-width="3"/>'
                 '<path d="M106 176 Q210 196 314 176" stroke="#F26B3A" stroke-width="10" fill="none"/>'
                 '<path d="M118 204 Q210 222 302 204" stroke="#FFB38A" stroke-width="6" fill="none"/>'
                 '<rect x="176" y="242" width="68" height="14" rx="6" fill="#fff" stroke="#F5C9AE" stroke-width="3"/>'
                 '<ellipse cx="210" cy="150" rx="110" ry="14" fill="none" stroke="#fff" stroke-width="6"/>')
    chop = ('<rect x="300" y="20" width="11" height="150" rx="5" fill="#C8955C" transform="rotate(32 300 20)"/>'
            '<rect x="322" y="18" width="11" height="150" rx="5" fill="#B07A45" transform="rotate(38 322 18)"/>')
    arm = ('<ellipse cx="96" cy="176" rx="20" ry="15" fill="#fff" stroke="#F5C9AE" stroke-width="3" transform="rotate(-30 96 176)"/>'
           '<ellipse cx="324" cy="186" rx="18" ry="14" fill="#fff" stroke="#F5C9AE" stroke-width="3"/>')
    dumpling = ('<g transform="translate(46 70) rotate(-12)">'
                '<path d="M-34 10 Q0 -40 34 10 Z" fill="#FFF4E6"/>'
                '<path d="M-20 -6 l6 10 M-6 -14 l4 12 M8 -14 l-2 12 M22 -6 l-6 10" stroke="#E8C9A6" stroke-width="3" stroke-linecap="round"/>'
                f'{face(0, 2, .3)}</g>')
    sushi = ('<g transform="translate(378 78) rotate(10)">'
             '<rect x="-30" y="-6" width="60" height="26" rx="12" fill="#fff"/>'
             '<path d="M-34 0 Q0 -30 34 0 Q0 -10 -34 0 Z" fill="#FF8A5B"/>'
             f'{face(0, 8, .28)}</g>')
    drum = ('<g transform="translate(52 198) rotate(-30)">'
            '<rect x="-5" y="-48" width="10" height="34" rx="5" fill="#FFF8F0"/>'
            '<circle cx="-7" cy="-50" r="7" fill="#FFF8F0"/><circle cx="7" cy="-50" r="7" fill="#FFF8F0"/>'
            '<ellipse cx="0" cy="0" rx="28" ry="32" fill="#E8890C"/>'
            f'{face(0, 2, .3)}</g>')
    bread = ('<g transform="translate(380 200) rotate(8)">'
             '<path d="M-30 24 L-30 -2 Q-30 -24 0 -24 Q30 -24 30 -2 L30 24 Z" fill="#E8A24A"/>'
             f'{face(0, 4, .3)}</g>')
    sparkles = "".join(
        f'<path d="M{x} {y - 9} L{x + 3} {y - 3} L{x + 9} {y} L{x + 3} {y + 3} L{x} {y + 9} L{x - 3} {y + 3} '
        f'L{x - 9} {y} L{x - 3} {y - 3} Z" fill="#fff" opacity=".9"/>' for x, y in [(130, 30), (300, 236), (20, 130), (405, 145)])
    backdrop = ('<circle cx="210" cy="150" r="118" fill="#FFD9C2"/>'
                '<circle cx="210" cy="150" r="96" fill="#FFE7D6"/>')
    body = (backdrop + steam([180, 240], 58, "#FFB38A") + chop + arm + bowl_body + rice + face(210, 188, 1.15)
            + dumpling + sushi + drum + bread + sparkles.replace('fill="#fff"', 'fill="#FFB86B"'))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 260" width="420" height="260">{body}</svg>'


# ---------------------------------------------------------------- 스티커 (흰 테두리 + 작은 얼굴)
W = 'stroke="#fff" stroke-width="7" stroke-linejoin="round" paint-order="stroke"'


def _sticker(inner: str, size: int = 100) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{size}" height="{size}">{inner}</svg>'


STICKERS = {
    "onigiri": _sticker(
        f'<path d="M50 10 Q60 10 86 70 Q90 86 74 88 L26 88 Q10 86 14 70 Q40 10 50 10 Z" fill="#fff" {W}/>'
        '<path d="M50 10 Q60 10 86 70 Q90 86 74 88 L26 88 Q10 86 14 70 Q40 10 50 10 Z" fill="#FFFDF7" stroke="#EADFCB" stroke-width="2"/>'
        '<rect x="34" y="62" width="32" height="26" rx="3" fill="#2B2B2B"/>' + face(50, 48, .42)),
    "boba": _sticker(
        f'<path d="M24 26 L76 26 L70 92 L30 92 Z" fill="#F3D9B1" {W}/>'
        '<rect x="20" y="20" width="60" height="10" rx="5" fill="#FF8FA3"/>'
        '<rect x="56" y="2" width="7" height="26" rx="3" fill="#FF6B8B" transform="rotate(12 56 2)"/>'
        + "".join(f'<circle cx="{x}" cy="{y}" r="5" fill="#5C3D2E"/>' for x, y in [(38, 82), (50, 85), (62, 82), (44, 74), (56, 74)])
        + face(50, 50, .4)),
    "skewer": _sticker(
        '<rect x="47" y="4" width="6" height="92" rx="3" fill="#C8955C"/>'
        + "".join(f'<rect x="32" y="{y}" width="36" height="20" rx="10" fill="#F0592A" {W}/>' for y in (12, 36, 60))
        + face(50, 46, .35)),
    "dumpling": _sticker(
        f'<path d="M8 66 Q50 0 92 66 Q50 84 8 66 Z" fill="#FFF4E6" {W}/>'
        '<path d="M30 40 l6 12 M44 32 l3 14 M58 32 l-3 14 M72 40 l-6 12" stroke="#E8C9A6" stroke-width="3" stroke-linecap="round"/>'
        + face(50, 60, .4)),
    "heart": _sticker(f'<path d="M50 86 L14 50 Q2 34 16 20 Q32 8 50 28 Q68 8 84 20 Q98 34 86 50 Z" fill="#FF6B8B" {W}/>'
                      '<ellipse cx="32" cy="32" rx="8" ry="5" fill="#fff" opacity=".6"/>'),
    "star": _sticker(f'<path d="M50 6 L62 36 L94 38 L69 58 L78 90 L50 72 L22 90 L31 58 L6 38 L38 36 Z" fill="#FFD43B" {W}/>'
                     + face(50, 54, .32)),
}


@lru_cache(maxsize=None)
def sticker_uri(name: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(STICKERS[name].encode("utf-8")).decode()


@lru_cache(maxsize=1)
def mascot_uri() -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(mascot_svg().encode("utf-8")).decode()


ILLUSTRATIONS = {
    "bibimbap": bibimbap, "stew": stew, "noodle": noodle, "bbq": bbq, "tteokbokki": tteokbokki,
    "chicken": chicken, "burger": burger, "pizza": pizza, "bread": bread, "sushi": sushi, "jjajang": jjajang,
    "pho": pho, "curry": curry, "pasta": pasta, "tray": tray, "coffee": coffee, "cloche": cloche,
}

# 세부 업종(상가정보 소분류) → 그림. 여기에 없으면 음식 종류(cuisine) 기본 그림을 쓴다.
BY_SUB = {
    "국수/칼국수": "noodle", "냉면/밀면": "noodle", "일식 면 요리": "noodle",
    "국/탕/찌개류": "stew", "곱창 전골/구이": "bbq",
    "돼지고기 구이/찜": "bbq", "소고기 구이/찜": "bbq", "닭/오리고기 구이/찜": "bbq", "족발/보쌈": "bbq",
    "치킨": "chicken", "피자": "pizza", "버거": "burger", "토스트/샌드위치/샐러드": "bread",
    "빵/도넛": "bread", "김밥/만두/분식": "tteokbokki", "마라탕/훠궈": "stew",
    "일식 카레/돈가스/덮밥": "curry", "일식 회/초밥": "sushi", "횟집": "sushi",
}
BY_CUISINE = {
    "korean": "bibimbap", "bunsik": "tteokbokki", "chinese": "jjajang", "japanese": "sushi", "vietnamese": "pho",
    "asian": "curry", "western": "pasta", "fastfood": "burger", "buffet": "tray", "cafe": "coffee", "etc": "cloche",
}


def illustration_key(cuisine: str, category_sub) -> str:
    return BY_SUB.get(category_sub) or BY_CUISINE.get(cuisine, "cloche")


@lru_cache(maxsize=None)
def illustration_uri(key: str) -> str:
    svg = ILLUSTRATIONS.get(key, cloche)()
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()
