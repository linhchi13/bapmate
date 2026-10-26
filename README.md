# 🍚 과기대 밥친구 (SeoulTech BapMate)

서울과기대 유학생을 위한 학교 주변 맛집 탐험 웹 서비스 — 4조

- 학교(공릉로 232) 반경 1.5km 음식점·카페 **1,205곳** (공공데이터 기반)
- 검색·필터, 예산으로 찾기, 테마별 추천, 데이터 분석(Plotly), 즐겨찾기, 학생 평가
- 확인되지 않은 정보는 만들지 않고 **'정보 없음'** 으로 표시

## 1. 설치

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 데이터 만들기 (이미 data/restaurants.csv 가 있으면 생략 가능)

```bash
python scripts/01_download_public_data.py   # 공공데이터포털에서 원본 내려받기
python scripts/02_fetch_osm.py              # OpenStreetMap 영어 이름·영업시간
python scripts/03_build_dataset.py          # 정제·결합 → data/restaurants.csv
```

## 3. 실행

```bash
streamlit run app.py
```
브라우저에서 http://localhost:8501 이 열립니다.

## 회원 기능

- Google 계정으로 로그인(`st.login`) → 닉네임 등록 → 즐겨찾기·평가·마이페이지·탈퇴
- 이메일·실명·비밀번호는 저장하지 않음. Google 계정 고유번호를 SHA-256 으로 바꾼 값만 저장
- 저장소: `secrets.toml` 에 `[gsheets]` 가 있으면 Google Sheets, 없으면 `data/*.csv`
- `secrets.toml` 이 없으면 **localhost 에서만** 닉네임으로 테스트 로그인 가능(배포된 앱에서는 막힘)
- 배포·설정 방법: `docs/HUONG_DAN_DUA_WEB_LEN_MANG.md`, 설정 예시: `.streamlit/secrets.toml.example`

## 4. 점검

```bash
python tests/smoke_test.py
```

## 폴더 구조

```
app.py                  앱 시작점(페이지 메뉴)
views/                  페이지: home, budget, themes, stats, favorites, about
src/config.py           설정(학교 좌표, 반경, 업종 분류, 가격 구간)
src/data.py             데이터 읽기·검사·평가 저장/집계
src/filters.py          검색·필터·정렬
src/ui.py               카드, 상세 창, 지도, 즐겨찾기, 스타일
src/i18n.py             다국어 문구 (locales/ko.json)
scripts/                데이터 수집·정제 파이프라인
data/restaurants.csv    앱이 쓰는 최종 데이터
data/sources.csv        데이터 출처·수집 시각 기록
data/quality_report.json 정제 결과 보고서
data/manual/            팀 현장 조사 자료(가격·영업시간·사진)
data/reviews.csv        앱에서 받은 학생 평가(자동 생성)
assets/images/          팀이 직접 찍은 가게 사진
```

## 현장 조사 자료 추가 방법

1. 앱에서 가게를 찾아 상세 창의 정보를 보고, `data/restaurants.csv` 에서 그 가게의 `id` 를 확인합니다.
2. `data/manual/menu_prices.csv` 에 한 줄씩 추가합니다.
   ```
   store_id,store_name,menu,price,checked_date,checked_by,note
   MA0101....,공릉동멸치국수,멸치국수,5000,2026-11-02,찐티린치,메뉴판 확인
   ```
3. 영업시간·영어 이름·사진은 `data/manual/store_info.csv` 에 적고, 사진은 `assets/images/` 에 넣습니다(직접 찍은 사진만).
4. `python scripts/03_build_dataset.py` 를 다시 실행합니다.

## 데이터 출처

| 데이터 | 제공 | 사용 항목 |
|---|---|---|
| 소상공인시장진흥공단_상가(상권)정보 (기준일 2026-06-30) | 공공데이터포털 | 상호, 업종, 주소, 위도·경도 |
| 행정안전부_착한가격업소 현황 (기준일 2026-09-30) | 공공데이터포털 | 착한가격업소 지정, 메뉴·가격 |
| OpenStreetMap | © OpenStreetMap contributors (ODbL) | 영어 이름, 영업시간, 지하철역 좌표 |
| 학생 평가 | 이 앱 사용자 | 별점, 혼밥·모임 추천, 결제 금액 |

네이버·카카오·구글의 리뷰·평점·사진은 이용약관상 수집하지 않습니다. 지도는 각 서비스의 공개 URL 링크만 사용합니다.
