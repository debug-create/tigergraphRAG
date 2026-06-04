import json

with open('results/benchmark_results.json', encoding='utf-8') as f:
    results = json.load(f)

def stats(key):
    tokens, lat, passes, costs = [], [], [], []
    for q in results:
        p = q.get(key, {})
        
        tok = p.get('total_tokens', 0)
        if tok: tokens.append(tok)
        
        if p.get('latency_seconds'): lat.append(p['latency_seconds'])
        
        j = p.get('llm_judge')
        if j == 'PASS':
            passes.append(1)
        elif j in ('FAIL', 'SKIP'): # Assumes anything not PASS is a 0 score
            passes.append(0)
            
        c = p.get('cost_usd', 0)
        if c: costs.append(c)
        
    return {
        'tokens': sum(tokens)/len(tokens) if tokens else 0,
        'latency': sum(lat)/len(lat) if lat else 0,
        'pass': sum(passes)/len(passes)*100 if passes else 0,
        'cost': sum(costs)/len(costs) if costs else 0,
    }

p1 = stats('pipeline1')
p2 = stats('pipeline2')
p3 = stats('pipeline3')
reduction = (1 - p3['tokens']/p2['tokens'])*100 if p2['tokens'] else 0

# Using outer double quotes and inner single quotes to avoid escape character issues
print(f"Token Reduction %:        {reduction:.1f}")
print(f"Tokens/query LLM Only:    {p1['tokens']:.0f}")
print(f"Tokens/query Basic RAG:   {p2['tokens']:.0f}")
print(f"Tokens/query GraphRAG:    {p3['tokens']:.0f}")
print(f"Cost/query LLM Only:      ${p1['cost']:.6f}")
print(f"Cost/query Basic RAG:     ${p2['cost']:.6f}")
print(f"Cost/query GraphRAG:      ${p3['cost']:.6f}")
print(f"Latency LLM Only:         {p1['latency']:.1f}s")
print(f"Latency Basic RAG:        {p2['latency']:.1f}s")
print(f"Latency GraphRAG:         {p3['latency']:.1f}s")
print(f"Pass% LLM Only:           {p1['pass']:.1f}")
print(f"Pass% Basic RAG:          {p2['pass']:.1f}")
print(f"Pass% GraphRAG:           {p3['pass']:.1f}")
