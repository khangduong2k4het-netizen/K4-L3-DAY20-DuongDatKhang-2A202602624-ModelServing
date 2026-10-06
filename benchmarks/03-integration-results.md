# 03 - Integrate: RAG pipeline run

Host `Windows-AMD64` � llama.cpp `b10488` �
retrieval backend: **keyword overlap** � 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.0 | 1662.1 | 1662.2 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.0 | 1016.5 | 1016.6 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.1 | 1069.4 | 1069.5 |

Mean per stage (ms): embed **0.0** � retrieve **0.0** �
llm **1249.3** � total **1249.4**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Based on the context provided, **Goodput** is more useful than raw throughput because it filters out requests that do not meet specific performance targets (TTFT and TPOT).

Raw throughput ignores SLOs (Service Level Objectives), whereas Goodput counts only requests that met these targets. This means Goodput provides a more accurate and realistic measure of system capacity and performance under lo

**What problem does PagedAttention actually solve?**

> Based on the provided context, **PagedAttention** solves the problem of **internal fragmentation in GPU memory**.

The text explicitly states: "PagedAttention stores the KV cache in non-contiguous pages, removing the internal fragmentation that wasted most GPU memory."

While the context also mentions RadixAttention uses a trie for caching to avoid prefill, and Disaggregated serving splits pools t

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps when the **prefill operation is compute-bound** (requires significant CPU/GPU cycles) but the **decode operation is memory-bound** (requires significant bandwidth).

This is achieved by prefilling the model with a shared prefix that allows the engine to skip the expensive prefill step entirely, while the actual decoding happens in separate pools. This optimizatio


## Which N16-N19 pieces are real

| Day | Piece trong lần chạy này | Real hay stub? |
|:--|:--|:--|
| N16 Cloud/IaC | Server local trên laptop; không nối cluster/IaC N16 | stub / chưa tích hợp |
| N17 Data pipeline | Không ingest/ETL; corpus khai báo sẵn trong Python | stub |
| N18 Lakehouse | TOY_DOCS: 6 tài liệu trong bộ nhớ; không dùng Iceberg/SQLite | stub |
| N19 Vector + features | retrieve() chấm keyword overlap, top-k=3; không embedding/vector index | stub |
| N20 Serving | HTTP /v1/chat/completions tới llama-server local, Qwen3.5 0.8B Q4_K_M, CUDA | real |

Chạy ngày 06/10/2026 bằng Windows runner tương đương `make pipeline`: `powershell -NoProfile -ExecutionPolicy Bypass -File lab.ps1 pipeline --base-url http://127.0.0.1:8080`. Cả 3 câu hỏi hoàn tất, có contexts/timings/answer; đầy đủ câu trả lời và server timings trong JSON cùng tên, output console trong `03-pipeline-output.log`. Server dùng threads=8, ngl=99, ctx=2048, parallel=4 (512 token/slot). Log `03-serve-stderr.log` ghi truncated=0 cho cả ba request.

Mean embed=0.0 ms, retrieve=0.0 ms, llm=1249.3 ms, total=1249.4 ms. LLM chiếm khoảng 99.99% (script làm tròn 100%), đúng kỳ vọng với corpus 6 tài liệu. Embed=0.0 vì không gọi embedding server; retrieve=0.0 là làm tròn tới 0.1 ms, không phải retrieval miễn phí (query thứ ba đo 0.1 ms). Mean total gồm overhead ghép prompt/sắp xếp ngoài stage timings.

Nếu phải giảm latency 2×, mục tiêu mean total ≤624.7 ms: tấn công stage llm. Timing server trung bình prefill≈109.2 ms và decode≈652.7 ms; decode là phần lớn trong thời gian xử lý server. Thử câu trả lời ngắn hơn và giới hạn output token trước, đồng thời dùng httpx.Client tái sử dụng kết nối thay vì tạo client qua mỗi httpx.post. Stage llm phía client còn gồm HTTP/client/server overhead: chênh với prefill+decode trung bình≈487.5 ms, chưa có instrumentation để tách chính xác. Chỉ giảm prefill hoặc tối ưu retrieve không thể tiết kiệm đủ khoảng 624.7 ms. Đo lại cùng ba query và kiểm tra chất lượng; chưa khẳng định đạt speedup 2×.

SYSTEM_PROMPT được giữ nguyên giữa ba lần gọi. Server log cho thấy chọn lại slot theo LCP ở query 2/3, nhưng chưa đo counter trước/sau để định lượng lợi ích prefix cache. Việc prompt_n giảm không tự chứng minh cache vì context và câu hỏi cũng đổi. Nếu nối corpus thật, cắt context theo tokenizer /tokenize của server và ngân sách 512 token/slot, chừa chỗ cho template và output.

Về chất lượng: top-k có cả tài liệu score=0 ở hai query đầu. Câu trả lời thứ ba lẫn prefix caching (radix) vào giải thích disaggregated serving; pipeline chạy thành công không đồng nghĩa mọi câu trả lời đều chính xác. Nếu thay retrieval thật, kiểm tra relevance và grounding bên cạnh latency.
