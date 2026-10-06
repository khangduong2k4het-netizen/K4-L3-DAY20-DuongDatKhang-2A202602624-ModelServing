# 02 - Continuous batching under load (u50)

Host `Windows-AMD64` · `--parallel 4` · 14 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 3.93 of 4 slots (98%) |
| `requests_processing` | 4 |
| `requests_deferred` | 44 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 27999 |

Highest sampled value was **3.93 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95.

## Observation

Đo ngày 06/10/2026, Qwen3.5 0.8B Q4_K_M, CUDA, threads=8, ctx=2048, parallel=4. Locust chạy 50 user trong 60 giây với ramp 25 user/s; sampler chạy chồng thời gian với tải. Các mẫu ngay đầu đã ghi `processing=4`, `deferred=39` và `busy_slots=3.89744`, nên bằng chứng không dựa vào lúc server rảnh. Peak gần 3.93/4 (98%) là mức trung bình slot hữu ích mỗi bước decode cao nhất đã lấy mẫu, không phải độ rộng batch tức thời tối đa.

Peak `requests_processing=4` và `requests_deferred=44` chứng minh hết slot và có hàng đợi. Effective concurrency ở 50 user là 41.7 từ RPS × mean latency; con số này tính request đang chờ lẫn đang xử lý, trong khi gauge busy slots mô tả phần decode hoạt động. Vì hai metric đo khác nhau, không kỳ vọng 41.7 bằng 3.93. Dùng gauge server để chứng minh batching và dùng concurrency/RPS/P95 để đọc áp lực hàng đợi. KV usage không được build xuất ra, giữ `n/a`.

Sampler thu 14 mẫu trong khoảng 60 giây; `--interval 2` là thời gian nghỉ giữa lần scrape, chưa bao gồm overhead HTTP. Timestamp CSV cho khoảng cách thực tế xấp xỉ 4.4 giây. Các mẫu cuối là lúc tải đã dừng/đang drain; gauge busy trung bình vẫn gần 3.93 dù processing về 0, nên luôn đọc cùng processing/deferred và token counter. Counter final 27999 là tích lũy cả smoke và các load run, không phải riêng số token của tải 50 user.
