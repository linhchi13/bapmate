# Hướng dẫn đưa 과기대 밥친구 lên mạng + bật đăng nhập Google

Làm lần lượt **5 bước** dưới đây, tổng cộng khoảng 40–60 phút. Không mất tiền.

| Bước | Việc cần làm | Kết quả |
|---|---|---|
| 1 | Đưa code lên GitHub | Có kho code online |
| 2 | Deploy lên Streamlit Cloud | Có link web, ví dụ `https://gwagidae-bapchingu.streamlit.app` |
| 3 | Tạo Google Sheets + Service Account | Nơi lưu hội viên, đánh giá, yêu thích |
| 4 | Tạo OAuth Client (đăng nhập Google) | Nút "Google 계정으로 로그인" hoạt động |
| 5 | Dán Secrets + mở cho mọi người dùng | Ai có Gmail cũng đăng ký được |

> ⚠️ **Quy tắc an toàn:**
> - Các mã `client_secret`, `private_key` và `cookie_secret` **tuyệt đối không** đưa lên GitHub và không gửi vào nhóm chat.
> - Chỉ dán các mã này vào ô **Secrets** của Streamlit Cloud, và vào file `.streamlit/secrets.toml` trên máy (file này đã nằm trong `.gitignore`).

---

## Bước 1 – Đưa code lên GitHub (không cần cài git)
1. Đăng ký tài khoản tại https://github.com.
2. Bấm **+** (góc trên bên phải) → **New repository**.
   - Repository name: `bapmate`
   - Chọn **Public** (Streamlit Cloud miễn phí yêu cầu Public, hoặc phải cấp quyền thêm nếu để Private)
   - Bấm **Create repository**.
3. Trên máy, mở PowerShell trong thư mục `python\seoultech_food` rồi chạy:
   ```
   ..\.venv\Scripts\python.exe scripts\prepare_upload.py
   ```
   Lệnh này tạo thư mục `python\bapmate_upload` chỉ chứa các file cần thiết (33 file, khoảng 470KB, không có dữ liệu gốc 300MB và không có mã bí mật).
4. Trên trang repo vừa tạo, bấm **uploading an existing file**.
5. Mở thư mục `bapmate_upload`, chọn **tất cả** file và thư mục bên trong (Ctrl+A), kéo thả vào trang GitHub, rồi bấm **Commit changes**.
6. Kiểm tra trên GitHub: phải thấy `app.py` ngay ở trang đầu (không nằm trong thư mục con) và có thư mục `.streamlit`, `data`, `src`, `views`.
   - Nếu thiếu `.streamlit`: bấm **Add file → Create new file**, gõ tên `.streamlit/config.toml`, rồi dán nội dung của file cùng tên trên máy vào.

## Bước 2 – Deploy lên Streamlit Community Cloud
1. Vào https://share.streamlit.io → **Continue with GitHub** → cho phép truy cập.
2. Bấm **Create app** → **Deploy a public app from GitHub**.
   - Repository: `<tên-bạn>/bapmate`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: đặt tên dễ nhớ, ví dụ `gwagidae-bapchingu` → link sẽ là `https://gwagidae-bapchingu.streamlit.app`
   - **Advanced settings** → Python version: chọn 3.12 hoặc mới hơn
3. Bấm **Deploy**, đợi vài phút.
4. Lúc này web đã chạy, mọi người xem và tìm quán được, nhưng ô đăng nhập hiện "로그인 기능을 준비 중이에요". Như vậy là đúng: chế độ đăng nhập thử bị khoá trên mạng để không ai mạo danh được.

📝 **Ghi lại link web của bạn**, bước 4 sẽ cần đến.

## Bước 3 – Google Sheets làm nơi lưu dữ liệu
### 3.1 Tạo project trên Google Cloud
1. Vào https://console.cloud.google.com và đăng nhập Gmail của bạn (nên dùng Gmail riêng của nhóm).
2. Ở thanh trên cùng, bấm chọn project → **New Project**. Đặt tên `bapmate` → **Create** → chọn project đó.

### 3.2 Bật API
1. Menu ☰ → **APIs & Services → Library**.
2. Tìm **Google Sheets API** → **Enable**.
3. Tìm **Google Drive API** → **Enable**.

### 3.3 Tạo Service Account (tài khoản "robot" để web ghi vào Sheets)
1. Menu ☰ → **IAM & Admin → Service Accounts** → **Create service account**.
2. Name: `bapmate-sheets` → **Create and continue** → bỏ qua phần phân quyền → **Done**.
3. Bấm vào service account vừa tạo → tab **Keys** → **Add key → Create new key → JSON** → **Create**.
   Máy sẽ tải về một file `.json`. **Giữ kỹ file này và không đưa lên GitHub.**
4. Mở file JSON và copy giá trị `client_email` (dạng `bapmate-sheets@bapmate-xxxx.iam.gserviceaccount.com`).

### 3.4 Tạo file Google Sheets
1. Vào https://sheets.google.com → tạo bảng tính trống, đặt tên `bapmate_db`.
2. Bấm **Share (공유)** → dán `client_email` ở trên → chọn quyền **Editor** → bỏ tick "Notify" → **Share**.
3. Copy link của bảng tính (thanh địa chỉ trình duyệt).

> Không cần tạo sheet con hay tiêu đề cột. Lần đầu web chạy sẽ tự tạo 3 sheet là `members`, `reviews`, `favorites`.

## Bước 4 – Tạo OAuth Client cho đăng nhập Google
1. Menu ☰ → **APIs & Services → OAuth consent screen**. Ở một số giao diện, mục này có tên **Google Auth Platform**.
2. Bấm **Get started** và điền:
   - App name: `과기대 밥친구`
   - User support email: email của bạn
   - Audience: **External**
   - Contact email: email của bạn → đồng ý điều khoản → **Create**
3. Mục **Clients** → **Create client**:
   - Application type: **Web application**
   - Name: `bapmate-web`
   - **Authorized redirect URIs**: thêm **2 dòng**:
     ```
     http://localhost:8501/oauth2callback
     https://gwagidae-bapchingu.streamlit.app/oauth2callback
     ```
     (dòng 2 thay bằng link web thật của bạn ở bước 2, **giữ đuôi `/oauth2callback`**)
   - Bấm **Create** → copy **Client ID** và **Client secret**.
4. Mục **Audience**:
   - Lúc đầu app ở chế độ **Testing**: chỉ những Gmail được thêm vào **Test users** mới đăng nhập được (tối đa 100). Hãy thêm Gmail của 5 thành viên để thử trước.
   - Khi muốn **mọi người** đều dùng được: bấm **Publish app**. Web chỉ xin quyền cơ bản (`openid`, `email`, `profile`) nên thường không cần Google xét duyệt.

## Bước 5 – Dán Secrets
### 5.1 Tạo `cookie_secret`
Chạy lệnh sau trên máy rồi copy chuỗi kết quả:
```
..\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

### 5.2 Điền nội dung Secrets
Mở file mẫu `.streamlit/secrets.toml.example` và điền:
- `[auth]`:
  - `redirect_uri`: link web + `/oauth2callback`
  - `cookie_secret`: chuỗi vừa tạo ở 5.1
  - `client_id` và `client_secret`: lấy từ bước 4
- `[gsheets]` → `spreadsheet_url`: link Google Sheets ở bước 3.4
- `[gsheets.service_account]`: chép **từng dòng** trong file JSON ở bước 3.3. Lưu ý:
  - `private_key` giữ nguyên các ký tự `\n`, đặt trong dấu ngoặc kép.

### 5.3 Dán lên Streamlit Cloud
1. Vào https://share.streamlit.io → bên cạnh app bấm **⋮ → Settings → Secrets**.
2. Dán toàn bộ nội dung (với `redirect_uri` là **link web thật**) → **Save**. App sẽ tự khởi động lại.

### 5.4 (Không bắt buộc) Dùng thử trên máy với Google login
Tạo file `seoultech_food/.streamlit/secrets.toml` với cùng nội dung, nhưng đổi `redirect_uri = "http://localhost:8501/oauth2callback"`.

## Kiểm tra sau khi xong
1. Mở link web → bấm **🔐 Google 계정으로 로그인** → chọn Gmail.
2. Màn hình **회원 가입** hiện ra → nhập nickname, tick đồng ý → **가입하고 시작하기**.
3. Bấm **♡ 저장** một quán, rồi đánh giá một quán.
4. Mở Google Sheets: phải thấy dữ liệu mới trong các sheet `members`, `favorites`, `reviews`.
5. Vào **마이페이지**: thấy nickname, đánh giá của mình, có nút đăng xuất và xoá tài khoản.

## Lỗi thường gặp
| Lỗi | Cách sửa |
|---|---|
| `redirect_uri_mismatch` khi đăng nhập | `redirect_uri` trong Secrets phải **giống hệt** một dòng trong *Authorized redirect URIs* (cả `https`, không có `/` thừa ở cuối) |
| `Access blocked` / `access_denied` | App đang ở chế độ Testing và Gmail đó chưa có trong Test users → thêm vào, hoặc bấm Publish app |
| `SpreadsheetNotFound` / `PermissionError` | Chưa Share bảng tính cho `client_email` với quyền Editor, hoặc chưa bật Sheets/Drive API |
| Web báo lỗi khi đọc `private_key` | Copy thiếu; phải giữ nguyên `-----BEGIN PRIVATE KEY-----` … `-----END PRIVATE KEY-----\n` |
| Web "ngủ" sau vài ngày không ai dùng | Đây là cơ chế của bản miễn phí; bấm nút **Yes, get this app back up** là chạy lại, dữ liệu trong Sheets vẫn còn |

## Cập nhật code sau này
Sửa code trên máy → chạy `tests/smoke_test.py` → chạy `scripts/prepare_upload.py` → trên GitHub bấm **Add file → Upload files** và kéo các file đã sửa vào → **Commit**. Streamlit Cloud sẽ tự cập nhật web sau khoảng 1 phút.

---

### Cách hệ thống hội viên hoạt động (để trình bày với giảng viên)
- **Xác thực (인증):** dùng Google OIDC qua hàm có sẵn `st.login()` của Streamlit. Web **không lưu mật khẩu**.
- **Định danh (식별):** mã `sub` của tài khoản Google được băm SHA-256 thành `user_id`. Trong Sheets **không có email hay họ tên**, chỉ có `user_id`, nickname và quốc tịch (tuỳ chọn).
- **Lưu trữ (저장소):** `src/storage.py` có 2 lớp `CsvStorage` (máy cá nhân) và `SheetsStorage` (khi deploy) với cùng các hàm. Code còn lại không cần biết dữ liệu đang được lưu ở đâu.
- **Ghi thêm, không sửa (append-only):**
  - Đánh giá lại hoặc bỏ yêu thích đều ghi thêm một dòng mới; pandas `drop_duplicates(keep="last")` chỉ lấy trạng thái mới nhất.
  - Nhờ vậy mỗi người chỉ có 1 đánh giá cho mỗi quán, và không bị lỗi khi nhiều người ghi cùng lúc.
- **Quyền của người dùng (개인정보 보호):** nút **회원 탈퇴** xoá toàn bộ dòng có `user_id` của người đó trong cả 3 bảng.
