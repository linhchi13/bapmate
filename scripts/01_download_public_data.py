"""1단계: 공공데이터포털(data.go.kr)에서 공공데이터 파일을 내려받는다.

내려받는 데이터
  1) 소상공인시장진흥공단_상가(상권)정보  : 가게 이름, 업종, 주소, 위도·경도
  2) 행정안전부_착한가격업소 현황        : 착한가격업소 이름, 주소, 메뉴, 가격

- 웹사이트의 [다운로드] 버튼과 똑같은 순서로 요청한다.
- 자동등록방지(캡차)가 요구되면 우회하지 않고 멈춘 뒤, 직접 내려받는 방법을 안내한다.
- 내려받은 시각과 출처는 data/sources.csv 에 기록한다.

실행:  python scripts/01_download_public_data.py
"""
import re
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SOURCES_CSV = ROOT / "data" / "sources.csv"

DATASETS = [
    {"key": "stores", "pk": "15083033", "title": "소상공인시장진흥공단_상가(상권)정보"},
    {"key": "good_price", "pk": "3045247", "title": "행정안전부_착한가격업소 현황"},
]


def log_source(name: str, url: str, file_name: str, note: str) -> None:
    """데이터 출처 기록: 언제, 어디서, 어떤 파일을 받았는지."""
    row = pd.DataFrame([{
        "source_name": name,
        "url": url,
        "file": file_name,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "note": note,
    }])
    if SOURCES_CSV.exists():
        old = pd.read_csv(SOURCES_CSV)
        old = old[old["source_name"] != name]  # 같은 출처는 최신 기록만 남김
        row = pd.concat([old, row], ignore_index=True)
    row.to_csv(SOURCES_CSV, index=False, encoding="utf-8-sig")


def download(session: requests.Session, ds: dict) -> Path:
    page_url = f"https://www.data.go.kr/data/{ds['pk']}/fileData.do"
    page = session.get(page_url, timeout=60).text
    detail_pk = re.search(r'id="publicDataDetailPk"[^>]*value="([^"]+)"', page).group(1)

    # (1) 다운로드할 파일 정보 요청
    info = session.post("https://www.data.go.kr/tcs/dss/selectFileDataDownload.do", data={
        "publicDataDetailPk": detail_pk,
        "publicDataPk": ds["pk"],
        "atchFileId": "",
        "fileDetailSn": "1",
        "publicDataTyCode": "PR0051",
    }, timeout=60).json()
    if not info.get("status"):
        raise SystemExit(f"파일 정보를 받지 못했습니다. 직접 내려받으세요: {page_url}")
    detail = info["dataSetFileDetailInfo"]

    # (2) 다운로드 제한 확인: 캡차가 필요하면 멈춘다(우회하지 않음)
    limit = session.post("https://www.data.go.kr/cmm/cmm/check-limit.json",
                         data={"atchFileId": info["atchFileId"], "fileDetailSn": info["fileDetailSn"]}, timeout=60)
    if limit.status_code == 403 or limit.json().get("needCaptcha"):
        raise SystemExit(f"자동등록방지 확인이 필요합니다. 브라우저에서 직접 내려받아 data/raw/ 에 넣어 주세요:\n  {page_url}")

    # (3) 파일 내려받기 (확장자는 서버가 알려주는 파일 이름에서 가져옴)
    url = (f"https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId={info['atchFileId']}"
           f"&fileDetailSn={info['fileDetailSn']}")
    print(f"내려받는 중: {detail['dataNm']}")
    with session.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        cd = r.headers.get("Content-Disposition", "")
        ext = ".zip" if ".zip" in cd.lower() else ".csv"
        out = RAW_DIR / f"{ds['key']}{ext}"
        with open(out, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)

    # (4) zip 이면 서울 파일만 꺼내고 zip은 지운다(용량 절약)
    if ext == ".zip":
        with zipfile.ZipFile(out) as z:
            seoul = [n for n in z.namelist() if "서울" in n and n.endswith(".csv")]
            if not seoul:
                raise SystemExit(f"압축 파일 안에서 서울 CSV를 찾지 못했습니다: {z.namelist()}")
            target = RAW_DIR / f"{ds['key']}_seoul.csv"
            target.write_bytes(z.read(seoul[0]))
        out.unlink()
        out = target

    log_source(ds["title"], page_url, out.name, f"기준일 {detail.get('stdrDe', '')} / {detail['dataNm']}")
    print(f"  → {out.relative_to(ROOT)}")
    return out


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (SeoulTech student project)"
    for ds in DATASETS:
        download(s, ds)
    print("완료")


if __name__ == "__main__":
    main()
