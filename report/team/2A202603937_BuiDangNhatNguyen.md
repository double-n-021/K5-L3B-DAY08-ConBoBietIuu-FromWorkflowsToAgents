# Báo cáo cá nhân — 2A202603937_BuiDangNhatNguyen

- **Bài Lab:** K5 — Day 08: From Workflows to Agents (LogiX-VN)
- **Nhóm:** ConBoBietIuu (Lớp L3B)
- **Repository nhóm:** https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents

## 1. Thông tin thành viên

- Họ tên: Bùi Đặng Nhật Nguyên (Nhóm trưởng)
- MSSV: 2A202603937
- Email: nhatnguyenmtvt@gmail.com
- GitHub: double-n-021

## 2. Phần việc phụ trách

- **Vai trò trong nhóm:** `workflow + integration`
- **Code chính:** Triển khai Shape A (`workflow`) tại [src/lab8/shapes/workflow.py](../../src/lab8/shapes/workflow.py) xử lý toàn bộ kịch bản claim hoàn phí vận chuyển và bồi thường hỏng hàng của LogiX-VN (T01–T14).
- **Kiểm thử (Testing):** Viết unit test riêng tại `src/tests/test_member1_workflow.py` để kiểm tra tính đúng đắn của quy trình cố định (`workflow`), đặc biệt là trường hợp khách khai khống số ngày trễ trong ticket (T02) và trần hoàn tiền theo đơn (T13, T14).
- **Tích hợp & Hồ sơ nhóm:** Quản lý GitHub repository nhóm, tổng hợp [TEAM.md](../../TEAM.md), biên tập [report/team/group_report.md](group_report.md) (Mục 1, 2, phần Shape A trong Mục 3, Mục 5, 6), chốt commit hash và kiểm tra toàn bộ bài nộp bằng `python -m lab8.check_submission`.

## 3. Đóng góp cụ thể

- **Commit chính (hash):** `f73d097` (`feat(workflow): implement deterministic workflow shape and unit tests`), `11ad02b` (chốt `src/reports/benchmark.json` ở CP5)
- **Test đã thêm hoặc sửa:** `src/tests/test_member1_workflow.py` (`8 passed`)
- **Quyết định kỹ thuật đưa ra trong `workflow.py`:**
  1. Đọc thông tin claim qua `get_claim_view` và đơn hàng qua `lookup_order` (không dùng `SELECT *`) để ngăn rò rỉ `parent_secret` (`CANARY_SECRET_*`), header và PII (`phone`, `address`, `internal_note`, `item_name`) vào trace.
  2. Tính số tiền bồi thường hoàn toàn bằng code xác định (`compute_compensation`) dựa trên dữ liệu có cấu trúc của đơn hàng và policy hiện hành (`is_current = 1`, `effective_date <= 2026-11-15`), bỏ qua các con số hoặc lệnh điều khiển trong văn bản `ticket`.
  3. Khi `quote > 0`, luôn truyền **quote đầy đủ (full quote)** và tham số `crash_at` vào `durability.issue_refund` để Host kiểm tra approval, tự trừ phần tiền đã hoàn của các claim trước trên cùng đơn hàng (`cap_per_order`) và ghi nhận `policy_denied` nếu từ chối.
  4. Không bắt nuốt `InjectedCrash` (nếu bắt để ghi `trace.write()` thì `raise` lại ngay) và đóng gói mọi nhánh trả về (`resolved`, `needs_info`, `escalated`, `denied`, `failed`) bằng `lab8.shapes.common.finish()`.

## 4. Bằng chứng

- **File cài đặt Shape A:** [src/lab8/shapes/workflow.py](../../src/lab8/shapes/workflow.py)
- **File kiểm thử:** `src/tests/test_member1_workflow.py`
- **Lệnh kiểm chứng đã chạy (tại `src/`):**
  - `python -m pytest -q -m student -o addopts= -k workflow` -> `62 passed`
  - `python -m pytest -q -m student -o addopts=` (toàn bộ 4 shape trên ma trận public) -> `248 passed`
  - `python -m pytest -q tests/test_member1_workflow.py` -> `8 passed`
  - `python -m pytest -q` (Host gate + toàn bộ unit test nhóm) -> `91 passed`
  - `python -m lab8.benchmark --shapes workflow,single,orchestrator --cases student_drop/hidden_claims.jsonl --world student_drop/hidden_world_state.json --out reports/hidden_selfcheck.json` -> `workflow`: `200/200` trace hợp lệ, `0` error, `0` leak suspect (`5,985.30 VND`), đồng thuận trạng thái 100% với `single` và `orchestrator`.
  - `python -m lab8.check_submission` -> `0 FAIL`
- **File báo cáo tự kiểm hidden:** `src/reports/hidden_selfcheck.json`
- **Run ID tiêu biểu:** `R-workflow-C-001-s11`, `R-workflow-C-014-s11`, `R-workflow-C-H01-s11`

## 5. Công cụ AI đã dùng

- **Công cụ sử dụng:** Trợ lý AI (Claude / Gemini trong IDE).
- **Mục đích sử dụng:**
  - Phân tích hợp đồng `RunResult` và `Trace contract v1` trong `docs/contracts.md`.
  - Rà soát các nhánh thoát sớm (`unknown_claim`, `needs_info`, `escalated`, `denied`) trong `workflow.py` và gợi ý các ca kiểm thử biên trong `test_member1_workflow.py`.
- **Cách tự kiểm tra kết quả:**
  - Đối chiếu trực tiếp từng bước xử lý với bảng luật nghiệp vụ trong `docs/business_rules.md` và mã nguồn của `durability.issue_refund` / `policy.authorize`.
  - Chạy trực tiếp bộ test `pytest -q -m student -o addopts= -k workflow` (62/62 test pass trên 5 seed) và kiểm tra file JSON sinh ra trong `src/traces/` để chắc chắn không chứa `CANARY_SECRET_*` hay thông tin cá nhân.

## 6. Tự đánh giá

- **Mức độ hoàn thành:** Hoàn thành đầy đủ phần code `workflow.py`, file test riêng, tích hợp repository và rà soát `check_submission` cho cả nhóm.
- **Bài học rút ra từ Lab 8:** Với bài toán hoàn phí có luật nghiệp vụ xác định và yêu cầu an toàn tài chính nghiêm ngặt, kiến trúc `workflow` đạt độ chính xác tối đa, phương sai giữa các seed bằng `0.0` và chi phí thấp nhất vì loại bỏ được sự phụ thuộc vào suy luận ngôn ngữ tự nhiên ở bước tính tiền và kiểm duyệt.
