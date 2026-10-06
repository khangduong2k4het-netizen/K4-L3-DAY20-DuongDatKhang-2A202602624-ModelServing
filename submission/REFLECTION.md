# Reflection — Day 20 Lab (Personal Report)

**Họ Tên:** Dương Đạt Khang
**MSSV:** 2A202602624
**Cohort:** K4, Track02 (theo tên repo)
**Ngày chuẩn bị bài nộp:** 2026-10-06 (UTC+7)

## 1. Hardware & runtime  *(rubric 1, 2 — 10 điểm)*

Nguồn: `hardware.json`, `models/active.json`, `runtime/active.json`.

- **OS:** Windows 11 AMD64; Python 3.13.14.
- **CPU:** AMD Ryzen 7 5800HS with Radeon Graphics.
- **Cores:** 8 physical / 16 logical.
- **CPU extensions:** probe không xuất trường này; chưa đo riêng.
- **RAM:** 23.4 GB theo probe.
- **Accelerator:** NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB; dùng CUDA offload. Probe cũng phát hiện Vulkan.
- **llama.cpp asset:** `llama-b10488-bin-win-cuda-12.4-x64.zip`, prebuilt b10488; không build source.
- **Model:** Qwen3.5 0.8B (`LAB_MODEL=qwen35-0.8b`), repo `unsloth/Qwen3.5-0.8B-GGUF`.
- **Quantization:** primary `Q4_K_M`, compare `UD-Q2_K_XL`.
- **Baseline:** threads=8, ngl=99, ctx=2048; serving parallel=4, continuous batching, metrics, reasoning off.

**Chạy ở đâu:** laptop local; không dùng Colab/Kaggle.

**Setup story** (≤80 chữ): Dùng Windows runner `lab.ps1` thay make. Chọn Qwen3.5 0.8B để chạy gọn trên RTX 3050 4 GB. PowerShell chặn script nên gọi với ExecutionPolicy Bypass theo hướng dẫn; Python cần chạy ngoài sandbox của công cụ. Sửa dấu gạch Unicode trong runner để tương thích PowerShell 5.1. Dùng runtime CUDA prebuilt, không biên dịch source.

Ảnh probe là lần probe ban đầu còn khuyến nghị Gemma 4 E2B; hardware không đổi. Sau đó chọn Qwen bằng LAB_MODEL, nên hardware.json/active.json hiện tại ghi Qwen. Ảnh load-10 console cuối có 217 request, CSV có 216 do thời điểm flush; số trong report dùng CSV nhất quán.

## 2. Đo lường  *(rubric 3, 4, 5 — 20 điểm)*

Nguồn: `benchmarks/01-quickstart-results.md`; mỗi quantization hoàn tất 10/10 request, bỏ warm-up, max_tokens=64.

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| Q4_K_M | 0.50 | 2953 | 335 / 358 | 6.2 / 6.5 | 726 / 748 / 748 | 160.8 |
| UD-Q2_K_XL | 0.39 | 1639 | 351 / 355 | 6.6 / 7.1 | 764 / 798 / 798 | 150.7 |

**Quan sát** (≤60 chữ): Q2 chậm hơn 6.3%, chỉ tiết kiệm 21.56% dung lượng. Cùng prompt, Q4 tính sai TTFT/TPOT nhưng kết thúc; Q2 sai công thức rồi lặp tới giới hạn. Cả hai không trả lời tiếng Việt. Chọn Q4: nhanh hơn, ít lỗi lặp trong phép thử này; một prompt chưa đủ kết luận chất lượng tổng quát.

Size (GB) của script thực tế là GiB. Load không phải cold-cache; với 10 mẫu nearest-rank, P95/P99 cùng lấy max. Decode là 1000/TPOT P50 phía client. CUDA offload khiến lợi ích ít byte của Q2 có thể bị chi phí kernel/dequantization bù lại; chưa có profiler để kết luận bottleneck. Quality test temperature=0, max_tokens=512; đáp án chuẩn TTFT=200 ms, TPOT=100 ms; output gốc trong `01-quality-comparison.json`.

---
## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

Nguồn: `benchmarks/02-server-results.md`, CSV Locust và metrics tải u50; `--parallel 4`.

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|--:|--:|--:|--:|--:|--:|--:|
| 10 | 3.76 | 1700 | 2800 | 3300 | 6.7 | 0.0% |
| 50 | 3.86 | 11000 | 13000 | 13000 | 41.7 | 0.0% |

| Going from 10 to 50 users | Kết quả |
|:--|--:|
| Offered load | 5× |
| Throughput thực giao | 1.03× (20.55% mức tuyến tính) |
| P95 latency | 4.64× |
| Effective concurrency ở 50 users | 41.7 / 4 slot; occupancy/slot 10.41 |

**Peak `llamacpp:n_busy_slots_per_decode`:** 3.93 / 4 slots (98%); đây là peak gauge trung bình mỗi bước decode, không phải instantaneous utilisation. Peak processing=4; deferred=44.

**Saturation reading** (≤ 80 chữ): Bão hoà tại 50 user; 10 user đã có dấu hiệu chờ. RPS tăng 1.03×, P95 4.64×; concurrency 41.7/4 slot, deferred=44 chứng minh queue góp phần tăng latency. Chưa tách chính xác queue/compute. Thử parallel 4→8 trước vì slot kín, ctx 2048→4096 giữ context/slot; tăng thread chưa giúp ổn định. Đo lại goodput để kiểm chứng.

**SLO và goodput:** Chọn P95 ≤ 3 giây: 10 user đạt, 50 user không đạt. Goodput đếm request thành công ≤3 giây: cận ước lượng ở 10 user ≥ khoảng 3.57 request/s (95% × 3.7587); ở 50 user ≤ khoảng 1.93 request/s (median 11 giây ⇒ tối đa khoảng 50% đạt). CSV percentile có làm tròn; đây không phải goodput chính xác. Cần histogram/log từng request để đo chính xác. Hai run hoàn tất 216/228 request, không có Small sample; concurrency vẫn là ước lượng từ request đã hoàn tất trong run hữu hạn.

---
## 4. Integration  *(rubric 12, 13 — 15 điểm)*

Nguồn: `benchmarks/03-integration-results.md`, JSON cùng tên và `03-pipeline-output.log`; chạy 3 query ngày 06/10/2026.

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | Local laptop; không tích hợp cluster/IaC | stub / chưa tích hợp |
| N17 Data pipeline | Corpus khai báo sẵn, không ingest/ETL | stub |
| N18 Lakehouse | TOY_DOCS: 6 tài liệu trong bộ nhớ | stub |
| N19 Vector + features | Keyword overlap top-k=3, không embedding/vector index | stub |
| N20 Serving | HTTP tới llama-server, Qwen3.5 0.8B Q4_K_M/CUDA | real |

**Latency split** (mean của 3 query):

- embed: **0.0 ms** (không gọi embedding server)
- retrieve: **0.0 ms** (làm tròn; query 3 là 0.1 ms)
- llm: **1249.3 ms**
- total: **1249.4 ms**
- **stage chiếm nhiều nhất:** **llm**, khoảng **99.99%** (output làm tròn 100%).

**Reflection** (≤ 60 chữ): LLM chiếm gần 100%, đúng kỳ vọng với 6 toy docs. Để giảm 2× xuống 624.7 ms, ưu tiên rút output và tái sử dụng HTTP client; decode server trung bình 652.7 ms, prefill 109.2 ms. Đo lại chất lượng và latency; tối ưu retrieval gần 0 ms không đủ. Chưa chứng minh speedup 2×.

Cả 3 query in contexts/timings/answer; log server ghi truncated=0. Output thứ ba lẫn prefix caching vào disaggregated serving, nên chưa coi chất lượng trả lời là đã xác nhận. System prompt giữ nguyên; chưa định lượng lợi ích cache qua counter trước/sau. Stage llm đo phía client gồm cả overhead HTTP, không đồng nhất với compute time server.

---
## 5. The single change that mattered most  *(rubric 11 — 10 điểm)*

> **Phần quan trọng nhất của report.** Không cần bonus track: `make tune` đã cho bạn
> một before/after thật (`benchmarks/01-tuning-tg128.md`). Đổi quantization,
> `LAB_N_CTX`, hay `--parallel` rồi đo lại cũng được.

**Change:** Thử tăng CPU thread từ `-t 8` (mặc định physical core) lên `-t 32`, giữ Qwen3.5 0.8B Q4_K_M và CUDA offload `-ngl 99`. Đây là knob đã kiểm tra, chưa chứng minh được cải thiện ổn định; giữ 8 thread sau kiểm tra.

```
Sweep đầu (tg128, 2 repetitions/điểm):
before:  165.77 tok/s (-t 8)
after:   168.99 tok/s (-t 32)
speedup: 1.0194× (+1.94%)

Kiểm tra (tg128, 5 repetitions/điểm):
before:  167.29 ± 0.99 tok/s (-t 8)
after:   166.98 ± 1.24 tok/s (-t 32)
speedup: 0.9981× (−0.19%)
```

**Cơ chế và giới hạn của kết quả:**

Sweep `[1, 4, 8, 16, 32]` gần phẳng (165.23–168.99 tok/s), không có knee rõ ở 8 core physical; plateau đã xuất hiện từ điểm 1 thread. Backend thực tế là CUDA trên RTX 3050 Laptop, nên phần lớn xử lý tensor/weights được offload. Thêm CPU thread không tăng băng thông VRAM hay tài nguyên GPU. Worker CPU thừa có thể tranh core, cache và scheduler, nhưng số đo không cho thấy mức tụt oversubscription rõ hoặc chứng minh bottleneck RAM bandwidth. Không dùng hình dạng CPU-only kỳ vọng để giải thích cưỡng ép một sweep có GPU offload.

Lần kiểm tra 5 repetitions đảo thứ hạng 8 và 32; chênh lệch 0.31 tok/s nhỏ hơn độ dao động được báo. Vì vậy 1.0194× ban đầu là kết quả thật của lần đo đó, nhưng không phải speedup ổn định. Tôi giữ 8 thread và không chạy lại baseline HTTP với 32. Nguồn: `benchmarks/01-tuning-tg128.md`, JSON cùng tên và `benchmarks/01-tuning-validation.log` (06/10/2026). Trong các thay đổi đã đo tới hiện tại, lựa chọn Q4 thay vì Q2 có tác động rõ hơn (+6.7% tốc độ decode phía client trong baseline trước); việc tune thread trên cấu hình GPU này chưa tạo ra lợi ích đáng kể.

---

## 6. Bonus

Không làm bonus.

## 7. Điều làm bạn ngạc nhiên nhất

Q2 nhỏ hơn nhưng decode chậm hơn Q4; tăng CPU thread lên 32 cũng không tạo speedup ổn định khi dùng CUDA.

## 8. Self-check trước khi push

- [x] Bằng chứng và REFLECTION đã commit.
- [x] Đủ 5 screenshot đúng tên; giữ nguyên nội dung ảnh thật.
- [x] Số đo đã đối chiếu với benchmarks; real/stub và giới hạn được khai rõ.
- [x] Verify exit 0; sửa chuẩn hoá đường dẫn Windows trong scripts/verify.py.
- [x] Tên repo đúng mẫu và public trên GitHub: K4-L3-DAY20-DuongDatKhang-2A202602624-ModelServing.
- [ ] Commit cuối đã push.
- [ ] URL repo đã nộp vào VinUni LMS.
- [x] Không đưa model weights, runtime, virtualenv hay .env vào bài nộp.

## 9. Khai báo sử dụng AI  *(docs/RULES.md §3)*

Dùng ChatGPT/Codex hỗ trợ chạy lệnh trên máy local, đọc/debug lỗi PowerShell và sandbox, kiểm tra số đo, so sánh quantization, tổng hợp bảng và hỗ trợ soạn/chỉnh nhận định ở REFLECTION và benchmarks. Các phép đo lấy từ script và server thật trên máy đã khai báo; ảnh là ảnh chụp do người dùng cung cấp, không tạo ảnh giả. Phần giải thích do AI hỗ trợ soạn cần người học đọc, hiểu và tự chịu trách nhiệm khi trình bày với grader/coach.
