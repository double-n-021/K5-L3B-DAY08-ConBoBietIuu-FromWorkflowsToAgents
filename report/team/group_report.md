# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

...

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

### Shape A — Workflow (Bùi Đặng Nhật Nguyên)
*(Nhật Nguyên hoàn thiện)*

### Shape B — Bounded Single ReAct Agent (Trần Gia Bảo - 2A202603914)

1. **Kiến trúc & Ranh giới Quyền hạn (Model vs Code vs Host):**
   - Shape B triển khai một Agent đơn lẻ hoạt động theo vòng lặp ReAct (`lab8.runtime.run_react`) với giới hạn cứng `max_steps=8` và cờ `worker=True`.
   - **Ranh giới an toàn tuyệt đối:** Model chỉ được phép chọn các công cụ đọc (`lookup_order`, `compute_compensation`). Quyền ghi tiền (`issue_refund`) hoàn toàn nằm ở code của Shape bên ngoài vòng lặp ReAct và được kiểm soát chặt chẽ bởi Host. Model tuyệt đối không thể tự cấp quyền hay ghi trực tiếp vào SQLite.
2. **Quy trình xử lý tuần tự (3 bước):**
   - *Bước 1:* Gọi `lookup_order` với `principal_id` của claim. Nếu đơn hàng không hợp lệ hoặc không thuộc quyền sở hữu của khách hàng (`visible=False`), dừng vòng lặp và trả về trạng thái `escalated`.
   - *Bước 2:* Dùng dữ liệu thật từ bảng `orders` để gọi `compute_compensation` tính toán số tiền bồi hoàn theo policy hiện hành. Không tin vào số ngày trễ hay điều khoản cũ ghi trong `ticket` của khách hàng.
   - *Bước 3:* Nhận quote hoàn tiền và kết thúc vòng lặp ReAct (`done`).
3. **Cơ chế Ghi tiền, Idempotency & Crash Recovery:**
   - Nếu `proposal <= 0`: Trả về `denied`, tuyệt đối không gọi `issue_refund`.
   - Nếu `proposal > 0`: Gọi `durability.issue_refund` với **full quote** và chuyển tiếp tham số `crash_at`. Host sẽ kiểm tra trần chi trả của đơn hàng, đối chiếu lịch sử refund trước đó, và ghi vào bảng `refund_ledger` kèm audit event trong cùng một transaction SQLite duy nhất với khóa `refund:{claim_id}`.
   - Khi xảy ra sự cố (`InjectedCrash` tại các điểm `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`), ngoại lệ được lan truyền ra ngoài không bị nuốt. Khi retry/resume, hệ thống tận dụng idempotency key để đảm bảo không bao giờ phát sinh 2 dòng hoàn tiền cho cùng 1 claim.
4. **Bảo mật & Trace Contract v1:**
   - Nhật ký trace chỉ ghi nhận tóm tắt trạng thái sau khi đã sanitize (loại bỏ toàn bộ `ticket` thô, không ghi các trường nhạy cảm như `parent_secret`, token Bearer, số điện thoại, địa chỉ hay ghi chú nội bộ).
   - Trace luôn được khởi tạo và ghi ra đĩa cho mọi nhánh kết thúc (kể cả early return hay crash).

### Shape C — Orchestrator + Read-Only Investigator (Trần Thị Hà Anh)
*(Hà Anh hoàn thiện)*

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

...

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

...

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
