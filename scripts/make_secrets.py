"""Google 설정값을 모아서 .streamlit/secrets.toml 을 만들고, Google Sheets 연결을 시험한다.

실행 예:
  python scripts/make_secrets.py --json "C:/Users/Admin/Downloads/bapmate-xxxx.json" \
      --sheet "https://docs.google.com/spreadsheets/d/..." \
      --client-id "xxx.apps.googleusercontent.com" --client-secret "GOCSPX-..." \
      --app-url "https://gwagidae-bapchingu.streamlit.app"

결과
  .streamlit/secrets.toml          : 내 컴퓨터용 (redirect_uri = localhost)
  .streamlit/secrets_cloud.toml    : Streamlit Cloud 의 Secrets 칸에 붙여 넣을 내용 (redirect_uri = 앱 주소)
두 파일 모두 .gitignore 대상이며 GitHub 에 올리면 안 된다.
"""
import argparse
import json
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ST_DIR = ROOT / ".streamlit"


def toml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # 따옴표·\n 을 TOML 에 맞게 이스케이프


def build(redirect_uri: str, cookie: str, args, sa: dict) -> str:
    lines = [
        "[auth]",
        f"redirect_uri = {toml_str(redirect_uri)}",
        f"cookie_secret = {toml_str(cookie)}",
        f"client_id = {toml_str(args.client_id)}",
        f"client_secret = {toml_str(args.client_secret)}",
        'server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"',
        "",
        "[gsheets]",
        f"spreadsheet_url = {toml_str(args.sheet)}",
        "",
        "[gsheets.service_account]",
    ]
    lines += [f"{k} = {toml_str(str(v))}" for k, v in sa.items()]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True, help="서비스 계정 JSON 키 파일 경로")
    p.add_argument("--sheet", required=True, help="Google Sheets 주소")
    p.add_argument("--client-id", required=True)
    p.add_argument("--client-secret", required=True)
    p.add_argument("--app-url", default="", help="Streamlit Cloud 앱 주소 (없으면 로컬용만 생성)")
    args = p.parse_args()

    sa = json.loads(Path(args.json).read_text(encoding="utf-8"))
    if sa.get("type") != "service_account":
        raise SystemExit("서비스 계정 JSON 파일이 아닙니다.")

    # 1) Google Sheets 연결 시험: 3개 워크시트(머리글 포함)를 미리 만들어 둔다
    import sys

    import gspread
    sys.path.insert(0, str(ROOT))
    from src.storage import TABLES

    book = gspread.service_account_from_dict(sa).open_by_url(args.sheet)
    for name, cols in TABLES.items():
        try:
            book.worksheet(name)
        except gspread.WorksheetNotFound:
            ws = book.add_worksheet(name, rows=1000, cols=len(cols))
            ws.append_row(cols, value_input_option="RAW")
    print(f"✅ Google Sheets 연결 성공: {book.title} (워크시트: {', '.join(TABLES)})")

    cookie = secrets.token_hex(32)
    ST_DIR.mkdir(exist_ok=True)
    (ST_DIR / "secrets.toml").write_text(build("http://localhost:8501/oauth2callback", cookie, args, sa), encoding="utf-8")
    print("✅ .streamlit/secrets.toml 생성 (로컬용)")
    if args.app_url:
        url = args.app_url.rstrip("/") + "/oauth2callback"
        (ST_DIR / "secrets_cloud.toml").write_text(build(url, cookie, args, sa), encoding="utf-8")
        print(f"✅ .streamlit/secrets_cloud.toml 생성 (Streamlit Cloud 용, redirect_uri={url})")


if __name__ == "__main__":
    main()
