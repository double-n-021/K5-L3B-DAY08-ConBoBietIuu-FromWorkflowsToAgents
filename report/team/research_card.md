# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R4 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Zhang et al., EMNLP 2026, https://aclanthology.org/2026.emnlp-main.798/, benchmark chẩn đoán thực nghiệm |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Các kỹ thuật cấu trúc và các bước gọi LLM phụ trợ trong agent pipeline thường bị phóng đại hiệu quả thực tế nếu không cô lập chuẩn xác các biến gây nhiễu (prompt, seed, số lượt gọi LLM phụ trợ) |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Giới hạn trong paper: Khảo sát trên các benchmark ngôn ngữ tự nhiên và hệ thống MAS đồng nhất (homogeneous agents chia sẻ mô hình nền), đánh giá cấu trúc topology và các phương pháp pruning/giao tiếp. Không mở rộng cho các hệ thống có agent mang mục tiêu xung đột hoặc môi trường bất định cao |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Đối với Single ReAct Agent, bước gọi model soạn câu trả lời draft ở cuối pipeline không can thiệp vào logic tính quote hay duyệt chi của Host; khi loại bỏ bước draft (treatment arm), pass rate và pass^5 sẽ giữ nguyên không đổi, số lượt gọi model trung bình (mean_model_calls) sẽ giảm đúng 1 cuộc gọi trên mỗi trial thành công có draft, và chi phí mô phỏng cost/success sẽ giảm tương ứng mà không làm thay đổi bất kỳ bản ghi nghiệp vụ hay số tiền hoàn nào |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: 14 public claims, seeds 11/22/33/44/55, MockLLM, read tools (lookup_order, compute_compensation), policy, pricing config, fresh SQLite per trial. Biến duy nhất thay đổi: Tắt lời gọi complete(..., purpose='draft') ở cuối pipeline |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Đo bằng pass_rate, pass^5, variance, cost/success, mean_model_calls. Kiểm tra đối chứng trực tiếp trên 70 cặp database độc lập giữa 2 nhánh: status, proposal_amount, refund_ledger (số dòng, số tiền), audit refund_committed, và audit policy_denied. Lỗi dự kiến nếu vi phạm: Nếu bỏ draft làm sai lệch bất kỳ trường nào trong các đối chiếu trên hoặc không giảm chi phí thì hypothesis thất bại |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn):
  `.venv/bin/python -m bonus.jay_ablation --out reports/jay_ablation.json`
- Run id / file report:
  `reports/jay_ablation.json` (chứa toàn bộ `baseline_report` và `treatment_report`)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu:
  **Xác nhận giả thuyết (Đạt)**:
  - Baseline: `pass_rate` = 1.0, `pass_5` = 1.0, `mean_model_calls` = 3.71, `cost/success` = 30.03 VND, `mean_steps` = 3.79.
  - Treatment (No Draft): `pass_rate` = 1.0, `pass_5` = 1.0, `mean_model_calls` = 2.71 (delta: -1.00), `cost/success` = 29.05 VND (delta: -0.98 VND), `mean_steps` = 3.79.
  - Kiểm tra đối chiếu DB trực tiếp (Paired DB verification): 70/70 cặp database độc lập (14 claim × 5 seed) đạt 0 điểm sai lệch (`PASS (0 mismatches)`: status, proposal_amount, số tiền hoàn thực tế trong `refund_ledger`, audit `refund_committed` và audit `policy_denied` hoàn toàn trùng khớp).
- Giới hạn:
  - **Giới hạn phòng lab (MockLLM)**: Môi trường LogiX-VN sử dụng MockLLM với chi phí token và lượt gọi mô phỏng, latency là `unavailable`; câu trả lời draft không được grader chấm nên thí nghiệm tập trung đo lường tính bất biến logic và chi phí mô phỏng.
  - **Giới hạn ứng dụng thực tế**: Trong sản phẩm thương mại thật, câu trả lời tự nhiên soạn cho khách hàng có giá trị trải nghiệm người dùng (UX) quan trọng dù không làm thay đổi bản ghi giao dịch trong ledger.
