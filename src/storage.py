"""회원·평가·즐겨찾기 저장소.

- secrets.toml 에 [gsheets] 설정이 있으면 → Google Sheets 에 저장 (배포용, 데이터가 사라지지 않음)
- 없으면 → data/ 폴더의 CSV 에 저장 (내 컴퓨터에서 개발·시연용)

두 저장소 모두 같은 함수(read, append, delete_user)를 제공하므로 나머지 코드는 어느 쪽인지 몰라도 된다.
모든 표는 '한 줄씩 추가'만 하고, 같은 사람이 같은 가게를 다시 평가하면 pandas 에서 마지막 줄만 쓴다.
"""
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DATA_DIR

TABLES = {
    "members": ["user_id", "nickname", "nationality", "joined_at"],
    "reviews": ["review_id", "user_id", "store_id", "stars", "solo_ok", "group_ok", "price_paid",
                "comment", "created_at"],
    "favorites": ["user_id", "store_id", "action", "created_at"],
    # 가게 정보 수정: 팀 현장 조사(바로 반영) 또는 회원 제보(관리자 승인 후 반영)
    # 같은 update_id 가 여러 줄이면 마지막 줄의 status 가 최종 상태 (pending → approved / rejected)
    "store_updates": ["update_id", "user_id", "store_id", "menus", "open_hours", "source", "status", "created_at"],
}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def secret_section(name: str):
    """secrets.toml 의 [name] 부분. 파일이나 항목이 없으면 None."""
    try:
        return st.secrets[name] if name in st.secrets else None
    except Exception:  # secrets.toml 자체가 없을 때
        return None


class CsvStorage:
    name = "CSV (로컬)"

    def __init__(self, folder: Path):
        self.folder = folder

    def _path(self, table: str) -> Path:
        return self.folder / f"{table}.csv"

    def read(self, table: str) -> pd.DataFrame:
        path = self._path(table)
        if not path.exists():
            return pd.DataFrame(columns=TABLES[table])
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        return df.reindex(columns=TABLES[table], fill_value="")

    def append(self, table: str, row: dict) -> None:
        path = self._path(table)
        new = pd.DataFrame([{c: row.get(c, "") for c in TABLES[table]}])
        new.to_csv(path, mode="a", header=not path.exists(), index=False, encoding="utf-8")

    def delete_where(self, table: str, column: str, value: str) -> None:
        """column 값이 value 인 줄을 모두 지운다."""
        df = self.read(table)
        df[df[column] != value].to_csv(self._path(table), index=False, encoding="utf-8")

    def delete_user(self, user_id: str) -> None:
        for table in TABLES:
            self.delete_where(table, "user_id", user_id)


class SheetsStorage:
    name = "Google Sheets"

    def __init__(self, conf):
        import gspread  # 배포 환경에서만 필요하므로 여기서 import

        client = gspread.service_account_from_dict(dict(conf["service_account"]))
        self.book = client.open_by_url(conf["spreadsheet_url"])
        self._ws = {}

    def _sheet(self, table: str):
        """표 이름과 같은 워크시트. 없으면 머리글과 함께 새로 만든다."""
        if table not in self._ws:
            import gspread
            try:
                ws = self.book.worksheet(table)
            except gspread.WorksheetNotFound:
                ws = self.book.add_worksheet(table, rows=1000, cols=len(TABLES[table]))
                ws.append_row(TABLES[table], value_input_option="RAW")
            self._ws[table] = ws
        return self._ws[table]

    def read(self, table: str) -> pd.DataFrame:
        values = self._sheet(table).get_all_values()  # 모든 값을 '문자열'로 받음
        if len(values) <= 1:
            return pd.DataFrame(columns=TABLES[table])
        return pd.DataFrame(values[1:], columns=values[0]).reindex(columns=TABLES[table], fill_value="")

    def append(self, table: str, row: dict) -> None:
        self._sheet(table).append_row([str(row.get(c, "")) for c in TABLES[table]], value_input_option="RAW")

    def delete_where(self, table: str, column: str, value: str) -> None:
        ws = self._sheet(table)
        values = ws.get_all_values()
        col = values[0].index(column)
        rows = [i + 1 for i, v in enumerate(values) if i > 0 and v[col] == value]
        for r in reversed(rows):  # 아래 줄부터 지워야 줄 번호가 밀리지 않음
            ws.delete_rows(r)

    def delete_user(self, user_id: str) -> None:
        for table in TABLES:
            self.delete_where(table, "user_id", user_id)


class HubStorage(CsvStorage):
    """Hugging Face 의 비공개 Dataset 저장소에 CSV 를 보관한다 (배포용).

    앱 서버는 프로세스가 하나뿐이므로, 서버 안의 CSV 를 기준으로 쓰고(잠금으로 순서 보장)
    쓸 때마다 Dataset 에 업로드한다. 서버가 다시 켜지면 Dataset 에서 최신 파일을 내려받는다.
    """
    name = "Hugging Face Dataset"

    def __init__(self, conf):
        import shutil
        import tempfile
        import threading

        from huggingface_hub import HfApi, hf_hub_download

        self.api = HfApi(token=conf["token"])
        self.repo = conf["repo_id"]
        self.lock = threading.Lock()
        super().__init__(Path(tempfile.gettempdir()) / "bapmate_data")
        self.folder.mkdir(parents=True, exist_ok=True)
        remote = set(self.api.list_repo_files(self.repo, repo_type="dataset"))
        for table in TABLES:
            if f"{table}.csv" in remote:
                src = hf_hub_download(self.repo, f"{table}.csv", repo_type="dataset",
                                      token=conf["token"], force_download=True)
                shutil.copy(src, self._path(table))

    def _push(self, table: str, message: str) -> None:
        if self._path(table).exists():
            self.api.upload_file(path_or_fileobj=str(self._path(table)), path_in_repo=f"{table}.csv",
                                 repo_id=self.repo, repo_type="dataset", commit_message=message)

    def append(self, table: str, row: dict) -> None:
        with self.lock:
            super().append(table, row)
            self._push(table, f"add {table}")

    def delete_where(self, table: str, column: str, value: str) -> None:
        with self.lock:
            super().delete_where(table, column, value)
            self._push(table, f"delete from {table}")

    def delete_user(self, user_id: str) -> None:
        with self.lock:
            for table in TABLES:
                CsvStorage.delete_where(self, table, "user_id", user_id)
                self._push(table, "delete user")


@st.cache_resource
def get_storage():
    if secret_section("gsheets"):
        return SheetsStorage(secret_section("gsheets"))
    if secret_section("hfdata"):
        return HubStorage(secret_section("hfdata"))
    return CsvStorage(DATA_DIR)


@st.cache_data(ttl=60, show_spinner=False)
def read_table(table: str) -> pd.DataFrame:
    """읽기는 60초 동안 캐시(Google Sheets 호출 횟수 제한 때문). 쓰기 후에는 캐시를 비운다."""
    return get_storage().read(table)


def append_row(table: str, row: dict) -> None:
    get_storage().append(table, row)
    read_table.clear()


def delete_user_data(user_id: str) -> None:
    get_storage().delete_user(user_id)
    read_table.clear()


def delete_rows(table: str, column: str, value: str) -> None:
    get_storage().delete_where(table, column, value)
    read_table.clear()
