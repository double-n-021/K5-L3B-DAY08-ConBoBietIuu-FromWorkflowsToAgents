# Research card — R4: Evaluation Confounders

## Phiếu nghiên cứu của nhóm

| Field | Mô tả tiêu chí | Nhóm điền |
| --- | --- | --- |
| CÂU | Câu hỏi nghiên cứu lựa chọn | R4 · Evaluation confounders (Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed?) |
| SOURCE | Nguồn bài báo và loại bằng chứng | Zhang et al., EMNLP 2026, *Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems*, https://aclanthology.org/2026.emnlp-main.798/, benchmark chẩn đoán thực nghiệm |
| CLAIM | Kết luận gốc của nguồn | Các kỹ thuật cấu trúc và các bước gọi LLM phụ trợ trong agent pipeline thường bị phóng đại hiệu quả thực tế nếu không cô lập chuẩn xác các biến gây nhiễu (prompt, seed, số lượt gọi LLM phụ trợ) |
| BOUNDARY | Phạm vi và giới hạn của nguồn | Khảo sát trên các benchmark ngôn ngữ tự nhiên và hệ thống MAS đồng nhất (homogeneous agents chia sẻ mô hình nền), đánh giá cấu trúc topology và các phương pháp pruning/giao tiếp. Không mở rộng cho các hệ thống có agent mang mục tiêu xung đột hoặc môi trường bất định cao |
| HYPOTHESIS | Giả thuyết kiểm chứng trên LogiX-VN | Đối với Single ReAct Agent, bước gọi model soạn câu trả lời draft ở cuối pipeline không can thiệp vào logic tính quote hay duyệt chi của Host; khi loại bỏ bước draft (treatment arm), pass rate và pass^5 sẽ giữ nguyên không đổi, số lượt gọi model trung bình (mean_model_calls) sẽ giảm đúng 1 cuộc gọi trên mỗi trial thành công có draft, và chi phí mô phỏng cost/success sẽ giảm tương ứng mà không làm thay đổi bất kỳ bản ghi nghiệp vụ hay số tiền hoàn nào |
| METHOD | Biến cố định và biến thay đổi | Cố định: 14 public claims, seeds 11/22/33/44/55, MockLLM, read tools (lookup_order, compute_compensation), policy, pricing config, fresh SQLite per trial. Biến duy nhất thay đổi: Tắt lời gọi complete(..., purpose='draft') ở cuối pipeline |
| FAILURE / METRIC | Thước đo và điều kiện bác bỏ giả thuyết | Đo bằng pass_rate, pass^5, variance, cost/success, mean_model_calls. Kiểm tra đối chứng trực tiếp trên 70 cặp database độc lập giữa 2 nhánh: status, proposal_amount, refund_ledger (số dòng, số tiền), audit refund_committed, và audit policy_denied. Nếu bỏ draft làm sai lệch bất kỳ trường nào trong các đối chiếu trên hoặc không giảm chi phí thì hypothesis thất bại |

## Kết quả ablation

- **Lệnh thực thi:**
  `python -m bonus.jay_ablation --out reports/jay_ablation.json`
- **File báo cáo:**
  `src/reports/jay_ablation.json` (chứa toàn bộ `baseline_report` và `treatment_report`)
- **Kết quả đối chiếu với giả thuyết:**
  **Xác nhận giả thuyết (Đạt)**:
  - Baseline: `pass_rate` = 1.0, `pass_5` = 1.0, `mean_model_calls` = 3.71, `cost/success` = 30.03 VND, `mean_steps` = 3.79.
  - Treatment (No Draft): `pass_rate` = 1.0, `pass_5` = 1.0, `mean_model_calls` = 2.71 (delta: -1.00), `cost/success` = 29.05 VND (delta: -0.98 VND), `mean_steps` = 3.79.
  - Kiểm tra đối chiếu DB trực tiếp (Paired DB verification): 70/70 cặp database độc lập (14 claim × 5 seed) đạt 0 điểm sai lệch (`PASS (0 mismatches)`: status, proposal_amount, số tiền hoàn thực tế trong `refund_ledger`, audit `refund_committed` và audit `policy_denied` hoàn toàn trùng khớp).
- Giới hạn:
  - **Giới hạn phòng lab (MockLLM)**: Môi trường LogiX-VN sử dụng MockLLM với chi phí token và lượt gọi mô phỏng, latency là `unavailable`; câu trả lời draft không được grader chấm nên thí nghiệm tập trung đo lường tính bất biến logic và chi phí mô phỏng.
  - **Giới hạn ứng dụng thực tế**: Trong sản phẩm thương mại thật, câu trả lời tự nhiên soạn cho khách hàng có giá trị trải nghiệm người dùng (UX) quan trọng dù không làm thay đổi bản ghi giao dịch trong ledger.
