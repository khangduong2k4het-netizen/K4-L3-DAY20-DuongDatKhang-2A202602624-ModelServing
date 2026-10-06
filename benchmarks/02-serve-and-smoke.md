# 02 — Server and smoke evidence

Date: 2026-10-06 (Asia/Saigon). Server remains running on `http://localhost:8080` for subsequent load tests.

Model: `Qwen3.5-0.8B-Q4_K_M.gguf`; llama.cpp `b10488`; threads=8, ngl=99, ctx=2048. Flags: `--parallel 4 --cont-batching --metrics --reasoning off`. `/health` returns `{"status":"ok"}`; `/slots` returns four idle slots, each with `n_ctx=512`.

The server was started using the existing `serve.py` launcher as a hidden background process. Launcher output is in `02-serve-stdout.log`, server request logs in `02-serve-stderr.log`, and the listening process details in `02-serve-process.json`.

## Smoke results

Both invocations of the existing `smoke-test.py` exited successfully and returned nonempty completions.

| Run | Prompt tokens evaluated | Prefill ms | Prefill tok/s | Output tokens | Decode ms | Decode tok/s | tokens_predicted_total before → after |
|--|--:|--:|--:|--:|--:|--:|--|
| First | 37 | 77 | 480.4 | 44 | 303 | 141.9 | 0 → 44 (+44) |
| Second, saved output | 4 | 33 | 122.8 | 30 | 216 | 134.0 | 44 → 74 (+30) |

The second request reused the same prompt prefix, so the server evaluated fewer prompt tokens; these prefill figures should not be treated as a cold-prompt comparison. Server timings exclude client HTTP overhead and are not identical to client TTFT/TPOT.

The saved run ends with:

```text
OK -- served a completion and tokens_predicted_total is 74 (non-zero).
```

Saved evidence: `02-smoke-output.log` (actual smoke stdout), `02-smoke-metrics.prom` (Prometheus endpoint snapshot), and `02-smoke-slots.json`. Successful serving proves the API/metrics operation, not factual correctness of the generated goodput definition.

## Screenshot evidence

Ảnh thật đã có tại submission/screenshots/03-serve-and-smoke.png, hiển thị launcher và smoke output cạnh nhau. Đã kiểm tra nội dung khớp số đo trên.
