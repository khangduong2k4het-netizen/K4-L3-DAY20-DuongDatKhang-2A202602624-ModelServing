# 01 - Tune: thread-count sweep

Model `Qwen3.5-0.8B-Q4_K_M.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
CPU: **8 physical · 16 logical** cores · `ngl=99` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 165.2 | 98% |
| 4 | 168.9 | 100% |
| 8 | 165.8 | 98% |
| 16 | 166.0 | 98% |
| 32 | 169.0 | 100% |

**Best**: `-t 32` at 169.0 tok/s
**Slowest tested**: `-t 1` at 165.2 tok/s (1.02x spread)
**Against the physical-core default** (`-t 8`, 165.8 tok/s): 1.02x

Use this in your run:

```bash
LAB_N_THREADS=32 make bench
```

## Explanation

Đo ngày 06/10/2026 trên laptop Windows 11, Ryzen 7 5800HS (8 physical / 16 logical), Q4_K_M, llama.cpp b10488; mỗi điểm sweep có 2 repetitions. Sweep này giữ `ngl=99`, không phải CPU-only. Lần kiểm tra bên dưới xác nhận backend CUDA và RTX 3050 Laptop 4 GB.

Không thấy knee rõ tại 8 core physical: đường cong gần phẳng từ 1 thread (165.23 tok/s) đến 32 thread (168.99 tok/s), toàn dải chỉ chênh 2.28%. Có thể nói vùng plateau đã bắt đầu ở điểm nhỏ nhất được đo (1 thread), nhưng chưa xác định được knee chính xác. Best của sweep là 32; 4 thread chỉ thấp hơn 0.13 tok/s (0.08%). So với mặc định 8 thread, 32 đạt 1.0194× (+1.94%) trong sweep đầu.

Cơ chế phù hợp với cấu hình này là GPU offload chuyển phần lớn phép tính tensor và truy cập weights sang GPU. Tăng CPU thread không tăng băng thông VRAM hoặc tài nguyên compute của GPU, nên `-t` ít tác động hơn trong CPU-only decode. Nếu nhiều worker CPU cùng hoạt động, chúng có thể tranh core physical, cache và thời gian scheduler; tuy nhiên bảng này không chứng minh tranh chấp memory channel RAM hay mức tụt do oversubscription. Không có profiler để phân biệt bottleneck GPU compute, bandwidth hay overhead điều phối.

### Kiểm tra thứ hạng (5 repetitions mỗi điểm)

Chạy cùng model, `-ngl 99 -p 0 -n 128 -r 5`, giữ các mặc định llama-bench khác; output gốc lưu ở `01-tuning-validation.log`. Dấu ± là độ lệch chuẩn do llama-bench báo, không phải khoảng tin cậy.

| threads (-t) | tg128 (tok/s, mean ± stddev) |
|--:|--:|
| 4 | 161.62 ± 9.38 |
| 8 | 167.29 ± 0.99 |
| 32 | 166.98 ± 1.24 |

Lần kiểm tra cho 32/8 = 0.9981× (−0.19%), đảo thứ hạng so với sweep đầu; chênh lệch nhỏ hơn độ dao động được báo. Chưa có bằng chứng 32 thread đem lại cải thiện ổn định, nên giữ mặc định 8 thread. Hai repetitions đầu chỉ đủ chọn ứng viên, không đủ chứng minh speedup nhỏ. Kết quả này là microbenchmark decode tg128, không phải TTFT/TPOT phía HTTP; không ghi đè baseline serving đã đo.
