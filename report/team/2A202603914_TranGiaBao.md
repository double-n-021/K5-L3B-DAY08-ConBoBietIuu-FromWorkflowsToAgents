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
- **Code chính:** Triển khai Shape B (`single` — Bounded ReAct Agent) tại [src/lab8/shapes/single.py](../../src/lab8/shapes/single.py) sử dụng vòng lặp `lab8.runtime.run_react` với giới hạn cứng `max_steps=8` và `worker=True`.
- **Kiểm thử & Độ bền vững (Durability / Crash Suite):**
  - Viết bộ kiểm thử toàn diện tại `src/tests/test_member2_single_and_crash.py` (**24 test cases**) kiểm tra: Happy path C-001, các nhánh early return (unknown claim, missing order, principal scope), tính chống prompt injection (T09), làm sạch dữ liệu nhạy cảm / PII trong trace (T10), tính bất biến khi gọi lại (Idempotency — T11), phục hồi sau sự cố tại cả 3 điểm crash (T12), runtime thật dừng sau đúng 8 lượt khi liên tục chọn tool đọc, Single xử lý `step_cap` trả về `failed` và không gọi hoàn tiền, spy đối chiếu chính xác lời gọi model/tool với Budget, kiểm tra chặt chẽ giả thuyết delta model_calls = -1.0 bằng `math.isclose`, phát hiện sai lệch nội dung audit policy_denied, tính bất biến thứ tự hàng/key JSON của audit, cùng test phản ví dụ phát hiện sai lệch cho ablation.
  - Chạy bộ kiểm thử crash tự động `python -m lab8.crash_test --count 20 --out reports/crash.json` đạt tuyệt đối `20/20`.
- **Nghiên cứu & Báo cáo nhóm:**
  - Hoàn thiện phiếu nghiên cứu R4 và thực nghiệm ablation (viết script `src/bonus/jay_ablation.py` sinh `src/reports/jay_ablation.json` với kiểm tra đối chiếu trực tiếp trên 70 cặp DB độc lập và chuẩn hóa audit) tại [report/team/research_card.md](research_card.md).
  - Viết phần giải pháp Shape B (Single Agent) trong Mục 3 của [report/team/group_report.md](group_report.md).

## 3. Đóng góp cụ thể

- **Commit chính (hash):** `b32666f` (nhánh `feat/member2-single-react-crash`)
- **Test đã thêm:** `src/tests/test_member2_single_and_crash.py` (24 unit/integration tests).
- **Quyết định kỹ thuật đưa ra trong `single.py` và kiểm thử Crash:**
  1. Thiết lập hàm `decide(observation)` chỉ được phép chọn các công cụ đọc (`lookup_order`, `compute_compensation`) với cờ `worker=True`, tuyệt đối không gọi `issue_refund` từ bên trong vòng lặp ReAct.
  2. Quản lý trạng thái cục bộ cho mỗi lần chạy để lưu `order_view` và `quote_payload`, gọi `MockLLM` (`complete`) ở mỗi bước để ghi nhận đầy đủ `model_calls` vào `Budget`.
  3. Không tin vào số ngày trễ ghi trong `ticket` (như ca T02 ghi 5 ngày nhưng thực tế đơn trễ 2 ngày); luôn căn cứ theo dữ liệu trả về từ DB qua `lookup_order` và tính toán của `compute_compensation`.
  4. Sau khi vòng lặp ReAct dừng, code của `single.py` truyền **full quote** và `crash_at` vào `durability.issue_refund`, để ngoại lệ `InjectedCrash` lan truyền tự nhiên (không nuốt lỗi). Đảm bảo khi resume sau sự cố (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`), hệ thống duy trì đúng 1 dòng trong bảng `refund_ledger` và 1 bản ghi audit `refund_committed`.
  5. Đảm bảo toàn bộ trace được làm sạch, không ghi lại ticket tự do của khách hàng, token canary, số điện thoại hay địa chỉ giao hàng.

## 4. Bằng chứng

- **File cài đặt Shape B:** [src/lab8/shapes/single.py](../../src/lab8/shapes/single.py)
- **File kiểm thử cá nhân:** `src/tests/test_member2_single_and_crash.py` (24 passed)
- **File báo cáo Crash Suite:** `src/reports/crash.json` (`"crash_safety": "20/20"`)
- **File benchmark riêng Single:** `src/reports/jay_single_benchmark.json` (`pass_rate: 1.0`, `pass_5: 1.0`, `cost/success: 30.03 VND`)
- **File kịch bản ablation & báo cáo:** `src/bonus/jay_ablation.py`, `src/reports/jay_ablation.json`
- **File phiếu nghiên cứu:** [report/team/research_card.md](research_card.md)
- **Lệnh kiểm chứng thực tế đã chạy thành công (tại `src/` dùng `.venv/bin/python`):**
  - `.venv/bin/python -m pytest -q tests/test_member2_single_and_crash.py` -> **`24 passed`**
  - `.venv/bin/python -m pytest -q tests/test_public_matrix.py -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"` -> **`62 passed`**
  - `.venv/bin/python -m pytest -q` (Cổng host gate + test cá nhân) -> **`78 passed`**
  - `.venv/bin/python -m lab8.crash_test --count 20 --out reports/crash.json` -> **`crash_safety 20/20`**
  - `.venv/bin/python -m bonus.jay_ablation --out reports/jay_ablation.json` -> `STATUS: THANH_CONG, paired DB checks: PASS (0 mismatches), mean_model_calls delta: -1.0000, cost delta: -0.98 VND`
- **Run ID tiêu biểu:** `R-single-C-001-s11`, `R-single-C-002-s55`, `R-single-C-011-s11`, `R-single-C-012-s11`, `R-single-C-014-s11`.

## 5. Công cụ AI đã dùng

- **Công cụ sử dụng:** Trợ lý AI Antigravity (Gemini).
- **Mục đích sử dụng:**
  - Phân tích luồng ReAct callback và cơ chế đóng kết nối SQLite an toàn trong `src/lab8/runtime.py`.
  - Hỗ trợ xây dựng kịch bản kiểm thử TDD tái hiện các điều kiện biên: Prompt injection (T09), Redaction kiểm tra rò rỉ PII/Canary secret (T10), Idempotency khi chạy lại (T11) và Crash Recovery tại 3 điểm ngắt (T12).
  - Thiết kế thực nghiệm ablation có kiểm soát (cô lập biến `draft`) cho Research Card R4 và cơ chế đối chiếu trực tiếp trên database độc lập.
- **Cách tự kiểm tra và xác minh:**
  - Áp dụng phương pháp TDD: Viết test trước trong `test_member2_single_and_crash.py`, chạy xác nhận các ca fail trên stub cũ, sau đó mới triển khai code trong `single.py` để đạt 20 test xanh.
  - Chạy đối chiếu ma trận công khai 14 claim x 5 seed (`62 passed` cho `single`), kiểm thử crash suite 20/20, và đối chiếu 70 cặp database độc lập giữa 2 nhánh baseline/treatment đảm bảo không có bất kỳ sai lệch nào về tiền hay audit.

## 6. Tự đánh giá

- **Mức độ hoàn thành:** Đã hoàn thành và xác minh đầy đủ các hạng mục được phân công cho thành viên Trần Gia Bảo theo đúng spec.
- **Bài học rút ra từ Lab 8:**
  - *Ranh giới an toàn:* Vòng lặp Agent chỉ nên có quyền thu thập dữ liệu và đề xuất phương án; mọi thao tác ghi dữ liệu, duyệt tiền và ràng buộc nghiệp vụ (capping, policy) bắt buộc phải do Host quản lý.
  - *Idempotency & Durability:* Checkpoint đơn thuần không thể đảm bảo an toàn giao dịch; chỉ có giao dịch ACID trên DB kết hợp Idempotency Key (`refund:{claim_id}`) và bảng Audit Event mới ngăn chặn triệt để hiện tượng chi trả trùng lặp khi hệ thống bị crash giữa chừng.
