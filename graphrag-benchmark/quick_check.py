import json
with open('results/benchmark_results.json', encoding='utf-8') as f:
    d = json.load(f)
for q in d[:3]:
    g = q.get('pipeline3') or {}
    print('Q:', q.get('question','')[:80])
    print('A:', str(g.get('answer',''))[:200])
    print('PASS:', g.get('llm_judge'))
    print()
