# 02 - Serve: load test + saturation reading

Host `Windows-AMD64` � llama.cpp `b10488` �
`--parallel 4` � `ctx=2048` � `threads=8` �
`ngl=99`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 216 | 3.76 | 1700 | 2800 | 3300 | 6.7 | 0.0% |
| 50 | 228 | 3.86 | 11000 | 13000 | 13000 | 41.7 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **1.03x** (21% of linear) |
| P95 latency | **4.64x** |
| Effective concurrency at 50 users | 41.7 vs `--parallel 4` slots (occupancy/slot ratio 10.41) |

**Saturated.** Throughput delivered only 1.03x for 5x the offered load, and effective concurrency (41.7) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

Throughput moved 1.03x while P95 moved 4.64x. That gap is the goodput argument: past saturation you buy throughput by spending latency, and if your SLO is a P95 target then the requests you added are no longer being served within it. (This lab does not fix an SLO number for you -- pick one in your write-up and state how much goodput you keep at it.)

## Reading

Server bão hoà rõ tại 50 user: tăng tải 5× chỉ giao 1.03× throughput (3.7587 → 3.8621 RPS, 20.55% mức tuyến tính), trong khi P95 tăng 4.64× (2.8 → 13 giây). Effective concurrency = RPS × mean latency: 6.66 ở 10 user và 41.65 ở 50 user, so với 4 slot (occupancy/slot = 10.41 ở 50 user, không phải utilisation). Ngay 10 user đã có dấu hiệu chờ slot; hai điểm đo chưa xác định chính xác knee. Cả hai run có trên 20 request (216 và 228), nên không có cảnh báo Small sample.

Metrics tải 50 user ghi peak requests_processing=4, requests_deferred=44 và peak gauge n_busy_slots_per_decode≈3.93/4 (98%, trung bình mỗi bước decode). Throughput gần phẳng, slot kín và deferred>0 chứng minh hàng đợi góp phần làm P95 tăng: tải thêm chủ yếu thành queue time. Chưa có timing queue/compute cho từng request nên không khẳng định toàn bộ 10.2 giây chênh P95 là queue time; compute cũng có thể đổi khi batching. Run hữu hạn chỉ tính request hoàn tất nên Little's Law ở đây là ước lượng.

Chọn SLO P95 ≤ 3 giây. 10 user đạt (P95=2.8 giây), 50 user không đạt (P95=13 giây). Với goodput đếm request thành công có latency ≤ 3 giây: từ percentile CSV, ở 10 user ước lượng ít nhất khoảng 95% × 3.7587 = **3.57 request/s**; ở 50 user median=11 giây nên chỉ có thể chặn trên khoảng 50% × 3.8621 = **1.93 request/s**. Đây là các cận ước lượng từ percentile Locust có làm tròn, không phải goodput chính xác hay khoảng tin cậy; cần histogram hoặc log latency từng request để tính chính xác. Không lấy 3.86 RPS throughput làm goodput đạt SLO.

Knob thử trước là `LAB_PARALLEL=8`, tăng từ 4 slot để giảm chờ và kiểm tra lợi ích continuous batching. Đồng thời dùng `LAB_N_CTX=4096` để giữ ngân sách 512 token mỗi slot như cấu hình 4 slot/ctx=2048; giữ model, GPU offload và threads=8. Đặt cùng LAB_PARALLEL khi serve và load-report, đo lại RPS/P95 và goodput tại 3 giây. Đây là thí nghiệm đề xuất, chưa có speedup đo được: thêm slot/KV cache có thể tăng VRAM và làm compute chậm. Ưu tiên slot vì có bằng chứng slot kín/queue; thread sweep trước đó chưa cho lợi ích ổn định khi tăng thread.

Nguồn: locust-10_stats.csv, locust-50_stats.csv, 02-server-metrics-u50.csv và 02-server-batching-u50.md. Report được chạy lại với LAB_PARALLEL=4, đúng command line server trong 02-serve-process.json. Trên Windows dùng `powershell -NoProfile -ExecutionPolicy Bypass -File lab.ps1 load-report`, tương đương target `make load-report`.
