# Báo cáo cá nhân — 2A202603914_TranGiaBao

- **Bài Lab:** K5 — Day 08: From Workflows to Agents (LogiX-VN)
- **Nhóm:** ConBoBietIuu (Lớp L3B)
- **Repository nhóm:** https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents

## 1. Thông tin thành viên

- Họ tên: Trần Gia Bảo
- MSSV: 2A202603914
- Email: 26ai.baotg@vinuni.edu.vn
- GitHub: Jay-Gabriel

## 2. Phần việc phụ trách

- **Vai trò trong nhóm:** `single + durability/crash`
- **Code chính:** Triển khai Shape B (`single` — Bounded ReAct Agent) tại [src/lab8/shapes/single.py](../../src/lab8/shapes/single.py) sử dụng vòng lặp `lab8.runtime.run_react` với giới hạn `max_steps=8`.
- **Kiểm thử & Độ bền vững (Durability / Crash Suite):**
  - Viết unit test riêng tại `src/tests/test_member2_single_and_crash.py` kiểm tra vòng lặp ReAct, khả năng chống prompt injection (T09), tính bất biến khi gọi lại (Idempotency — T11) và khả năng phục hồi sau sự cố (Crash Recovery — T12).
  - Chạy bộ kiểm thử 20 điểm crash (`python -m lab8.crash_test --count 20 --out reports/crash.json`) đảm bảo đạt `20/20`.
- **Nghiên cứu & Báo cáo nhóm:** Hoàn thiện phiếu nghiên cứu và thực nghiệm ablation tại [report/team/research_card.md](research_card.md); viết phần giải pháp Shape B (Single Agent) trong Mục 3 của [report/team/group_report.md](group_report.md).

## 3. Đóng góp cụ thể

- **Commit chính (hash):** *(Điền mã commit hash sau khi push code `single.py`, `crash.json` và test)*
- **Test đã thêm hoặc sửa:** `src/tests/test_member2_single_and_crash.py`
- **Quyết định kỹ thuật đưa ra trong `single.py` và kiểm thử Crash:**
  1. Thiết kế hàm `decide(observation)` chỉ được phép chọn các công cụ đọc (`READONLY_TOOLS`: `lookup_order`, `lookup_policy`, `compute_compensation`) với cờ `worker=True`, tuyệt đối không gọi `issue_refund` từ bên trong vòng lặp ReAct.
  2. Do `run_react` ghi đè biến `seen` ở mỗi bước lặp, sử dụng biến trạng thái cục bộ để lưu kết quả `order_view` và `quote_payload`, đồng thời gọi `MockLLM` (`complete`) để ghi nhận đầy đủ `model_calls` vào `Budget`.
  3. Không tin số ngày trễ hay mã điều khoản cũ (`SHIP-LATE-OLD`) viết trong `ticket`; chỉ kết luận dựa trên dữ liệu trả về từ `lookup_order` và `compute_compensation`.
  4. Sau khi vòng lặp ReAct dừng, code của `single.py` truyền **full quote** và `crash_at` vào `durability.issue_refund`, không bắt nuốt `InjectedCrash` để đảm bảo khi resume sau crash (`after_effect_before_checkpoint`), hệ thống chỉ giữ đúng 1 dòng `refund_ledger` và 1 audit `refund_committed`.

## 4. Bằng chứng

- **File cài đặt Shape B:** [src/lab8/shapes/single.py](../../src/lab8/shapes/single.py)
- **File kiểm thử:** `src/tests/test_member2_single_and_crash.py`
- **File báo cáo Crash Suite:** `src/reports/crash.json` (`"crash_safety": "20/20"`)
- **File phiếu nghiên cứu:** [report/team/research_card.md](research_card.md)
- **Lệnh kiểm chứng đã chạy (tại `src/`):**
  - `python -m pytest -q -m student -o addopts= -k single` -> `62 passed`
  - `python -m lab8.crash_test --count 20 --out reports/crash.json` -> `crash_safety 20/20`
  - `python -m pytest -q tests/test_member2_single_and_crash.py` -> `passed`
- **Run ID tiêu biểu:** `R-single-C-001-s11`, `R-single-C-012-s11`

## 5. Công cụ AI đã dùng

- **Công cụ sử dụng:** Trợ lý AI (Claude / Gemini / ChatGPT).
- **Mục đích sử dụng:**
  - Tìm hiểu cơ chế hoạt động của `run_react` và `dispatch` trong `src/lab8/runtime.py`.
  - Hỗ trợ phân tích cơ chế transaction và idempotency key `refund:{claim_id}` trong `src/lab8/durability.py` và rà soát khung nội dung `research_card.md`.
- **Cách tự kiểm tra kết quả:**
  - Chạy thực nghiệm phản ví dụ `python -m lab8.demo.buggy_workflow` để đối chiếu sự khác biệt giữa checkpoint đơn lẻ và ledger có khóa idempotency.
  - Chạy toàn bộ 62 test của `single` trên 5 seed (`11, 22, 33, 44, 55`) và kiểm tra nội dung `src/reports/crash.json` đạt `20/20`.

## 6. Tự đánh giá

- **Mức độ hoàn thành:** Hoàn thành đầy đủ Shape B (`single.py`), bộ test riêng, báo cáo `crash.json` (`20/20`) và `research_card.md`.
- **Bài học rút ra từ Lab 8:** Vòng lặp ReAct cho phép Agent linh hoạt chọn công cụ đọc theo ngữ cảnh, nhưng bắt buộc phải đặt giới hạn số bước (`max_steps=8`), tách quyền ghi tiền về phía Host và sử dụng idempotency key trong cùng transaction SQLite để chống chi trả trùng lặp khi crash.
