# Team

## Thông tin nhóm

- Tên nhóm: ConBoBietIuu
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents, `main`, (điền ở CP5)

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
| Bùi Đặng Nhật Nguyên (`2A202603937`) | `workflow + integration` | (cập nhật ở CP5) | `src/tests/test_member1_workflow.py` |
| Trần Gia Bảo (`2A202603914`) | `single + durability/crash` | (cập nhật ở CP5) | `src/tests/test_member2_single_and_crash.py` |
| Trần Thị Hà Anh (`2A202603887`) | `orchestrator + handoff + benchmark/adr` | (cập nhật ở CP5) | `src/tests/test_member3_orchestrator_security.py` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603937_BuiDangNhatNguyen

### Phần việc phụ trách

- Nhóm trưởng, quản lý tích hợp Git, kiểm soát chất lượng bài nộp (`check_submission`).
- Triển khai Shape A (`src/lab8/shapes/workflow.py`) và bộ kiểm thử `src/tests/test_member1_workflow.py`.
- Tổng hợp `TEAM.md` và `report/team/group_report.md` (Mục 1, 2, phần Shape A trong Mục 3, Mục 5, 6).

### Đóng góp cụ thể

- (Cập nhật chi tiết sau khi hoàn thành CP2–CP5)

### Bằng chứng

- File code: `src/lab8/shapes/workflow.py`
- File test: `src/tests/test_member1_workflow.py`
- Báo cáo cá nhân: `report/team/2A202603937_BuiDangNhatNguyen.md`

## 2A202603914_TranGiaBao

### Phần việc phụ trách

- Triển khai Shape B (`src/lab8/shapes/single.py` — Bounded ReAct Agent với `max_steps=8`).
- Kiểm thử Idempotency (T11), Crash Recovery (T12), chạy Crash Suite 20/20 (`src/reports/crash.json`) và viết bộ kiểm thử `src/tests/test_member2_single_and_crash.py`.
- Hoàn thiện `report/team/research_card.md` (kèm ablation) và viết phần Shape B trong Mục 3 của `report/team/group_report.md`.

### Đóng góp cụ thể

- (Cập nhật chi tiết sau khi hoàn thành CP2–CP5)

### Bằng chứng

- File code: `src/lab8/shapes/single.py`
- File test: `src/tests/test_member2_single_and_crash.py`
- Báo cáo sinh tự động: `src/reports/crash.json`
- Báo cáo nghiên cứu & cá nhân: `report/team/research_card.md`, `report/team/2A202603914_TranGiaBao.md`

## 2A202603887_TranThiHaAnh

### Phần việc phụ trách

- Triển khai Shape C (`src/lab8/shapes/orchestrator.py` — Orchestrator + Read-Only Investigator qua `handoff.v1`).
- Kiểm thử bảo mật handoff/trace (`src/tests/test_member3_orchestrator_security.py`) và chạy Benchmark 4 shape x 5 seed (`src/reports/benchmark.json`).
- Hoàn thiện `report/team/decision_adr.md` và viết phần Shape C (Mục 3) cùng Mục 4, 7, 8 của `report/team/group_report.md`.

### Đóng góp cụ thể

- (Cập nhật chi tiết sau khi hoàn thành CP2–CP5)

### Bằng chứng

- File code: `src/lab8/shapes/orchestrator.py`
- File test: `src/tests/test_member3_orchestrator_security.py`
- Báo cáo sinh tự động: `src/reports/benchmark.json`
- Báo cáo quyết định kiến trúc & cá nhân: `report/team/decision_adr.md`, `report/team/2A202603887_TranThiHaAnh.md`
