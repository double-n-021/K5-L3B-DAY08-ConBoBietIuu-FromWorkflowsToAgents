# Kế hoạch Phân công & Hướng dẫn Triển khai Nhóm 3 Người — Lab 8 (LogiX-VN)

- **Bài Lab:** K5 — Day 08: From Workflows to Agents (LogiX-VN)
- **Tên nhóm:** `ConBoBietIuu` (Lớp `L3B`)
- **URL Repository nhóm:** https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents

| STT | Thành viên | MSSV | GitHub | Vai trò trong nhóm (`TEAM.md`) | File Báo cáo cá nhân (Lab 8) |
| --: | --- | --- | --- | --- | --- |
| 1 | **Bùi Đặng Nhật Nguyên** (Nhóm trưởng) | `2A202603937` | `double-n-021` | `workflow + integration` | [2A202603937_BuiDangNhatNguyen.md](../report/team/2A202603937_BuiDangNhatNguyen.md) |
| 2 | **Trần Gia Bảo** | `2A202603914` | `Jay-Gabriel` | `single + durability/crash` | [2A202603914_TranGiaBao.md](../report/team/2A202603914_TranGiaBao.md) |
| 3 | **Trần Thị Hà Anh** | `2A202603887` | `hnha02` | `orchestrator + handoff + benchmark/adr` | [2A202603887_TranThiHaAnh.md](../report/team/2A202603887_TranThiHaAnh.md) |

---

## 1. Cài đặt Môi trường trên Máy Cá nhân (15 phút đầu — CP1)

Cả 3 thành viên clone **repo nhóm** về máy. Mọi lệnh chạy của Lab 8 đều thực hiện bên trong thư mục `src/`:

### Windows (PowerShell)

```powershell
git clone https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents.git
cd K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents\src
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m lab8.smoke
python -m pytest -q
```

*(Nếu PowerShell báo lỗi chặn script, chạy `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi activate lại).*

### macOS / Linux (hoặc Git Bash)

```bash
git clone https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents.git
cd K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents/src
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m lab8.smoke
python -m pytest -q
```

**Dấu hiệu cài đặt thành công:**
- `python -m lab8.smoke` in ra `lab8.smoke pass`.
- `python -m pytest -q` báo `54 passed` (`0 failed`).

---

## 2. Bảng Phân công Tổng thể (Mỗi người 1 Kiến trúc + 1 File Test + 1 Phần Báo cáo)

Đề bài Lab 8 yêu cầu nhóm cài đặt **3 kiến trúc (Shape A, Shape B, Shape C)** để xử lý yêu cầu hoàn phí vận chuyển của công ty LogiX-VN, rồi so sánh với kiến trúc có sẵn `swarm_reference.py`:

| Thành viên | File Code chính cần viết (CP2–CP3) | File Test riêng cần tạo (`src/tests/`) | Việc cần làm ở CP4–CP5 & Báo cáo |
| --- | --- | --- | --- |
| **1. Nhật Nguyên** (`2A202603937`) | [src/lab8/shapes/workflow.py](../src/lab8/shapes/workflow.py) (Shape A: Quy trình Python cố định) | `src/tests/test_member1_workflow.py` | - Quản lý Git & cập nhật [TEAM.md](../TEAM.md)<br>- Viết Mục 1, 2, Shape A (Mục 3), 5, 6 trong [group_report.md](../report/team/group_report.md)<br>- Hoàn thiện [2A202603937_BuiDangNhatNguyen.md](../report/team/2A202603937_BuiDangNhatNguyen.md)<br>- Chạy chốt `python -m lab8.check_submission` đạt `0 FAIL` |
| **2. Gia Bảo** (`2A202603914`) | [src/lab8/shapes/single.py](../src/lab8/shapes/single.py) (Shape B: Vòng lặp Single ReAct Agent) | `src/tests/test_member2_single_and_crash.py` | - Chạy lệnh sinh `src/reports/crash.json` đạt `20/20`<br>- Điền [research_card.md](../report/team/research_card.md) + chạy thực nghiệm ablation<br>- Viết phần Shape B (Mục 3) trong [group_report.md](../report/team/group_report.md)<br>- Hoàn thiện [2A202603914_TranGiaBao.md](../report/team/2A202603914_TranGiaBao.md) |
| **3. Hà Anh** (`2A202603887`) | [src/lab8/shapes/orchestrator.py](../src/lab8/shapes/orchestrator.py) (Shape C: Orchestrator + Investigator chỉ đọc) | `src/tests/test_member3_orchestrator_security.py` | - Chạy lệnh sinh `src/reports/benchmark.json` (4 shape x 5 seed)<br>- Điền [decision_adr.md](../report/team/decision_adr.md)<br>- Viết phần Shape C (Mục 3) + Mục 4, 7, 8 trong [group_report.md](../report/team/group_report.md)<br>- Hoàn thiện [2A202603887_TranThiHaAnh.md](../report/team/2A202603887_TranThiHaAnh.md) |

---

## 3. Hướng dẫn Việc Cụ thể cho Từng Thành viên

### 3.1. Công việc của Bùi Đặng Nhật Nguyên (`workflow + integration`)

1. **Viết code Shape A tại [src/lab8/shapes/workflow.py](../src/lab8/shapes/workflow.py)**:
   - Mở kết nối SQLite `conn = connect(store_path)` và đóng trong `finally: conn.close()`.
   - Đọc claim bằng `get_claim_view(conn, claim_id)`:
     - Nếu `not claim["found"]` -> trả `status="failed"`, `error_reason="unknown_claim"`, `proposal_amount=0`.
     - Nếu thiếu `order_id` -> trả `status="needs_info"`, `proposal_amount=0`.
   - Đọc đơn hàng bằng `lookup_order(conn, claim["order_id"], claim["principal_id"])`:
     - Nếu `not order_view["visible"]` -> trả `status="escalated"`, `proposal_amount=0`.
   - Tính số tiền hoàn bằng code: `quote_payload = compute_compensation(conn, order_view["order"])` (bỏ qua số ngày trễ viết trong `ticket`).
   - Nếu `proposal <= 0` -> trả `status="denied"`, `proposal_amount=0` (không gọi `issue_refund`).
   - Nếu `proposal > 0` -> gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **full quote** (không tự trừ tiền đã hoàn trước đó) và không bắt nuốt `InjectedCrash`:
     - Nếu `outcome["ok"]` là `True` -> trả `status="resolved"`, `proposal_amount=proposal`.
     - Nếu `outcome["conflict"]` là `True` -> trả `status="failed"`, `proposal_amount=proposal`.
     - Ngược lại -> trả `status="denied"`, `proposal_amount=proposal`.
   - Mọi nhánh return đều gọi `finish(...)` trong [src/lab8/shapes/common.py](../src/lab8/shapes/common.py).
2. **Chạy lệnh tự kiểm tra (tại `src/`)**:
   ```powershell
   python -m pytest -q -m student -o addopts= -k workflow
   ```
   Mục tiêu: **`62 passed`**.
3. **Viết file test riêng**: Tạo `src/tests/test_member1_workflow.py` (kiểm tra T02 không tin ticket nói dối và T14 hoàn đúng phần chênh lệch).
4. **Hoàn thiện hồ sơ**: Cập nhật [TEAM.md](../TEAM.md), ghép [group_report.md](../report/team/group_report.md), cập nhật commit hash vào [2A202603937_BuiDangNhatNguyen.md](../report/team/2A202603937_BuiDangNhatNguyen.md) và chạy `python -m lab8.check_submission` đạt `0 FAIL`.

---

### 3.2. Công việc của Trần Gia Bảo (`single + durability/crash`)

1. **Viết code Shape B tại [src/lab8/shapes/single.py](../src/lab8/shapes/single.py)**:
   - Kiểm tra claim bằng `get_claim_view` (`unknown_claim` -> `failed`; thiếu `order_id` -> `needs_info`).
   - Sử dụng `run_react(conn, budget, observation={"claim": claim}, decide=decide, max_steps=8, worker=True)` từ [src/lab8/runtime.py](../src/lab8/runtime.py):
     - Trong hàm `decide(obs)`, gọi `complete(budget, seed=seed, purpose=..., prompt=...)` để tính `model_calls` vào `Budget`.
     - Lưu kết quả giữa các bước vào biến cục bộ (vì `run_react` ghi đè `seen` sau mỗi bước): Bước 1 chọn tool `"lookup_order"` -> nếu đơn không `visible` thì dừng bằng `{"final": {"status": "escalated"}}` -> Bước 2 chọn tool `"compute_compensation"` trên `order_view["order"]` -> Bước 3 dừng bằng `{"final": {"status": "done", "quote": ...}}`.
     - Tuyệt đối không gọi `issue_refund` trong `decide`.
   - Sau khi `run_react` kết thúc, nếu `proposal > 0` thì code của `single.py` gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **full quote**, không bắt nuốt `InjectedCrash`, và trả kết quả qua `finish(...)`.
2. **Chạy lệnh tự kiểm tra và sinh báo cáo Crash (tại `src/`)**:
   ```powershell
   python -m pytest -q -m student -o addopts= -k single
   python -m lab8.crash_test --count 20 --out reports/crash.json
   ```
   Mục tiêu: **`62 passed`** cho `single` và **`crash_safety 20/20`** trong `src/reports/crash.json`.
3. **Viết file test riêng**: Tạo `src/tests/test_member2_single_and_crash.py` (kiểm tra `single` dừng trong `<= 8` bước, chống prompt injection T09, và kiểm tra crash `after_effect_before_checkpoint` + resume giữ đúng 1 dòng ledger).
4. **Hoàn thiện hồ sơ**: Điền [research_card.md](../report/team/research_card.md), viết phần Shape B trong Mục 3 của [group_report.md](../report/team/group_report.md), và cập nhật commit hash vào [2A202603914_TranGiaBao.md](../report/team/2A202603914_TranGiaBao.md).

---

### 3.3. Công việc của Trần Thị Hà Anh (`orchestrator + handoff + benchmark/adr`)

1. **Viết code Shape C tại [src/lab8/shapes/orchestrator.py](../src/lab8/shapes/orchestrator.py)**:
   - Kiểm tra claim bằng `get_claim_view` (`unknown_claim` -> `failed`; thiếu `order_id` -> `needs_info`).
   - Tạo gói chuyển giao đã lọc allowlist bằng `make_handoff` trong [src/lab8/handoff.py](../src/lab8/handoff.py):
     ```python
     handoff = make_handoff(
         request_id=f"REQ-{claim_id}",
         claim_id=claim_id,
         task="check_applicable_policy",
         facts={},
         allowed_tools=["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"],
     )
     ```
   - Ghi `safe_dump(handoff)` vào `trace` (tuyệt đối không đưa `parent_secret`, `raw_headers` hay raw claim row vào `facts` hoặc `trace`).
   - Chạy Investigator chỉ đọc: `investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim["principal_id"])`.
   - Kiểm tra `order_view = investigated["tools"].get("lookup_order", {})`: nếu `not order_view.get("visible")` -> trả `status="escalated"`, `proposal_amount=0`.
   - Lấy `quote_payload = investigated["tools"]["compute_compensation"]`: nếu `proposal <= 0` -> trả `status="denied"`, `proposal_amount=0`; nếu `proposal > 0` -> Orchestrator gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **full quote**, không bắt nuốt `InjectedCrash`, và trả kết quả qua `finish(...)`.
2. **Chạy lệnh tự kiểm tra và sinh báo cáo Benchmark (tại `src/`)**:
   ```powershell
   python -m pytest -q -m student -o addopts= -k orchestrator
   python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
   ```
   Mục tiêu: **`62 passed`** cho `orchestrator` và sinh đầy đủ `src/reports/benchmark.json` (khi cả 3 shape đã xong).
3. **Viết file test riêng**: Tạo `src/tests/test_member3_orchestrator_security.py` (kiểm tra `orchestrator` trên T05 và T10 đảm bảo trace hợp lệ và không lộ `CANARY_SECRET_*` hay PII).
4. **Hoàn thiện hồ sơ**: Điền số liệu từ `benchmark.json` vào [decision_adr.md](../report/team/decision_adr.md), viết phần Shape C (Mục 3) cùng Mục 4, 7, 8 trong [group_report.md](../report/team/group_report.md), và cập nhật commit hash vào [2A202603887_TranThiHaAnh.md](../report/team/2A202603887_TranThiHaAnh.md).

---

## 4. Checklist 5 Điều kiện Bắt buộc Trước khi Nộp Bài

1. **Mỗi thành viên có ít nhất 1 commit và 1 file test riêng**:
   - Nhật Nguyên: `src/lab8/shapes/workflow.py` + `src/tests/test_member1_workflow.py`
   - Gia Bảo: `src/lab8/shapes/single.py` + `src/tests/test_member2_single_and_crash.py`
   - Hà Anh: `src/lab8/shapes/orchestrator.py` + `src/tests/test_member3_orchestrator_security.py`
2. **Ba file báo cáo cá nhân đã có sẵn trong `report/team/`** (đã tạo sẵn khung chuẩn Lab 8, mỗi người chỉ cần điền thêm mã commit hash của mình sau khi push; **không xóa** file mẫu [MSSV_HoTen.md](../report/team/MSSV_HoTen.md)):
   - [report/team/2A202603937_BuiDangNhatNguyen.md](../report/team/2A202603937_BuiDangNhatNguyen.md)
   - [report/team/2A202603914_TranGiaBao.md](../report/team/2A202603914_TranGiaBao.md)
   - [report/team/2A202603887_TranThiHaAnh.md](../report/team/2A202603887_TranThiHaAnh.md)
3. **Không sửa các file bị cấm**: Tuyệt đối không sửa `metrics.py`, `durability.py`, `policy.py`, `compensation.py`, `tools.py`, `handoff.py`, `runtime.py`, `swarm_reference.py`, `src/config/*.yaml`, `src/data/*`, và không sửa tay file JSON trong `src/reports/`.
4. **Kiểm tra toàn bộ bài nộp (tại `src/`)**:
   ```powershell
   python -m pytest -q
   python -m pytest -q -m student -o addopts=
   python -m lab8.check_submission
   ```
   Cả 3 lệnh đều phải xanh và `check_submission` báo **`0 FAIL`**.
5. **Nộp link trên LMS**: Cả 3 thành viên đều phải tự đăng nhập LMS bằng tài khoản cá nhân và nộp cùng link `https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents` trước deadline.
