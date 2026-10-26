"""2단계: OpenStreetMap(Overpass API)에서 학교 주변 음식점 정보를 가져온다.

- OSM 데이터는 ODbL 라이선스로 자유롭게 쓸 수 있다(출처 표시 필요: © OpenStreetMap contributors).
- 공공데이터에 없는 '영어 이름', '영업시간'을 보충하는 용도로만 사용한다.
- 서버에 부담을 주지 않도록 요청은 한 번만 보낸다.

실행:  python scripts/02_fetch_osm.py
"""
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import CAMPUS_LAT, CAMPUS_LON, SEARCH_RADIUS_M  # noqa: E402

RAW_DIR = ROOT / "data" / "raw"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def main() -> None:
    query = f"""[out:json][timeout:90];
nwr(around:{SEARCH_RADIUS_M},{CAMPUS_LAT},{CAMPUS_LON})[amenity~"^(restaurant|fast_food|cafe|food_court)$"];
out center tags;"""
    r = requests.post(OVERPASS_URL, data={"data": query},
                      headers={"User-Agent": "SeoulTech student project (BapMate)"}, timeout=180)
    if r.status_code != 200:
        raise SystemExit(f"Overpass 서버 응답 오류({r.status_code}). 잠시 후 다시 실행하세요.")
    elements = r.json()["elements"]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / "osm_food.json"
    out.write_text(json.dumps(elements, ensure_ascii=False, indent=1), encoding="utf-8")

    # 출처 기록 (01 스크립트의 함수 재사용)
    sys.path.insert(0, str(ROOT / "scripts"))
    log_source = __import__("01_download_public_data").log_source
    log_source("OpenStreetMap (Overpass API)", "https://www.openstreetmap.org/copyright", out.name,
               f"반경 {SEARCH_RADIUS_M}m 음식점·카페 {len(elements)}건, ODbL")
    print(f"OSM 음식점 {len(elements)}건 저장 → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
