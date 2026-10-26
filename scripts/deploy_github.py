"""GitHub 에 저장소를 만들고 코드를 올린다 (git 설치 불필요, GitHub REST API 사용).

- 올리는 파일은 prepare_upload.py 와 같은 규칙으로 고른다(원본 데이터·비밀 파일 제외).
- 이미 있는 파일은 내용이 바뀐 경우에만 갱신한다.

실행:  $env:GH_TOKEN="ghp_..."; python scripts/deploy_github.py
"""
import base64
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_upload import wanted  # noqa: E402

REPO = "bapmate"
API = "https://api.github.com"


def main() -> None:
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("환경변수 GH_TOKEN 이 필요합니다.")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})

    me = s.get(f"{API}/user", timeout=30)
    me.raise_for_status()
    owner = me.json()["login"]

    r = s.post(f"{API}/user/repos", json={"name": REPO, "private": False,
                                          "description": "과기대 밥친구 - 서울과기대 유학생 맛집 탐험"}, timeout=30)
    if r.status_code not in (201, 422):  # 422 = 이미 있음
        raise SystemExit(f"저장소 생성 실패: {r.status_code} {r.text[:300]}")

    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and wanted(p))
    changed = 0
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        content = base64.b64encode(path.read_bytes()).decode()
        cur = s.get(f"{API}/repos/{owner}/{REPO}/contents/{rel}", timeout=30)
        body = {"message": f"update {rel}", "content": content}
        if cur.status_code == 200:
            if cur.json().get("content", "").replace("\n", "") == content:
                continue  # 바뀐 것 없음
            body["sha"] = cur.json()["sha"]
        put = s.put(f"{API}/repos/{owner}/{REPO}/contents/{rel}", json=body, timeout=60)
        if put.status_code not in (200, 201):
            raise SystemExit(f"{rel} 업로드 실패: {put.status_code} {put.text[:300]}")
        changed += 1
        print("  ↑", rel)

    print(f"\n완료: 파일 {len(files)}개 중 {changed}개 업로드")
    print(f"저장소: https://github.com/{owner}/{REPO}")


if __name__ == "__main__":
    main()
