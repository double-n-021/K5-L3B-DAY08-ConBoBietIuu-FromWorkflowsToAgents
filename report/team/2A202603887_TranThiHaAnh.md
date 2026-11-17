# Báo cáo cá nhân — 2A202603887_TranThiHaAnh

- **Bài Lab:** K5 — Day 08: From Workflows to Agents (LogiX-VN)
- **Nhóm:** ConBoBietIuu (Lớp L3B)
- **Repository nhóm:** https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents

## 1. Thông tin thành viên

- Họ tên: Trần Thị Hà Anh
- MSSV: 2A202603887
- Email: tranthihaanh200204@gmail.com
- GitHub: hnha02

## 2. Phần việc phụ trách

- **Vai trò trong nhóm:** `orchestrator + handoff + benchmark/adr`
- **Code chính:** Triển khai Shape C (`orchestrator`) tại [src/lab8/shapes/orchestrator.py](../../src/lab8/shapes/orchestrator.py) kết hợp cơ chế chuyển giao dữ liệu qua allowlist (`lab8.handoff.make_handoff`) và Investigator chỉ đọc (`lab8.runtime.run_readonly_investigators`).
- **Kiểm thử Bảo mật & Đánh giá Benchmark:**
  - Viết unit test riêng tại `src/tests/test_member3_orchestrator_security.py` kiểm tra ranh giới bảo mật của `handoff.v1`, phân quyền Investigator và kiểm tra không rò rỉ `CANARY_SECRET_*` hay PII vào trace (T05, T10).
  - Chạy Benchmark so sánh 4 kiến trúc (`workflow`, `single`, `orchestrator`, `swarm`) trên 14 claim public x 5 seed (`11, 22, 33, 44, 55`) sinh file `src/reports/benchmark.json`.
- **Quyết định Kiến trúc & Báo cáo nhóm:** Hoàn thiện [report/team/decision_adr.md](decision_adr.md); viết phần giải pháp Shape C (Mục 3) cùng Mục 4 (Kết quả), Mục 7 (Hạn chế) và Mục 8 (Tài liệu tham khảo) trong [report/team/group_report.md](group_report.md).

## 3. Đóng góp cụ thể

- **Commit chính (hash):** `971feff` (`feat(orchestrator): implement orchestrator shape and security tests`), `492587b` (`docs(team): fill member 3 email in TEAM.md`)
- **Test đã thêm hoặc sửa:** `src/tests/test_member3_orchestrator_security.py`
- **Quyết định kỹ thuật đưa ra trong `orchestrator.py` và ADR:**
  1. Sử dụng `lab8.handoff.make_handoff` để lọc các trường được phép (`ALLOWED_FIELDS`, `FACT_KEYS`) và chỉ cấp quyền `READONLY_TOOLS` (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`) cho Investigator; tuyệt đối không truyền `parent_secret` hay `raw_headers`.
  2. Chỉ ghi gói `handoff` đã được sanitize (`safe_dump(handoff)`) và kết quả đọc đã qua allowlist vào `Trace`, đảm bảo tuân thủ `Trace contract v1` và đạt `0` lần lộ secret/PII.
  3. Giữ quyền gọi `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` tại tầng Orchestrator với **full quote**, không cấp bất kỳ công cụ ghi nào cho Investigator.
  4. Dựa trên số liệu thực nghiệm trong `src/reports/benchmark.json` (so sánh `pass_rate`, `pass_5`, `seed_variance`, `cost_per_success_vnd`, `mean_steps`), phân tích điểm yếu của `swarm` ở seed 55 (T02) và lập luận lựa chọn kiến trúc tối ưu trong `decision_adr.md`.

## 4. Bằng chứng

- **File cài đặt Shape C:** [src/lab8/shapes/orchestrator.py](../../src/lab8/shapes/orchestrator.py)
- **File kiểm thử:** `src/tests/test_member3_orchestrator_security.py`
- **File báo cáo Benchmark:** `src/reports/benchmark.json`
- **File quyết định kiến trúc (ADR):** [report/team/decision_adr.md](decision_adr.md)
- **Lệnh kiểm chứng đã chạy (tại `src/`):**
  - `python -m pytest -q -m student -o addopts= -k orchestrator` -> `62 passed`
  - `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
  - `python -m pytest -q tests/test_member3_orchestrator_security.py` -> `passed`
- **Run ID tiêu biểu:** `R-orchestrator-C-005-s11`, `R-orchestrator-C-010-s11`

## 5. Công cụ AI đã dùng

- **Công cụ sử dụng:** Trợ lý AI (Claude / Gemini / ChatGPT).
- **Mục đích sử dụng:**
  - Phân tích cơ chế allowlist trong `src/lab8/handoff.py` và luồng thực thi của `run_readonly_investigators` trong `src/lab8/runtime.py`.
  - Hỗ trợ kiểm tra công thức tính `pass_5`, `seed_variance` và `cost_per_success_vnd` trong `src/lab8/metrics.py` để trình bày vào `decision_adr.md`.
- **Cách tự kiểm tra kết quả:**
  - Kiểm tra trực tiếp bằng các ca test bảo mật T05 (`C-005`, khác `principal_id`) và T10 (`C-010`, kiểm tra `forbid_substrings`) thông qua `pytest -q -m student -o addopts= -k orchestrator`.
  - Đối chiếu toàn bộ số liệu ghi trong `decision_adr.md` và `group_report.md` khớp chính xác với file `src/reports/benchmark.json` do công cụ sinh ra.

## 6. Tự đánh giá

- **Mức độ hoàn thành:** Hoàn thành đầy đủ Shape C (`orchestrator.py`), bộ test bảo mật handoff/trace, chạy benchmark 4 shape x 5 seed và viết `decision_adr.md`.
- **Bài học rút ra từ Lab 8:** Khi chuyển giao tác vụ giữa các Agent (Orchestrator sang Investigator), tóm tắt bằng LLM không thể thay thế cơ chế lọc allowlist bằng code (`make_handoff`), và mọi quyết định chọn kiến trúc đều phải dựa trên bằng chứng định lượng (variance, cost, safety) thay vì mặc định chọn Multi-Agent.
