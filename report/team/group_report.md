# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: ConBoBietIuu
- Lớp: L3B
- Repository nhóm: https://github.com/double-n-021/K5-L3B-DAY08-ConBoBietIuu-FromWorkflowsToAgents
- Thành viên: xem [TEAM.md](../../TEAM.md) (Bùi Đặng Nhật Nguyên — `2A202603937`, Trần Gia Bảo — `2A202603914`, Trần Thị Hà Anh — `2A202603887`)
- Commit chốt (trùng `report/team/decision_adr.md`): `2acf9dc`

## 2. Mục tiêu và cách tiếp cận

### 2.1. Phân tích bài toán
Bài toán đặt ra là xây dựng hệ thống xử lý yêu cầu hoàn phí vận chuyển và bồi thường hỏng hàng của công ty giả lập LogiX-VN (`as_of = 2026-11-15`) trên bốn kiến trúc có mức độ tự chủ tăng dần: `workflow` (Shape A), `single` (Shape B — Bounded ReAct), `orchestrator` (Shape C — Orchestrator + Read-Only Investigator) và `swarm` (Shape D — kiến trúc đối chứng có sẵn).

Mục tiêu cốt lõi của nhóm là:
1. Thiết lập ranh giới chặt chẽ giữa **Deterministic Code**, **Host** và **MockLLM**: mọi phép tính tiền (`compute_compensation`), kiểm tra quyền sở hữu đơn hàng (`principal_id`), lọc điều khoản hiện hành (`is_current = 1`, `effective_date <= 2026-11-15`), kiểm tra chứng từ phê duyệt (`approval_id` khớp `claim_id`, `valid`, chưa hết hạn) và áp trần hoàn tiền theo đơn (`cap_per_order`) đều do code và tầng Host thực hiện.
2. Đảm bảo tuyệt đối 3 điều kiện **Must-Pass**: không hoàn tiền khi thiếu approval hợp lệ (`approval_bypass_count = 0`), không rò rỉ `CANARY_SECRET_*` hay PII trong trace/output (`secret_leak_count = 0`), và chịu lỗi crash đạt `20/20` (mỗi claim tối đa 1 dòng `refund_ledger` và 1 audit `refund_committed`).
3. So sánh định lượng 4 kiến trúc trên cùng tập dữ liệu và 5 seed (`11, 22, 33, 44, 55`) để lựa chọn kiến trúc **ít tự chủ nhất mà vẫn hoàn thành đúng nghiệp vụ với chi phí và độ dao động thấp nhất**.

### 2.2. Phân chia công việc và trình tự triển khai
Nhóm 3 thành viên chia mỗi người phụ trách độc lập 1 Shape và 1 file kiểm thử riêng biệt để làm việc song song không xung đột Git:
1. **Bùi Đặng Nhật Nguyên (`2A202603937`)**: Phụ trách `workflow + integration` (`src/lab8/shapes/workflow.py`, `src/tests/test_member1_workflow.py`, quản lý Git, `TEAM.md` và tổng hợp báo cáo).
2. **Trần Gia Bảo (`2A202603914`)**: Phụ trách `single + durability/crash` (`src/lab8/shapes/single.py`, `src/tests/test_member2_single_and_crash.py`, `src/reports/crash.json`, `report/team/research_card.md`).
3. **Trần Thị Hà Anh (`2A202603887`)**: Phụ trách `orchestrator + handoff + benchmark/adr` (`src/lab8/shapes/orchestrator.py`, `src/tests/test_member3_orchestrator_security.py`, `src/reports/benchmark.json`, `report/team/decision_adr.md`).

## 3. Giải pháp

### 3.1. Ranh giới giữa Code, Host và MockLLM
Trong cả ba shape nhóm triển khai, ranh giới bảo mật và tài chính được giữ thống nhất:
- **MockLLM (`src/lab8/mock_llm.py`)**: Chỉ dùng để soạn thảo câu chữ trả lời (`purpose="draft"`) hoặc chọn bước gọi công cụ đọc trong vòng lặp ReAct (`purpose="decide"`). Model không bao giờ tự tính số tiền, không tạo approval và không được gọi trực tiếp công cụ ghi (`WRITE_TOOLS`).
- **Shape Code (`workflow.py`, `single.py`, `orchestrator.py`)**: Chỉ đọc dữ liệu qua các read-only tool đã lọc allowlist (`get_claim_view`, `lookup_order`), tính mức bồi thường bằng `compute_compensation` trên dòng `order` có cấu trúc (bỏ qua con số hoặc lệnh điều khiển trong văn bản `ticket`), truyền **quote đầy đủ (full quote)** và tham số `crash_at` vào `durability.issue_refund`, không bắt nuốt `InjectedCrash`, và đóng gói mọi nhánh trả về qua `lab8.shapes.common.finish()`.
- **Host (`durability.py`, `policy.py`, `handoff.py`)**: Thực thi kiểm tra quyền sở hữu, kiểm tra approval gắn đúng `claim_id`, tự động trừ phần tiền các claim trước đã nhận trên cùng đơn hàng (`order_refunded_vnd`) bên trong transaction `BEGIN IMMEDIATE`, đảm bảo idempotency bằng khóa `refund:{claim_id}` và ghi audit `policy_denied` / `refund_committed`.

### 3.2. Shape A — Workflow (`src/lab8/shapes/workflow.py` — Bùi Đặng Nhật Nguyên, commit `f73d097`)
Triển khai theo luồng tuần tự cố định:
1. Mở kết nối SQLite trong khối `try ... finally: conn.close()` và đọc claim qua `get_claim_view(conn, claim_id)` (loại bỏ `parent_secret` và `raw_headers_json`). Nếu `not claim["found"]` thì trả `status="failed"` (`error_reason="unknown_claim"`).
2. Nếu thiếu `order_id` (T04) -> trả sớm `status="needs_info"`, `proposal_amount=0`.
3. Gọi `lookup_order(conn, claim["order_id"], claim["principal_id"])` (loại bỏ `phone`, `address`, `internal_note`, `item_name`). Nếu `not order_view["visible"]` (T05) -> trả `status="escalated"`, `proposal_amount=0`.
4. Gọi `compute_compensation(conn, order_view["order"])` lấy `proposal = int(quote_payload["amount_vnd"])`. Nếu `proposal <= 0` (T02, T06, T09) -> trả `status="denied"`, `proposal_amount=0` và không gọi `issue_refund`.
5. Nếu `proposal > 0` -> gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với full quote. Nếu gặp `InjectedCrash`, ghi sự kiện `crash` vào trace, gọi `trace.write()` rồi `raise` lại ngay. Nếu Host từ chối (`not outcome["ok"]`), trả `failed` khi `conflict=True` hoặc `denied` (với `proposal_amount=proposal` cho T07, T13). Nếu thành công, trả `resolved` (`proposal_amount=proposal` cho T01, T03, T08, T10, T11, T12, T14).
6. **Trace events của `workflow`**: Chỉ ghi các sự kiện sạch gồm `claim_view` (`claim_id`, `principal_id`, `order_id`), `lookup_order`, `quote`, `decision` (và `error` / `crash` nếu có).

### 3.3. Shape B — Bounded Single ReAct Agent (`src/lab8/shapes/single.py` — Trần Gia Bảo, commit `b32666f`)
1. **Kiến trúc & Ranh giới Quyền hạn (Model vs Code vs Host):**
   - Shape B triển khai một Agent đơn lẻ hoạt động theo vòng lặp ReAct (`lab8.runtime.run_react`) với giới hạn cứng `max_steps=8` và cờ `worker=True`.
   - Model chỉ được phép chọn các công cụ đọc (`lookup_order`, `compute_compensation`). Quyền ghi tiền (`issue_refund`) hoàn toàn nằm ở code của Shape bên ngoài vòng lặp ReAct và được kiểm soát chặt chẽ bởi Host.
2. **Quy trình xử lý tuần tự trong ReAct (3 bước):**
   - *Bước 1:* Gọi `lookup_order` với `principal_id` của claim. Nếu đơn hàng không hợp lệ hoặc không thuộc quyền sở hữu của khách hàng (`visible=False`), dừng vòng lặp và trả về trạng thái `escalated`.
   - *Bước 2:* Dùng dữ liệu thật từ bảng `orders` để gọi `compute_compensation` tính toán số tiền bồi hoàn theo policy hiện hành. Không tin vào số ngày trễ hay điều khoản cũ ghi trong `ticket` của khách hàng.
   - *Bước 3:* Nhận quote hoàn tiền và kết thúc vòng lặp ReAct (`done`).
3. **Cơ chế Ghi tiền, Idempotency & Crash Recovery:**
   - Nếu `proposal <= 0`: Trả về `denied`, tuyệt đối không gọi `issue_refund`.
   - Nếu `proposal > 0`: Gọi `durability.issue_refund` với **full quote** và chuyển tiếp tham số `crash_at`. Khi xảy ra sự cố (`InjectedCrash` tại các điểm `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`), trace được flush và ngoại lệ được lan truyền ra ngoài không bị nuốt. Khi retry/resume, hệ thống tận dụng idempotency key `refund:{claim_id}` để đảm bảo đúng 1 dòng hoàn tiền.
4. **Trace events của `single`**: Chỉ ghi nhận tóm tắt trạng thái sau khi đã sanitize (`claim`, `lookup_order`, `quote`, `decision`, `error` / `crash`), loại bỏ toàn bộ `ticket` thô, `parent_secret`, token Bearer và PII.

### 3.4. Shape C — Orchestrator & Handoff Security (`src/lab8/shapes/orchestrator.py` — Trần Thị Hà Anh, commit `971feff`)
1. Orchestrator đọc thông tin claim qua `get_claim_view` (không truy cập `parent_secret` hay `raw_headers_json`). Nếu `not claim["found"]` -> trả `failed` (`unknown_claim`); nếu thiếu `order_id` -> trả `needs_info`.
2. Xây dựng gói dữ liệu chuyển giao `handoff.v1` bằng `lab8.handoff.make_handoff` với `facts={}` (không chuyển văn bản `ticket` của người dùng sang worker) và chỉ cấp danh sách công cụ đọc `INVESTIGATOR_TOOLS = ["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"]`.
3. Ghi sự kiện `handoff` đã qua `safe_dump(handoff)` vào `Trace`, sau đó gọi `run_readonly_investigators(conn, budget, handoff, principal_id=claim["principal_id"])`.
4. Kiểm tra kết quả từ Investigator: nếu `not order_view.get("visible")` -> trả `escalated` (`proposal_amount=0`). Lấy `proposal` từ `compute_compensation`, nếu `proposal <= 0` -> trả `denied` (`proposal_amount=0`).
5. Khi `proposal > 0`, chính Orchestrator (không phải Investigator) gọi `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **full quote**, bắt riêng `InjectedCrash` để flush `trace.write()` rồi `raise` lại ngay, và đóng gói mọi nhánh trả về qua `finish()`.
6. **Trace events của `orchestrator`**: Ghi các sự kiện đã lọc allowlist gồm `claim`, `handoff`, `investigator` (`lookup_order`, `refund_history`), `quote`, `host`, `decision` (và `crash` nếu có).

## 4. Kết quả

### 4.1. Bảng so sánh 4 Shape trên bộ Public (`src/reports/benchmark.json`)
Điều kiện thực nghiệm cố định: 14 claim public (`C-001` đến `C-014`) x 5 seed (`11, 22, 33, 44, 55`) = 70 trials/shape, `as_of = 2026-11-15`, bảng giá mô phỏng `config/pricing.yaml` (`input: 20 VND/1k`, `output: 80 VND/1k`, `tool: 10 VND/call`), mỗi trial chạy trên một cơ sở dữ liệu SQLite mới hoàn toàn (`fresh_sqlite_per_trial`).

| Shape | Trials (Pass/Total) | Pass Rate | Pass^5 | Seed Min – Max | Seed Variance | Cost / Success (VND, mô phỏng) | Total Cost (VND) | Mean / p95 Steps | Mean Model / Tool Calls |
| --- | :---: | ---: | ---: | :---: | ---: | ---: | ---: | :---: | :---: |
| **`workflow` (Chọn)** | 70 / 70 | **1.000** | **1.000** | 1.000 – 1.000 | **0.000000** | **28.79** | 2015.00 | 3.79 / 4.0 | 1.00 / 2.79 |
| `single` | 70 / 70 | **1.000** | **1.000** | 1.000 – 1.000 | **0.000000** | 30.03 | 2102.00 | 3.79 / 4.0 | 3.71 / 2.79 |
| `orchestrator` | 70 / 70 | **1.000** | **1.000** | 1.000 – 1.000 | **0.000000** | 56.52 | 3956.10 | 5.36 / 6.0 | 0.86 / 5.57 |
| `swarm` (Đối chứng) | 69 / 70 | 0.986 | 0.929 | 0.929 – 1.000 | 0.000816 | 49.57 | 3420.12 | 2.80 / 3.0 | 3.00 / 4.66 |

### 4.2. Độ an toàn Crash Recovery & Bảo mật (`src/reports/crash.json` & Test Matrix)
- **Crash Safety (`src/reports/crash.json`):** Đạt **20/20** (`CR-01` đến `CR-20`: 5 kịch bản `before_effect`, 7 kịch bản `after_effect_before_checkpoint`, 5 kịch bản `after_checkpoint`, 1 kịch bản `amount_conflict_on_retry`, 1 kịch bản `retry_without_approval`, 1 kịch bản `swarm_after_effect_before_checkpoint`).
- **Ma trận kiểm thử (`pytest`):**
  - Cổng Host + Unit Tests của 3 thành viên (`python -m pytest -q`): **91 passed, 0 failed**.
  - Ma trận Student trên cả 4 shape (`python -m pytest -q -m student -o addopts=`): **248 passed, 0 failed**.
- **Quyết định kiến trúc:** Nhóm chọn **`workflow`** vì đạt đồng thời `pass_rate = 1.000`, `pass^5 = 1.000`, `seed_variance = 0.000000` với chi phí thấp nhất (**28.79 VND/success**). Phân tích chi tiết nằm tại [report/team/decision_adr.md](decision_adr.md) và kết quả nghiên cứu ablation R4 nằm tại [report/team/research_card.md](research_card.md).

### 4.3. Tự kiểm trên bộ Hidden (`src/reports/hidden_selfcheck.json`)
Chạy tự kiểm trên bộ `student_drop/` do lab coach phát (40 claim không nhãn `C-H01` đến `C-H40` x 5 seed `11, 22, 33, 44, 55` = **200 trials/shape**, không có đáp án nên chỉ kiểm tra runtime, Trace Contract v1 và dấu hiệu rò rỉ):

| Shape | Trials | Trace hợp lệ (`unlabeled`) | `error_trials` | `leak_suspect_trials` | Phân bố `status` (200 trials) | Total Cost (VND, mô phỏng) | Mean / p95 Steps |
| --- | :---: | :---: | :---: | :---: | --- | ---: | :---: |
| **`workflow` (Chọn)** | 200 | 200 / 200 | **0** | **0** | `denied: 95`, `resolved: 90`, `escalated: 10`, `needs_info: 5` | **5,985.30** | 3.90 / 4.0 |
| `single` | 200 | 200 / 200 | **0** | **0** | `denied: 95`, `resolved: 90`, `escalated: 10`, `needs_info: 5` | 6,247.90 | 3.90 / 4.0 |
| `orchestrator` | 200 | 200 / 200 | **0** | **0** | `denied: 95`, `resolved: 90`, `escalated: 10`, `needs_info: 5` | 11,822.70 | 5.50 / 6.0 |

Cả ba shape (`workflow`, `single`, `orchestrator`) **đồng thuận 100%** về `status` trên toàn bộ 200 cặp `(claim_id, seed)` (`0` điểm sai khác), `0` lỗi runtime và `0` nghi ngờ rò rỉ secret; `workflow` tiếp tục giữ mức chi phí mô phỏng thấp nhất.

## 5. Khó khăn và cách xử lý

1. **Rủi ro trừ kép trần hoàn tiền theo đơn ở T14 (`C-014`, đơn `O-515`)**:
   - **Vấn đề**: Đơn `O-515` đã được hoàn 30.000 VND phí ship ở claim lịch sử `C-HIST-515`, nay phát sinh hỏng hàng đã xác minh với entitlement 150.000 VND. Nếu shape tự dùng `lookup_refund_history` để trừ `150000 - 30000 = 120000` trước khi truyền vào `durability.issue_refund`, hàm `policy.authorize` của Host sẽ trừ tiếp 30.000 VND lần thứ hai còn 90.000 VND và làm sai cả `proposal_amount`.
   - **Cách xử lý**: Tuân thủ nghiêm ngặt hợp đồng truyền **full quote (`150000`)** vào `issue_refund` và giữ nguyên `proposal_amount = 150000` trong `RunResult`; để Host tự thực hiện phép trừ trong transaction ghi ledger (`refund_vnd = 120000`).
2. **Xử lý `InjectedCrash` và đảm bảo Trace Contract v1 ở T12 (`C-012`)**:
   - **Vấn đề**: Ở kịch bản `crash_at="after_effect_before_checkpoint"`, nếu shape dùng `try ... except Exception` bắt nuốt ngoại lệ thì test T12 báo `crash did not fire`; ngược lại nếu không ghi trace ở các nhánh thoát sớm (`needs_info`, `escalated`) thì grader fail-closed với lỗi `missing_trace`.
   - **Cách xử lý**: Bắt riêng `InjectedCrash` chỉ để ghi sự kiện `crash` và `trace.write()`, sau đó `raise` lại ngay lập tức; mọi nhánh kết thúc bình thường đều trả qua `lab8.shapes.common.finish()`.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp, mã commit và file kiểm thử của từng thành viên được khai báo đầy đủ trong [TEAM.md](../../TEAM.md) (bảng `## Bảng đóng góp`) và 3 báo cáo cá nhân:
- [report/team/2A202603937_BuiDangNhatNguyen.md](2A202603937_BuiDangNhatNguyen.md) (Commit `f73d097`, 8 tests trong `test_member1_workflow.py`)
- [report/team/2A202603914_TranGiaBao.md](2A202603914_TranGiaBao.md) (Commit `b32666f`, 24 tests trong `test_member2_single_and_crash.py`)
- [report/team/2A202603887_TranThiHaAnh.md](2A202603887_TranThiHaAnh.md) (Commit `971feff`, 5 tests trong `test_member3_orchestrator_security.py`)

## 7. Hạn chế và hướng cải thiện

- **Giới hạn của MockLLM và Chi phí mô phỏng:** `MockLLM` chỉ sinh chuỗi cố định theo băm `sha256(seed|purpose|prompt)` và tính giá giả lập theo `src/config/pricing.yaml` (không phải hóa đơn API thực tế); độ trễ (`latency`) là `unavailable`.
- **Điều kiện làm kết luận thay đổi:** Trong bài toán hiện tại, dữ liệu đơn hàng đã được chuẩn hóa trong bảng `orders` nên `workflow` đạt hiệu quả tối ưu. Nếu mở rộng sang bài toán mà quy trình thu thập bằng chứng phụ thuộc động vào nội dung sự cố phức tạp (cần tra cứu linh hoạt nhiều hệ thống), `single` (Bounded ReAct) sẽ phù hợp hơn; hoặc nếu cần cô lập vùng bảo mật cứng giữa tiến trình điều phối và các tác nhân bên thứ ba, `orchestrator` kèm `handoff.v1` sẽ phát huy tác dụng.

## 8. Tài liệu tham khảo

1. Tài liệu bài Lab 8 LogiX-VN: `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`.
2. Google Research (2026), *Towards a Science of Scaling Agent Systems*.
3. Cemri et al. (NeurIPS 2025), *MAST: Why Do Multi-Agent LLM Systems Fail?*.
4. Zhang et al. (EMNLP 2026), *Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems*, https://aclanthology.org/2026.emnlp-main.798/.
5. DBOS, *Durable Workflows and Steps — Exactly-Once Execution with Database Transactions*.
