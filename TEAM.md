# Team

## Thông tin nhóm

- Tên nhóm: ConBoBietIuu
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents, `main`, `11ad02b`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Bùi Đặng Nhật Nguyên (Nhóm trưởng) | 2A202603937 | nhatnguyenmtvt@gmail.com | double-n-021 | workflow + integration |
|   2 | Trần Gia Bảo | 2A202603914 | 26ai.baotg@vinuni.edu.vn | Jay-Gabriel | single + durability/crash |
|   3 | Trần Thị Hà Anh | 2A202603887 | tranthihaanh200204@gmail.com | hnha02 | orchestrator + handoff + benchmark/adr |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Bùi Đặng Nhật Nguyên (`2A202603937`) | `workflow + integration` | `f73d097` | `src/tests/test_member1_workflow.py` |
| Trần Gia Bảo (`2A202603914`) | `single + durability/crash` | `b32666f` | `src/tests/test_member2_single_and_crash.py` |
| Trần Thị Hà Anh (`2A202603887`) | `orchestrator + handoff + benchmark/adr` | `971feff` | `src/tests/test_member3_orchestrator_security.py` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603937_BuiDangNhatNguyen

### Phần việc phụ trách

- Nhóm trưởng, quản lý tích hợp Git, giải quyết xung đột khi merge PR và kiểm soát chất lượng bài nộp (`check_submission`).
- Triển khai Shape A (`src/lab8/shapes/workflow.py`) và bộ kiểm thử `src/tests/test_member1_workflow.py`.
- Tổng hợp `TEAM.md`, `report/team/group_report.md` (Mục 1–8), phối hợp chạy benchmark 4 shapes (`src/reports/benchmark.json`) và chốt `report/team/decision_adr.md`.

### Đóng góp cụ thể

- Triển khai hoàn chỉnh Shape A (`src/lab8/shapes/workflow.py`) xử lý quy trình hoàn phí cố định: đọc dữ liệu qua allowlist (`get_claim_view`, `lookup_order`), tính tiền bằng `compute_compensation`, truyền full quote và `crash_at` vào `durability.issue_refund`, đạt `62/62 passed` trên student matrix.
- Viết bộ unit test `src/tests/test_member1_workflow.py` (`8 passed`) kiểm tra chống khai khống ngày trễ (T02 trên 5 seed), trần hoàn tiền theo đơn (T13, T14), bảo mật trace (T05, T10) và phục hồi sau crash (T12).
- Thiết lập repository nhóm, quản lý merge PR của 3 thành viên, chạy chốt `src/reports/benchmark.json` (commit `11ad02b`) và hoàn thiện `decision_adr.md`, `group_report.md` đạt `0 FAIL` trên `check_submission`.

### Bằng chứng

- Commit chính: `f73d097` (`feat(workflow): implement deterministic workflow shape and unit tests`), `11ad02b` (`feat(cp5): generate 4-shape public benchmark report and resolve TEAM.md table`)
- File code: `src/lab8/shapes/workflow.py`
- File test: `src/tests/test_member1_workflow.py` (`8 passed`)
- Báo cáo cá nhân: `report/team/2A202603937_BuiDangNhatNguyen.md`

## 2A202603914_TranGiaBao

### Phần việc phụ trách

- Triển khai Shape B (`src/lab8/shapes/single.py` — Bounded ReAct Agent với `max_steps=8`).
- Kiểm thử Idempotency (T11), Crash Recovery (T12), chạy Crash Suite 20/20 (`src/reports/crash.json`) và viết bộ kiểm thử `src/tests/test_member2_single_and_crash.py`.
- Hoàn thiện `report/team/research_card.md` (kèm ablation) và viết phần Shape B trong Mục 3 của `report/team/group_report.md`.

### Đóng góp cụ thể

- Triển khai hoàn chỉnh Shape B tại `src/lab8/shapes/single.py` (vòng lặp Bounded ReAct với `max_steps=8`, `worker=True`, model chỉ đọc qua `lookup_order` và `compute_compensation`, Host ghi tiền và kiểm tra duyệt qua `issue_refund`).
- Viết file test toàn diện `src/tests/test_member2_single_and_crash.py` (24/24 test passed) bao gồm kiểm thử ReAct loop, 8-step cap runtime thật, spy budget đối chiếu chính xác, trace sạch, chống prompt injection, idempotency, crash recovery, kiểm tra delta model calls = -1.0 bằng math.isclose, chuẩn hóa và đối chiếu nội dung audit policy_denied, và test phản ví dụ cho ablation.
- Chạy công cụ crash test sinh `src/reports/crash.json` đạt tuyệt đối `20/20`.
- Chạy benchmark độc lập cho Single `src/reports/jay_single_benchmark.json` (70/70 trial pass, pass^5=1.0, cost/success=30.03 VND).
- Xây dựng thực nghiệm ablation `src/bonus/jay_ablation.py` (với kiểm tra đối chiếu trực tiếp trên 70 cặp DB độc lập) sinh `src/reports/jay_ablation.json` và hoàn thiện phiếu nghiên cứu R4 tại `report/team/research_card.md`.
- Viết phần giải pháp Shape B trong Mục 3 của `report/team/group_report.md` và hoàn thiện báo cáo cá nhân `report/team/2A202603914_TranGiaBao.md`.

### Bằng chứng

- Commit chính: `b32666f` (`feat(single): implement Shape B bounded ReAct agent, crash suite and ablation`), `a883b34`
- File code: `src/lab8/shapes/single.py`
- File test: `src/tests/test_member2_single_and_crash.py` (24 test passed)
- Báo cáo sinh tự động: `src/reports/crash.json` (20/20), `src/reports/jay_single_benchmark.json`, `src/reports/jay_ablation.json`
- Báo cáo nghiên cứu & cá nhân: `report/team/research_card.md`, `report/team/2A202603914_TranGiaBao.md`

## 2A202603887_TranThiHaAnh

### Phần việc phụ trách

- Triển khai Shape C (`src/lab8/shapes/orchestrator.py` — Orchestrator + Read-Only Investigator qua `handoff.v1`).
- Kiểm thử bảo mật handoff/trace (`src/tests/test_member3_orchestrator_security.py`) và chạy Benchmark 4 shape x 5 seed (`src/reports/benchmark.json`).
- Hoàn thiện `report/team/decision_adr.md` và viết phần Shape C (Mục 3) cùng Mục 4, 7, 8 của `report/team/group_report.md`.

### Đóng góp cụ thể

- Triển khai hoàn chỉnh Shape C (`src/lab8/shapes/orchestrator.py`): đọc claim qua `get_claim_view`, tạo gói chuyển giao `handoff.v1` đã lọc allowlist (`make_handoff`) chỉ cấp `READONLY_TOOLS` (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`), chạy `run_readonly_investigators` và giữ quyền gọi `durability.issue_refund` với full quote tại tầng Orchestrator, đạt `62/62 passed` trên student matrix.
- Viết bộ unit test bảo mật `src/tests/test_member3_orchestrator_security.py` (`5 passed`) kiểm tra `Trace contract v1`, chống rò rỉ `CANARY_SECRET_*` và PII ở T05/T10, kiểm tra allowlist của `handoff.v1` và tính idempotent khi chạy lại.
- Đối chiếu kết quả thực nghiệm của Shape C trên `src/reports/benchmark.json` (`pass_rate = 1.000`, `pass^5 = 1.000`, `variance = 0.000000`, `cost/success = 56.52 VND`, `mean_steps = 5.36`) để cùng nhóm chốt chọn `workflow` trong `report/team/decision_adr.md`.

### Bằng chứng

- Commit chính: `971feff` (`feat(orchestrator): implement orchestrator shape and security tests`), `492587b` (`docs(team): fill member 3 email in TEAM.md`)
- File code: `src/lab8/shapes/orchestrator.py`
- File test: `src/tests/test_member3_orchestrator_security.py` (`5 passed`)
- Báo cáo sinh tự động: `src/reports/benchmark.json`
- Báo cáo quyết định kiến trúc & cá nhân: `report/team/decision_adr.md`, `report/team/2A202603887_TranThiHaAnh.md`
