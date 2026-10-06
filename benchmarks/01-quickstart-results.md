# 01 - Measure: latency baseline

Model `Qwen3.5 0.8B` · host `Windows-AMD64` · llama.cpp `b10488`
Settings: `threads=8` `ngl=99` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `Q4_K_M` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| Q4_K_M | 0.50 | 2953 | 335 / 358 | 6.2 / 6.5 | 726 / 748 / 748 | 160.8 |
| UD-Q2_K_XL | 0.39 | 1639 | 351 / 355 | 6.6 / 7.1 | 764 / 798 / 798 | 150.7 |

- **TTFT** is measured client-side from sending the request to the first nonempty content delta; it includes HTTP/client overhead as well as prefill.
- **TPOT** is the client decode interval divided by `predicted_n - 1`; output counts come from server timings. `decode tok/s = 1000 / TPOT_p50`. Compute, kernels and memory bandwidth can all affect it.
- `UD-Q2_K_XL` decodes **1.07x SLOWER** than `Q4_K_M` here, despite being 0.11 GB smaller. That is a real result, not a mistake: fewer bits only buys speed when decode is limited by memory bandwidth. On a machine that is compute-limited instead — few cores, no GPU offload — the extra dequantization work of a heavily-quantized format can cost more than the bytes it saves. Say which case yours is.

## Observation

Đo ngày 06/10/2026 trên Ryzen 7 5800HS (8 core vật lý), RAM 23.4 GB, RTX 3050 Laptop 4 GB, runtime được cấu hình chọn CUDA. Đây là lần benchmark hoàn tất đầu tiên trong phiên này; mỗi model bỏ một request warm-up. Không xóa page cache, nên không coi Load là số đo cold-cache. Hai model đều hoàn thành 10/10 request; nearest-rank với 10 mẫu khiến P95 và P99 cùng lấy giá trị lớn nhất.

**Tốc độ:** UD-Q2_K_XL đạt 150.7 tok/s so với 160.8 tok/s của Q4_K_M: tốc độ thấp hơn 6.3% (4-bit nhanh hơn 1.067 lần). TPOT P50 tăng từ 6.22 lên 6.63 ms; TTFT P50 tăng từ khoảng 335 lên 351 ms. E2E còn phụ thuộc độ dài câu trả lời, nên dùng TPOT để so decode.

**Dung lượng:** bảng báo khoảng 0.50 xuống 0.39 GiB (cột Size (GB) của script thực tế chia cho 1024^3), Kích thước thực tế là 532,517,120 và 417,718,528 byte: giảm 114,798,592 byte (0.107 GiB), tương đương 21.56%.

**Chất lượng:** hỏi cùng một prompt ở temperature=0, max_tokens=512, server riêng trên port 18199; kiểm tra trường model để xác nhận đúng quantization. Prompt yêu cầu trả lời tiếng Việt, tính TTFT/TPOT khi 5 token có token đầu ở 200 ms và token cuối ở 600 ms, rồi giải thích 2-bit có luôn nhanh hơn không. Đáp án chuẩn là TTFT=200 ms và TPOT=(600-200)/(5-1)=100 ms. Q4_K_M trả lời bằng tiếng Anh và tính sai cả hai thành 1200 ms, nhưng kết thúc câu trả lời và nói 2-bit không luôn nhanh hơn. UD-Q2_K_XL cũng không trả lời tiếng Việt, viết công thức sai rồi lặp TPOT đến khi bị cắt (`finish_reason=length`). Câu trả lời nguyên văn và metadata nằm trong `01-quality-comparison.json`; một prompt chưa đủ kết luận chất lượng tổng quát.

**Có đáng dùng không:** trong lần đo và phép thử này, chọn Q4_K_M làm baseline: nhanh hơn và không bị lặp như Q2. Tiết kiệm khoảng 0.11 GiB chưa đáng đánh đổi tốc độ và chất lượng trên máy hiện tại. Cả hai vẫn cần kiểm tra chất lượng thêm vì Q4 cũng tính sai. Máy bật GPU offload (`ngl=99`), nên không thuộc ví dụ CPU ít core/không offload; kết quả phù hợp với khả năng chi phí kernel/dequantization hoặc compute vượt lợi ích giảm byte, nhưng benchmark này không có profiler để xác định chính xác bottleneck.

