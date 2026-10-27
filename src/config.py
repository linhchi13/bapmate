"""프로젝트 전체에서 함께 쓰는 설정값."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESTAURANTS_CSV = DATA_DIR / "restaurants.csv"
SOURCES_CSV = DATA_DIR / "sources.csv"
QUALITY_REPORT = DATA_DIR / "quality_report.json"
MANUAL_DIR = DATA_DIR / "manual"
IMAGES_DIR = ROOT / "assets" / "images"  # 팀이 직접 찍은 가게 사진 (없으면 src/illustrations.py 의 일러스트 사용)

# 서울과학기술대학교 기준 좌표: 학교 공식 주소(공릉로 232)의 좌표.
# 상가(상권)정보에서 '서울특별시 노원구 공릉로 232' 주소를 가진 업소의 위도·경도 값을 사용했다.
CAMPUS_NAME = "서울과학기술대학교 (공릉로 232)"
CAMPUS_LAT = 37.633078
CAMPUS_LON = 127.076789

# 학교에서 이 거리(직선, m) 안의 가게만 수집한다.
SEARCH_RADIUS_M = 1500

# '학교 앞'으로 볼 거리(m). 그보다 멀면 가장 가까운 지하철역 이름으로 구역을 나눈다.
CAMPUS_FRONT_M = 400

# 지하철역 좌표: OpenStreetMap(railway=station) 에서 조회한 값
STATIONS = {
    "공릉역": (37.6256358, 127.0730437),
    "태릉입구역": (37.6176924, 127.0756723),
    "하계역": (37.6360179, 127.0682520),
    "화랑대역": (37.6197841, 127.0837122),
    "중계역": (37.6455373, 127.0638733),
    "먹골역": (37.6114417, 127.0776518),
}

# 도보 시간 추정: 직선거리 × 1.3(도로가 구불구불한 정도) ÷ 분당 75m
WALK_DETOUR = 1.3
WALK_M_PER_MIN = 75

# 예산 구간 기본값(원). 화면에서 바꿀 수 있다.
DEFAULT_BUDGET_BANDS = (8000, 12000)

# 학생 평가로 '혼밥/모임 추천'을 판단할 최소 응답 수와 찬성 비율
MIN_VOTES = 3
MIN_YES_RATIO = 0.6

# 상가(상권)정보 업종 → 앱에서 쓰는 음식 종류
# (중분류, 소분류) 순서로 찾고, 소분류 규칙이 없으면 중분류 규칙을 쓴다.
CUISINE_BY_SUB = {
    "김밥/만두/분식": "bunsik",
    "버거": "fastfood", "피자": "fastfood", "치킨": "fastfood",
    "토스트/샌드위치/샐러드": "fastfood",
    "베트남식 전문": "vietnamese",
    "기타 동남아식 전문": "asian",
    "빵/도넛": "cafe", "아이스크림/빙수": "cafe", "떡/한과": "cafe", "카페": "cafe",
    "그 외 기타 간이 음식점": "etc",
}
CUISINE_BY_MID = {
    "한식": "korean",
    "중식": "chinese",
    "일식": "japanese",
    "서양식": "western",
    "동남아시아": "asian",
    "구내식당·뷔페": "buffet",
    "비알코올": "cafe",
}
EXCLUDED_MID = {"주점"}  # 술집은 제외

CUISINE_ORDER = ["korean", "bunsik", "chinese", "japanese", "vietnamese", "asian",
                 "western", "fastfood", "buffet", "cafe", "etc"]
CUISINE_ICON = {
    "korean": "🍚", "bunsik": "🍙", "chinese": "🥟", "japanese": "🍣", "vietnamese": "🍜",
    "asian": "🍛", "western": "🍝", "fastfood": "🍔", "buffet": "🍱", "cafe": "☕", "etc": "🍴",
}
CUISINE_COLOR = {
    "korean": "#E8590C", "bunsik": "#F08C00", "chinese": "#C92A2A", "japanese": "#1971C2",
    "vietnamese": "#2B8A3E", "asian": "#5F3DC4", "western": "#A61E4D", "fastfood": "#E67700",
    "buffet": "#0B7285", "cafe": "#795548", "etc": "#495057",
}
