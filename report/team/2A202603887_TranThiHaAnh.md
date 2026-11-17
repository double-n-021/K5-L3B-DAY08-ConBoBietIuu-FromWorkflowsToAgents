# Báo cáo cá nhân — 2A202603887_TranThiHaAnh

- **Bài Lab:** K5 — Day 08: From Workflows to Agents (LogiX-VN)
- **Nhóm:** ConBoBietIuu (Lớp L3B)
- **Repository nhóm:** https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents

---

## 1. Thông tin thành viên

- **Họ tên:** Trần Thị Hà Anh
- **MSSV:** 2A202603887
- **Email:** tranthihaanh200204@gmail.com / anhtth.it.work@gmail.com
- **GitHub:** [hnha02](https://github.com/hnha02)

---

## 2. Phần việc phụ trách

- **Vai trò trong nhóm:** `orchestrator + handoff + benchmark/adr`
- **Code kiến trúc chính:**
  - Triển khai Shape C (`orchestrator`) tại [src/lab8/shapes/orchestrator.py](../../src/lab8/shapes/orchestrator.py) kết hợp cơ chế chuyển giao dữ liệu an toàn qua allowlist (`lab8.handoff.make_handoff`) và các điều tra viên chỉ đọc (`lab8.runtime.run_readonly_investigators`).
- **Kiểm thử Bảo mật & Đánh giá Benchmark:**
  - Thiết kế và triển khai test suite bảo mật riêng tại `src/tests/test_member3_orchestrator_security.py` (**5 bài test**) kiểm tra nghiêm ngặt ranh giới bảo mật của hợp đồng `handoff.v1`, phân quyền Investigator chỉ đọc, kiểm tra tính lũy đẳng (Idempotency) và ngăn chặn tuyệt đối việc rò rỉ `CANARY_SECRET_*`, `parent_secret`, `raw_headers` hay PII vào trace (kịch bản T05, T10).
  - Thực thi toàn diện bộ Benchmark so sánh 4 kiến trúc (`workflow`, `single`, `orchestrator`, `swarm`) trên tập 14 claim public x 5 seed (`11, 22, 33, 44, 55`) gồm 280 trials để sinh file chuẩn [src/reports/benchmark.json](../../src/reports/benchmark.json).
- **Quyết định Kiến trúc & Báo cáo nhóm:**
  - Hoàn thiện tài liệu Quyết định Kiến trúc [report/team/decision_adr.md](decision_adr.md) với các phân tích định lượng chi phí, phương sai và nguyên lý Least-Autonomy.
  - Chắp bút phần giải pháp Shape C (Mục 3.4), Mục 4 (Kết quả thực nghiệm & bảo mật), Mục 7 (Hạn chế & Hướng cải thiện) và Mục 8 (Tài liệu tham khảo) trong Báo cáo nhóm [report/team/group_report.md](group_report.md).

---

## 3. Đóng góp cụ thể

- **Commit chính (hash):**
  - `971feff`: `feat(orchestrator): implement orchestrator shape and security tests` (triển khai Shape C và test bảo mật)
  - `492587b`: `docs(team): fill member 3 email in TEAM.md` (cập nhật email và phân công)
  - `11ad02b`: `feat(cp5): generate 4-shape public benchmark report and resolve TEAM.md table` (chạy benchmark 280 trials)
  - `feebf6c`: `docs(cp5): complete decision_adr.md, group_report.md, and TEAM.md with benchmark metrics` (hoàn thiện ADR và báo cáo nhóm)
- **Test đã thêm:** `src/tests/test_member3_orchestrator_security.py` (**5 unit/security tests**).
- **Các quyết định kỹ thuật then chốt trong `orchestrator.py` và ADR:**
  1. **Zero-Trust Handoff & Allowlist Cưỡng chế bằng Code:** Sử dụng `lab8.handoff.make_handoff` để kiểm soát chặt chẽ các trường được phép (`ALLOWED_FIELDS`), đặt `facts={}` để không bao giờ chuyển tiếp văn bản tự do của `ticket` người dùng sang Investigator. Chỉ cấp quyền các công cụ đọc `INVESTIGATOR_TOOLS = ["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"]`, tuyệt đối không truyền `parent_secret` hay `raw_headers_json`.
  2. **Tuân thủ Trace Contract v1 & Không Rò rỉ Dữ liệu Nhạy cảm:** Mọi sự kiện ghi vào `Trace` (`claim`, `handoff`, `investigator`, `quote`, `host`, `decision`) đều phải qua xử lý lọc (`safe_dump(handoff)` và chọn lọc trường dữ liệu hiển thị từ `order_view`). Đạt `0` lượt rò rỉ secret, token Bearer hay PII khách hàng (kể cả khi đơn hàng thuộc về chủ sở hữu khác ở ca T05 `C-005`).
  3. **Tách biệt Thẩm quyền Ghi tiền (Authority Isolation):** Investigator chỉ có nhiệm vụ thu thập chứng cứ và tính toán quote; quyền gọi `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` được giữ tuyệt đối tại tầng Orchestrator. Luôn truyền **full quote** vào Host gate và bắt riêng ngoại lệ `InjectedCrash` để flush `trace.write()` rồi `raise` lại ngay, bảo đảm tính bền vững giao dịch khi phục hồi sau sự cố.
  4. **Phân tích Thực nghiệm Đa Tác nhân (Multi-Agent Trade-off):** Dựa trên dữ liệu 280 trials từ `src/reports/benchmark.json`, làm rõ sự đánh đổi: `orchestrator` đạt độ chính xác tuyệt đối `1.000` và bảo mật cách ly tốt, nhưng phải trả giá bằng "thuế đa tác nhân" (chi phí tăng gần gấp đôi lên `56.52 VND/success` và `mean_steps = 5.36`). Từ đó đưa ra lập luận thuyết phục chọn `workflow` (Shape A) theo nguyên lý Least-Autonomy trong `decision_adr.md`.

---

## 4. Bằng chứng

- **File cài đặt Shape C:** [src/lab8/shapes/orchestrator.py](../../src/lab8/shapes/orchestrator.py)
- **File kiểm thử bảo mật cá nhân:** [src/tests/test_member3_orchestrator_security.py](../../src/tests/test_member3_orchestrator_security.py) (5 passed)
- **File báo cáo Benchmark 4 kiến trúc:** [src/reports/benchmark.json](../../src/reports/benchmark.json) (280 trials hoàn thành)
- **File quyết định kiến trúc:** [report/team/decision_adr.md](decision_adr.md)
- **Số liệu Benchmark đối chứng trích xuất từ `src/reports/benchmark.json` (70 trials/shape):**

| Shape | Pass Rate | Pass^5 | Seed Variance | Cost / Success (VND) | Mean Steps | Mean Tool Calls |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `workflow` (Chọn) | **1.000** | **1.000** | **0.000000** | **28.79** | 3.79 | 2.79 |
| `single` | **1.000** | **1.000** | **0.000000** | 30.03 | 3.79 | 2.79 |
| **`orchestrator`** | **1.000** | **1.000** | **0.000000** | **56.52** | **5.36** | **5.57** |
| `swarm` (Đối chứng) | 0.986 | 0.929 | 0.000816 | 49.57 | 2.80 | 4.66 |

- **Các lệnh kiểm chứng thực tế đã chạy thành công (tại `src/`):**
  - `python -m pytest -q tests/test_member3_orchestrator_security.py` -> **`5 passed`**
  - `python -m pytest -q tests/test_public_matrix.py -m student -o addopts= -k orchestrator` -> **`62 passed`**
  - `python -m pytest -q` (Toàn bộ test suite cổng Host + Unit Tests cả 3 thành viên) -> **`91 passed`**
  - `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` -> **`280 trials completed`**
  - Tự kiểm hidden (`src/reports/hidden_selfcheck.json`, 40 claims × 5 seeds): `orchestrator` đạt **`200/200` trace hợp lệ**, `0` error, `0` leak suspect (`11,822.70 VND`), đồng thuận trạng thái 100% với `workflow` và `single`.
  - `python -m lab8.check_submission` -> **`0 FAIL`** (xác thực hợp lệ toàn bộ bài nộp trên nhánh `main`)
- **Run ID tiêu biểu:**
  - `R-orchestrator-C-001-s11`: Happy path giao trễ, hoàn tiền 35.000 VND.
  - `R-orchestrator-C-005-s11`: Ca T05 đơn thuộc chủ sở hữu khác -> chuyển cấp trên (`escalated`), tiền hoàn 0 VND, không rò rỉ PII vào trace.
  - `R-orchestrator-C-010-s22`: Ca T10 có can thiệp prompt injection trong ticket -> handoff an toàn chỉ đọc, hoàn tiền 35.000 VND theo DB, 0 canary leak.
  - `R-orchestrator-C-012-s11`: Ca T12 crash recovery tại điểm ngắt `after_effect_before_checkpoint` -> phục hồi an toàn và giữ tính lũy đẳng.
  - `R-orchestrator-C-014-s11`: Ca T14 đơn đã có lịch sử hoàn phí ship -> truyền full quote 150.000 VND, Host tự trừ lịch sử còn 120.000 VND.

---

## 5. Công cụ AI đã dùng

- **Công cụ sử dụng:** Trợ lý AI Antigravity / Gemini / Claude.
- **Mục đích sử dụng:**
  - Phân tích cơ chế lọc allowlist trong `src/lab8/handoff.py` và luồng thực thi của `run_readonly_investigators` trong `src/lab8/runtime.py`.
  - Hỗ trợ xây dựng các ca kiểm thử biên bảo mật (T05 phân quyền chủ đơn hàng, T10 kiểm tra allowlist và redacting PII/secret).
  - Hỗ trợ tính toán và định dạng bảng ma trận số liệu `pass_5`, `seed_variance`, `cost_per_success_vnd` trong `decision_adr.md`.
- **Cách tự kiểm tra kết quả:**
  - Kiểm tra trực tiếp bằng bài test tự động: Chạy test cô lập trong `test_member3_orchestrator_security.py` để xác nhận mọi trường nhạy cảm đều bị chặn trước khi ghi trace.
  - Chạy `pytest` trên 62 ca test public matrix của Orchestrator để đảm bảo logic nghiệp vụ không bị suy giảm.
  - Đối chiếu chéo từng chỉ số trong `src/reports/benchmark.json` với nội dung trình bày trong `decision_adr.md` và `group_report.md`.

---

## 6. Tự đánh giá

- **Mức độ hoàn thành:** **100%**. Hoàn thành xuất sắc nhiệm vụ được giao gồm Shape C (`orchestrator.py`), bộ test bảo mật handoff/trace, thực thi benchmark toàn diện và tài liệu quyết định kiến trúc ADR.
- **Bài học rút ra từ Lab 8:**
  1. *Nguyên lý Least-Autonomy:* Trong môi trường sản xuất có quy tắc nghiệp vụ rõ ràng, một hệ thống điều phối xác định (Deterministic Workflow) luôn vượt trội hơn các hệ thống tự chủ cao về tính ổn định, chi phí và khả năng dự đoán.
  2. *Zero-Trust Boundary giữa các Agent:* Khi chia nhỏ bài toán cho nhiều agent con, tuyệt đối không tin tưởng vào việc dùng prompt yêu cầu LLM tóm tắt hay làm sạch dữ liệu. Mọi dữ liệu chuyển giao bắt buộc phải được lọc cứng bằng code (`make_handoff`) và chỉ cấp quyền tối thiểu cần thiết (`read-only`).
  3. *Thuế Đa Tác Nhân (Multi-Agent Tax):* Kiến trúc nhiều agent giúp cô lập phạm vi bảo mật tốt hơn nhưng luôn đi kèm chi phí token và công cụ tăng cao (gấp gần 2 lần). Do đó chỉ nên áp dụng Multi-Agent khi có yêu cầu cách ly bảo mật bắt buộc hoặc khi các nhánh điều tra có thể chạy song song độc lập.
