"""GitHub 에 올릴 파일만 골라서 ../bapmate_upload 폴더에 복사한다.

- 제외: 원본 데이터(300MB), 비밀 키(secrets.toml), 로컬 회원·평가 CSV, 캐시 파일
- 만들어진 폴더 안의 내용을 GitHub 웹사이트에 끌어다 놓으면 된다.

실행:  python scripts/prepare_upload.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "bapmate_upload"

EXCLUDE_DIRS = {"raw", "__pycache__", ".venv", "_test_storage"}
EXCLUDE_FILES = {"secrets.toml", "secrets_cloud.toml", "members.csv", "reviews.csv", "favorites.csv"}


def wanted(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    return path.name not in EXCLUDE_FILES and path.suffix not in {".bak", ".pyc"}


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    files = [p for p in ROOT.rglob("*") if p.is_file() and wanted(p)]
    for f in files:
        target = OUT / f.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
    size = sum(f.stat().st_size for f in files) / 1024
    print(f"{len(files)}개 파일 ({size:,.0f} KB) → {OUT}")
    for f in files:
        print("  ", f.relative_to(ROOT))


if __name__ == "__main__":
    main()
