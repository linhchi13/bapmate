# 과기대 밥친구 – Tài liệu báo cáo & thuyết trình (Nhóm 4)

> Mọi con số dưới đây lấy từ lần chạy thật ngày 26/10/2026 (`data/quality_report.json`).
> Nếu chạy lại script, số liệu có thể thay đổi. Khi đó hãy cập nhật lại tài liệu này.

---

## 1. Mục tiêu dự án (프로젝트 목표)
Xây dựng một website giúp sinh viên quốc tế SeoulTech **tìm quán ăn quanh trường theo ngân sách, khoảng cách và loại món**. Toàn bộ thông tin phải có **nguồn gốc rõ ràng**: thông tin nào chưa xác minh thì hiện "정보 없음", tuyệt đối không tự tạo.

## 2. Lý do chọn chủ đề (주제 선정 이유)
- Sinh viên quốc tế mới sang thường không đọc được review tiếng Hàn và chưa quen món ăn Hàn.
- Ngân sách sinh viên có hạn → cần biết **giá** trước khi vào quán.
- Naver/Kakao Map có nhiều thông tin nhưng không lọc theo nhu cầu của du học sinh (giá rẻ, đi một mình, gần trường).
- Chủ đề này cho phép áp dụng đủ quy trình **thu thập → tiền xử lý → phân tích → trực quan hoá → web** bằng Python.

## 3. Nguồn dữ liệu (데이터 출처)
| Nguồn | Loại | Lấy được gì | Số liệu thực tế |
|---|---|---|---|
| 소상공인시장진흥공단_상가(상권)정보 (data.go.kr) | Dữ liệu công, miễn phí, cập nhật theo quý | Tên quán, ngành, địa chỉ, **toạ độ** | 554.092 cửa hàng ở Seoul → 1.205 quán quanh trường |
| 행정안전부_착한가격업소 현황 (data.go.kr) | Dữ liệu công | Quán "giá tốt" do nhà nước chỉ định, **món + giá** | Ghép được 9 quán, 8 quán có giá |
| OpenStreetMap (Overpass API) | Dữ liệu mở, giấy phép ODbL | Tên tiếng Anh, giờ mở cửa, toạ độ ga tàu | 235 điểm, ghép được 129 |
| Đánh giá của sinh viên trong app | Nhóm tự thu thập | Số sao, ăn một mình/đi nhóm, số tiền đã trả | Bắt đầu từ 0 |

**Không dùng:** review, điểm và ảnh của Naver/Kakao/Google, vì điều khoản sử dụng của họ cấm thu thập tự động và nội dung đó có bản quyền.

## 4. Phương pháp thu thập (데이터 수집 방법)
- `scripts/01_download_public_data.py`:
  - Gửi request theo đúng trình tự mà nút [다운로드] trên data.go.kr thực hiện.
  - Nếu trang yêu cầu captcha (자동등록방지) thì script **dừng lại, không vượt qua**, và hướng dẫn tải thủ công.
- `scripts/02_fetch_osm.py`: gọi Overpass API **một lần** với bán kính 1.500m quanh trường.
- Mỗi lần tải, script ghi tên nguồn, URL, thời điểm và ngày cơ sở dữ liệu vào `data/sources.csv`.

## 5. Các bước tiền xử lý (데이터 전처리) – `scripts/03_build_dataset.py`
| Bước | Code pandas chính | Kết quả |
|---|---|---|
| Đọc dữ liệu | `pd.read_csv(..., usecols=...)` (chỉ đọc 13/39 cột cho nhẹ) | 554.092 dòng |
| Lọc quán ăn, bỏ quán nhậu | `df[(대분류=="음식") & ~중분류.isin({"주점"})]` | 125.003 dòng |
| Thiếu toạ độ | `pd.to_numeric(errors="coerce")` → `dropna` | 0 dòng thiếu |
| Tính khoảng cách | Công thức haversine bằng numpy (tính cả mảng cùng lúc) | |
| Lọc theo bán kính 1,5km | `df[df["distance_m"] <= 1500]` | 1.210 dòng |
| Bỏ trùng | `drop_duplicates(["name_norm", "도로명주소"])` | bỏ 5 dòng → 1.205 |
| Chuẩn hoá tên | Regex bỏ khoảng trắng, ký tự đặc biệt | dùng để so khớp giữa các nguồn |
| Chuẩn hoá loại món | `map()` từ 247 tiểu loại → 11 nhóm (한식, 분식, 베트남…) | |
| Chia khu vực | Trong trường (địa chỉ 공릉로 232) / trước cổng (≤400m) / gần ga nào nhất | |
| Làm sạch giá | `"7,000원"` → `7000`; ≤0, >100.000 hoặc không phải số → `NaN` | |
| Giá trị thiếu | **Giữ NaN**, giao diện hiện "정보 없음", không điền giá trị trung bình | |
| Ghép nguồn | So khớp tên đã chuẩn hoá + tên đường (착한가격); tên + khoảng cách ≤150m (OSM) | chỉ ghép khi khớp **đúng 1** quán |
| Báo cáo | `quality_report.json` | số dòng ở từng bước, các quán không ghép được |

**Vì sao không điền giá trị thiếu bằng trung bình?** Đây là thông tin cho người dùng thật. Nếu điền giá trung bình, sinh viên sẽ hiểu đó là giá thật của quán, tức là thông tin sai.

## 6. Phương pháp phân tích (데이터 분석 방법) – trang 📊
- **Thống kê mô tả:** `value_counts()` (số quán theo loại món và khu vực), `groupby().agg(mean, count)` (giá trung bình theo loại món).
- **Phân nhóm:** chia giá thành 3 khoảng (<8.000 / 8.000–12.000 / >12.000 won); người dùng chỉnh được các mốc.
- **Phân bố:** histogram khoảng cách, phân bố số sao.
- **Ngưỡng tin cậy:** nhóm nào có dưới 3 mẫu thì không vẽ, và app ghi rõ "데이터 부족".
- **Tổng hợp đánh giá (crowdsourcing):** một quán chỉ được coi là "hợp ăn một mình" khi có **≥3 người trả lời và ≥60% đồng ý**.
- **Một vài phát hiện từ dữ liệu:**
  - Quán Hàn nhiều nhất (445).
  - Đứng thứ hai là cafe (309).
  - Phần lớn quán tập trung quanh ga 공릉 (598 quán).

## 7. Vai trò của từng công nghệ
| Công nghệ | Vai trò trong dự án |
|---|---|
| **Python** | Ngôn ngữ chính cho cả thu thập, xử lý và web |
| **requests** | Tải file từ data.go.kr, gọi Overpass API |
| **pandas / numpy** | Đọc CSV, lọc, chuẩn hoá, bỏ trùng, merge, groupby; numpy tính khoảng cách cho 125.000 dòng cùng lúc |
| **Streamlit** | Biến script Python thành web: widget (ô tìm kiếm, slider, pills), nhiều trang (`st.navigation`), hộp thoại chi tiết (`st.dialog`), cache (`st.cache_data`), lưu trạng thái (`st.session_state`) |
| **Plotly** | Biểu đồ tương tác (bar, histogram) và bản đồ (`Scattermap` với nền Carto miễn phí, không cần API key) |
| **CSV / JSON** | Lưu dữ liệu và văn bản giao diện (`locales/ko.json`) |

## 8. Giải thích những đoạn code quan trọng
1. **Tính khoảng cách (`haversine_m`):** dùng công thức tính khoảng cách trên mặt cầu Trái Đất. Hàm nhận cả cột pandas, nên tính được 125.000 quán chỉ trong một dòng code.
2. **Tìm kiếm (`src/filters.py → search`):**
   - Ghép tên, menu, ngành và địa chỉ thành một chuỗi, rồi kiểm tra từ khoá bằng `str.contains`.
   - Bỏ qua khác biệt dấu cách: gõ "멸치 국수" vẫn tìm ra "멸치국수".
3. **Lọc (`apply_filters`):** tạo một mask True/False rồi lần lượt `&=` từng điều kiện. Đây là kiểu lọc boolean indexing của pandas.
4. **Đánh giá (`aggregate_reviews`):** `groupby("store_id").agg(...)` tính điểm trung bình, số lượt, số phiếu đồng ý; sau đó `merge` vào bảng quán.
5. **Đa ngôn ngữ (`src/i18n.py`):** mọi chữ trên giao diện nằm trong `locales/ko.json`. Muốn thêm tiếng Việt thì tạo `vi.json` với cùng các khoá.
6. **Xử lý lỗi:**
   - Thiếu file dữ liệu → app hiện hướng dẫn chạy script.
   - Thiếu cột bắt buộc → báo tên cột.
   - Thiếu cột tuỳ chọn → tự thêm cột rỗng.
   - Giá sai → chuyển thành NaN.
   - Không có kết quả → hiện thông báo trống (empty state).

## 9. Khó khăn và hạn chế (어려움과 한계)
- **Rất ít dữ liệu giá công khai:** chỉ 8/1.205 quán có giá → trang "theo ngân sách" còn ít kết quả. *Cách khắc phục:* khảo sát thực địa và cho sinh viên báo số tiền đã trả.
- **Không có điểm đánh giá công khai hợp pháp** → điểm chỉ đến từ sinh viên đánh giá trong app, ban đầu bằng 0.
- **Dữ liệu cửa hàng chốt ngày 30/06/2026**, quán có thể đã đóng hoặc chuyển đi.
- **Khoảng cách là đường chim bay**, thời gian đi bộ chỉ là ước tính (×1,3 ÷ 75m/phút).
- **So khớp tên giữa các nguồn chưa hoàn hảo:** tên chi nhánh hoặc địa chỉ ghi khác nhau → một số quán không ghép được (danh sách có trong báo cáo chất lượng).
- **Danh sách yêu thích không có đăng nhập** → mất khi đóng trình duyệt; phải tải file JSON về.
- **Trên Streamlit Cloud, file `reviews.csv` sẽ bị xoá khi server khởi động lại** → muốn lưu lâu dài cần dùng database như Google Sheets hoặc Supabase.

## 10. Hướng phát triển (향후 발전 방향)
1. Khảo sát thực địa khoảng 50 quán gần cổng trường: giá, giờ mở cửa, ảnh tự chụp.
2. Hoàn thiện giao diện tiếng Việt và tiếng Anh (`vi.json`, `en.json`) và nút đổi ngôn ngữ.
3. Lưu đánh giá vào database online (Google Sheets API hoặc Supabase).
4. Thêm thông tin halal / ăn chay sau khi đã xác minh.
5. Gợi ý cá nhân hoá dựa trên lịch sử yêu thích.
6. Tự động cập nhật dữ liệu mỗi quý theo lịch cập nhật của data.go.kr.

## 11. Thuật ngữ chuyên môn tiếng Hàn (전문 용어)
| Tiếng Việt | 한국어 | English |
|---|---|---|
| Thu thập dữ liệu | 데이터 수집 | data collection |
| Tiền xử lý dữ liệu | 데이터 전처리 | preprocessing |
| Làm sạch dữ liệu | 데이터 정제 | data cleaning |
| Giá trị thiếu | 결측치 | missing value |
| Giá trị ngoại lai / bất thường | 이상치 | outlier |
| Bản ghi trùng lặp / loại bỏ trùng lặp | 중복 데이터 / 중복 제거 | duplicate removal |
| Chuẩn hoá | 정규화 / 표준화 | normalization |
| Ghép dữ liệu | 데이터 결합 (병합) | merge / join |
| Lọc | 필터링 | filtering |
| Thống kê mô tả | 기술 통계 | descriptive statistics |
| Trực quan hoá | 시각화 | visualization |
| Biểu đồ cột / Histogram | 막대그래프 / 히스토그램 | bar chart / histogram |
| Phân bố | 분포 | distribution |
| Nhóm theo / tổng hợp | 그룹화 / 집계 | groupby / aggregation |
| Toạ độ (vĩ độ, kinh độ) | 좌표 (위도, 경도) | coordinates |
| Công thức haversine | 하버사인 공식 | haversine formula |
| Đường thẳng (chim bay) | 직선거리 | straight-line distance |
| Dữ liệu công | 공공데이터 | public data |
| Cổng dữ liệu công | 공공데이터포털 | Public Data Portal |
| Giấy phép / Điều khoản | 이용 허락 / 이용약관 | license / terms of use |
| Nguồn dữ liệu | 데이터 출처 | data source |
| Ngày cơ sở dữ liệu | 기준일 | reference date |
| Cào dữ liệu web | 웹 크롤링 / 스크래핑 | web crawling |
| Giao diện người dùng | 사용자 인터페이스 (UI) | UI |
| Trải nghiệm người dùng | 사용자 경험 (UX) | UX |
| Thiết kế responsive | 반응형 디자인 | responsive design |
| Sản phẩm khả dụng tối thiểu | 최소 기능 제품 (MVP) | MVP |
| Bộ nhớ đệm | 캐시 | cache |
| Đa ngôn ngữ | 다국어 지원 | i18n |
| Dữ liệu do người dùng đóng góp | 크라우드소싱 데이터 | crowdsourced data |
| Độ tin cậy | 신뢰도 | reliability |
| Kiểm thử | 테스트 | testing |
| Triển khai | 배포 | deployment |

## 12. Câu hỏi giảng viên có thể hỏi (예상 질문)
- **Q. 데이터는 어디서 얻었나요?**
  → 공공데이터포털의 소상공인시장진흥공단 상가(상권)정보와 행정안전부 착한가격업소 현황, 그리고 OpenStreetMap을 사용했습니다. 출처와 수집 시각은 `sources.csv`에 기록했습니다.
- **Q. 네이버 리뷰를 크롤링하지 않은 이유는?**
  → 이용약관상 자동 수집이 금지되어 있고 리뷰는 저작권이 있는 콘텐츠이기 때문입니다. 대신 앱 안에서 학생 평가를 직접 받습니다.
- **Q. 결측치는 어떻게 처리했나요?**
  → 사용자에게 잘못된 정보를 줄 수 있어서 평균값으로 채우지 않고 '정보 없음'으로 표시했습니다. 가격 이상치(0 이하, 10만 원 초과, 숫자가 아닌 값)는 결측치로 바꿨습니다.
- **Q. 중복은 어떻게 판단했나요?**
  → 공백·특수문자를 제거한 상호명과 도로명주소가 같으면 같은 가게로 보고 `drop_duplicates`로 제거했습니다. 5건이 제거됐습니다.
- **Q. 거리는 어떻게 계산했나요?**
  → 학교 주소(공릉로 232)의 위도·경도와 가게 좌표 사이를 하버사인 공식으로 계산한 직선거리입니다. 도보 시간은 1.3배 우회 계수와 분당 75m로 추정했습니다.
- **Q. '혼밥하기 좋은 곳'은 어떻게 정했나요?**
  → 추측하지 않고, 학생 3명 이상이 응답하고 60% 이상이 '좋다'고 답한 가게만 보여 줍니다.

## 13. Gợi ý kịch bản demo (5 phút)
1. **맛집 찾기:** gõ "쌀국수" → hiện các quán Việt → bấm 자세히 → bấm "카카오맵 길찾기".
2. **맛집 찾기 → 💰 1인 예산:** chọn "8,000원 이하" → các quán 착한가격 hiện ra kèm giá thật.
3. **테마별 추천:** các chủ đề 혼밥 / 친구와 / 평점 chưa hiện. Giải thích: web không tự đoán, phải có ≥3 sinh viên đánh giá thì chủ đề mới tự mở.
4. **Đăng nhập Gmail → đặt nickname** → bấm ♡ 저장 một quán → đánh giá quán đó → vào **마이페이지** xem tab 즐겨찾기 và 내 평가.
5. **데이터 분석:** lọc theo loại món, giải thích các biểu đồ.
6. **서비스 소개·개인정보:** bảng nguồn dữ liệu, các bước xử lý, chính sách bảo mật.
7. (Nếu có thời gian) **🛠️ 관리자:** số hội viên, biểu đồ đăng ký, quản lý đánh giá. Chỉ tài khoản quản trị mới thấy mục này.

## 14. Triển khai lên mạng (배포) – Streamlit Community Cloud, miễn phí
1. Tạo repo GitHub, push thư mục `seoultech_food` (thư mục `data/raw` đã nằm trong `.gitignore`, nhưng **phải push `data/restaurants.csv`**).
2. Vào https://share.streamlit.io → New app → chọn repo, đặt Main file là `app.py`.
3. Lưu ý: trên Cloud, file `reviews.csv` sẽ bị xoá khi app khởi động lại (xem mục 9).
