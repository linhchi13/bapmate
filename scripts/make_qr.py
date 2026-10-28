"""웹사이트 주소 QR 코드 만들기 → assets/qr_bapmate.png (포스터·발표 자료용).

실행:  python scripts/make_qr.py
(앱에서는 이 그림 파일만 보여 주므로, 배포 서버에는 qrcode 라이브러리가 필요 없다)
"""
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
URL = "https://gwagidae-bapchingu.streamlit.app"
OUT = ROOT / "assets" / "qr_bapmate.png"


def main() -> None:
    qr = qrcode.QRCode(box_size=12, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(URL)
    code = qr.make_image(fill_color="#3B2A20", back_color="white").convert("RGB")

    # 아래에 서비스 이름과 주소를 적은 카드 형태로
    w, h = code.size
    card = Image.new("RGB", (w + 60, h + 150), "#FFF4EC")
    card.paste(code, (30, 30))
    draw = ImageDraw.Draw(card)
    try:
        title = ImageFont.truetype("malgunbd.ttf", 34)
        small = ImageFont.truetype("malgun.ttf", 20)
    except OSError:
        title = small = ImageFont.load_default()
    draw.text(((w + 60) / 2, h + 60), "과기대 밥친구", fill="#F26B3A", font=title, anchor="mm")
    draw.text(((w + 60) / 2, h + 108), URL.removeprefix("https://"), fill="#3B2A20", font=small, anchor="mm")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    card.save(OUT)
    print("저장:", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
