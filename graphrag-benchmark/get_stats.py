import json
import statistics

with open('results/benchmark_results.json', encoding='utf-8') as f:
    results = json.load(f)

def stats(key):
    tokens, lat, passes, costs = [], [], [], []
    for q in results:
        p = q.get(key, {})
        tok = p.get('total_tokens', 0)
        if tok: tokens.append(tok)
        
        j = p.get('llm_judge')
        if j: passes.append(1 if j == 'PASS' else 0)
        
        c = p.get('cost_usd')
        if c is not None:
            costs.append(c)
            
    return {
        'pass': sum(passes)/len(passes)*100 if passes else 0,
        'cost': sum(costs)/len(costs) if costs else 0,
    }

p1 = stats('pipeline1')
p2 = stats('pipeline2')
p3 = stats('pipeline3')

print(f"LLM-as-Judge Pass % (GraphRAG): {p3['pass']:.1f}%")
print(f"Cost per query (LLM Only):      ${p1['cost']:.6f}")
print(f"Cost per query (RAG):           ${p2['cost']:.6f}")
print(f"Cost per query (GraphRAG):      ${p3['cost']:.6f}")
