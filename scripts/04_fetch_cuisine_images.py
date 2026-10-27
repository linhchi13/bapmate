"""4단계: 음식 종류별 '예시 이미지'를 Wikimedia Commons 에서 내려받는다.

- 자유 라이선스(CC0, 퍼블릭 도메인, CC BY, CC BY-SA) 사진만 사용한다.
- 가게의 실제 음식 사진이 아니므로 화면에 '예시 이미지'라고 표시한다.
- 저작자·라이선스·원본 주소를 assets/cuisine/credits.csv 에 기록하고 앱의 '데이터 출처' 페이지에 표시한다.
- 사진은 640×320 으로 가운데를 잘라 저장한다(라이선스상 출처와 함께 변경 사실을 표시).

실행:  python scripts/04_fetch_cuisine_images.py
"""
import io
import re
import time
from pathlib import Path

import pandas as pd
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "cuisine"
HEADERS = {"User-Agent": "SeoulTechBapMate/1.0 (student project)"}
SIZE = (640, 320)

# 음식 종류 → Wikimedia Commons 파일 이름 (사람 얼굴이 없는 사진으로 골랐다)
FILES = {
    "korean": "File:Korean.food-Bibimbap-02.jpg",
    "bunsik": "File:Korean.snacks-Tteokbokki-08.jpg",
    "chinese": "File:Jajangmyeon by KFoodaddict.jpg",
    "japanese": "File:Sushi platter.jpg",
    "vietnamese": "File:Pho Bo by Banh & Mee in Kirkgate Market.jpg",
    "asian": "File:Roast Duck Curry - Thai Dish 2026-08-05.jpg",
    "western": "File:Espaguetis carbonara.jpg",
    "fastfood": "File:Homemade hamburger with french fries in Argentina.jpg",
    "buffet": "File:Laid table in Seoul, South Korea.jpg",
    "cafe": "File:Latte and dark coffee.jpg",
    "etc": "File:Korean street food-02.jpg",
}


def fetch_info(title: str) -> dict:
    for attempt in range(4):  # 서버가 요청 제한을 걸면 잠시 쉬었다가 다시 시도
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=HEADERS, timeout=60, params={
            "action": "query", "format": "json", "titles": title, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 960})
        if r.status_code == 200 and r.text.startswith("{"):
            break
        time.sleep(5 * (attempt + 1))
    else:
        raise SystemExit(f"{title}: Wikimedia 응답 오류 ({r.status_code}). 잠시 후 다시 실행하세요.")
    page = next(iter(r.json()["query"]["pages"].values()))
    ii = page["imageinfo"][0]
    md = ii["extmetadata"]
    return {
        "image_url": ii["thumburl"],
        "source_url": ii["descriptionurl"],
        "license": md.get("LicenseShortName", {}).get("value", ""),
        "license_url": md.get("LicenseUrl", {}).get("value", ""),
        "artist": re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip(),
    }


def crop_center(img: Image.Image) -> Image.Image:
    w, h = img.size
    target = SIZE[0] / SIZE[1]
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return img.resize(SIZE, Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for cuisine, title in FILES.items():
        info = fetch_info(title)
        if not re.match(r"^(CC0|Public domain|CC BY(-SA)? \d\.\d)", info["license"], re.I):
            raise SystemExit(f"{title}: 허용하지 않는 라이선스 {info['license']}")
        raw = requests.get(info["image_url"], headers=HEADERS, timeout=120).content
        img = crop_center(Image.open(io.BytesIO(raw)).convert("RGB"))
        img.save(OUT / f"{cuisine}.jpg", "JPEG", quality=78, optimize=True)
        rows.append({"cuisine": cuisine, "title": title.removeprefix("File:"), **info,
                     "modified": "가운데 잘라 640×320 으로 축소"})
        print(f"{cuisine:11s} {info['license']:14s} {title}")
        time.sleep(1.5)  # 서버 부담 줄이기
    pd.DataFrame(rows).drop(columns=["image_url"]).to_csv(OUT / "credits.csv", index=False, encoding="utf-8-sig")
    print(f"\n완료 → {OUT.relative_to(ROOT)} ({len(rows)}장)")


if __name__ == "__main__":
    main()
