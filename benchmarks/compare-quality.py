import json
import pathlib
import sys

import httpx

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'lib'))
import labkit

prompt = 'Answer in Vietnamese in at most 180 words. A request produces 5 output tokens. The first token arrives 200 ms after sending the request; the last arrives at 600 ms. Calculate TTFT and TPOT, show the formula, and explain whether 2-bit quantization is always faster than 4-bit.'
active = labkit.load_active()
results = {'prompt': prompt, 'temperature': 0, 'max_tokens': 512, 'responses': []}
for key in ('primary', 'compare'):
    with labkit.serve_bg(str(labkit.repo_root() / active[key + '_model']), port=18199) as base:
        response = httpx.post(base + '/v1/chat/completions', json={
            'model': 'local', 'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0, 'max_tokens': 512, 'stream': False,
        }, timeout=300)
        response.raise_for_status()
        data = response.json()
        assert pathlib.Path(data['model']).name == pathlib.Path(active[key + '_model']).name, data['model']
        results['responses'].append({'quant': active[key + '_quant'], 'response': data})
        print(active[key + '_quant'], json.dumps(data, ensure_ascii=False), flush=True)
pathlib.Path('benchmarks/01-quality-comparison.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
