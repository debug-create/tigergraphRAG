'use client'

import { useState, useEffect } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getBenchmarkResults, BenchmarkSummary } from '@/lib/api'

// Fallback data
const FALLBACK_SUMMARY: BenchmarkSummary = {
  token_reduction_pct: 78.7,
  pipeline1: { avg_tokens: 282, pass_rate: 90 },
  pipeline2: { avg_tokens: 963, pass_rate: 90 },
  pipeline3: { avg_tokens: 205, pass_rate: 100 }
};

export function BenchmarkResultsTab() {
  const [summary, setSummary] = useState<BenchmarkSummary>(FALLBACK_SUMMARY);
  const [isOffline, setIsOffline] = useState(false);
  
  useEffect(() => {
    async function loadData() {
      try {
        const data = await getBenchmarkResults();
        if (data && data.summary) {
          setSummary(data.summary);
          setIsOffline(false);
        }
      } catch (e) {
        setIsOffline(true);
      }
    }
    loadData();
  }, []);
  return (
    <div className="space-y-12">
      {/* Four Stats in 2x2 Grid */}
      <div className="border border-border rounded divide-y divide-x divide-border grid grid-cols-2">
        {/* Top-left */}
        <div className="p-8 border-r border-border border-b border-border relative">
          {isOffline && <div className="absolute top-2 right-2 text-[10px] bg-red-900/30 text-red-400 px-1.5 py-0.5 rounded">OFFLINE - MOCK DATA</div>}
          <div className="text-5xl font-bold font-mono text-accent mb-2">{summary.token_reduction_pct}%</div>
          <div className="text-xs text-muted-foreground">token reduction vs Basic RAG</div>
        </div>

        {/* Top-right */}
        <div className="p-8 border-b border-border">
          <div className="text-5xl font-bold font-mono text-foreground mb-2">{summary.pipeline3.pass_rate}%</div>
          <div className="text-xs text-muted-foreground">GraphRAG pass rate</div>
        </div>

        {/* Bottom-left */}
        <div className="p-8 border-r border-border">
          <div className="text-5xl font-bold font-mono text-foreground mb-2">0.714</div>
          <div className="text-xs text-muted-foreground">BERTScore F1 · bonus threshold met</div>
        </div>

        {/* Bottom-right */}
        <div className="p-8">
          <div className="text-5xl font-bold font-mono text-foreground mb-2">2.32s</div>
          <div className="text-xs text-muted-foreground">avg GraphRAG latency · 58% faster</div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="grid grid-cols-3 gap-8">
        <div className="space-y-2">
          <div className="inline-block px-2 py-1 bg-secondary text-muted-foreground text-xs font-mono rounded">CAT A</div>
          <div className="text-xs text-foreground font-mono">~20% reduction</div>
          <div className="text-xs text-foreground font-mono">90% pass rate</div>
          <p className="text-xs text-muted-foreground pt-1">All pipelines competitive</p>
        </div>

        <div className="space-y-2">
          <div className="inline-block px-2 py-1 bg-amber-900/30 border border-amber-700 text-amber-300 text-xs font-mono rounded">CAT B</div>
          <div className="text-xs text-foreground font-mono">~65% reduction</div>
          <div className="text-xs text-foreground font-mono">93% pass rate</div>
          <p className="text-xs text-muted-foreground pt-1">GraphRAG pulls ahead</p>
        </div>

        <div className="space-y-2">
          <div className="inline-block px-2 py-1 bg-emerald-900/30 border border-emerald-700 text-accent text-xs font-mono rounded">CAT C ★</div>
          <div className="text-xs text-foreground font-mono">~85% reduction</div>
          <div className="text-xs text-foreground font-mono">100% pass rate</div>
          <p className="text-xs text-muted-foreground pt-1">Multi-hop is the differentiator</p>
        </div>
      </div>

      {/* Key Insight Section */}
      <div className="border-l-2 border-accent pl-6 py-4 space-y-4">
        <h3 className="text-sm font-medium text-foreground">Why GraphRAG wins on complex queries</h3>
        <div className="text-xs text-muted-foreground leading-relaxed space-y-3">
          <p>
            Vector search retrieves similar text chunks. On multi-hop questions, this means dumping thousands of tokens of loosely related content into the LLM prompt.
          </p>
          <p>
            GraphRAG traverses a knowledge graph — Drug → Protein → Disease → Treatment — and returns only the precise subgraph relevant to the question.
          </p>
          <p className="text-foreground font-medium">
            {summary.token_reduction_pct}% fewer tokens. Same accuracy. Faster responses.
          </p>
        </div>
      </div>

      {/* Results Table */}
      <div className="space-y-4">
        <div className="border border-border rounded overflow-hidden">
          <Table>
            <TableHeader className="bg-secondary border-b border-border">
              <TableRow className="border-none hover:bg-secondary">
                <TableHead className="text-xs font-mono text-muted-foreground uppercase tracking-wider text-left">Pipeline</TableHead>
                <TableHead className="text-xs font-mono text-muted-foreground uppercase tracking-wider text-right">Tokens</TableHead>
                <TableHead className="text-xs font-mono text-muted-foreground uppercase tracking-wider text-right">Latency</TableHead>
                <TableHead className="text-xs font-mono text-muted-foreground uppercase tracking-wider text-right">Pass Rate</TableHead>
                <TableHead className="text-xs font-mono text-muted-foreground uppercase tracking-wider text-right">BERTScore</TableHead>
                <TableHead className="text-xs font-mono text-muted-foreground uppercase tracking-wider text-right">Cost/Query</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow className="border-b border-border hover:bg-card/50">
                <TableCell className="text-xs font-mono text-foreground font-medium">#ef4444 LLM-Only</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">{summary.pipeline1.avg_tokens}</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">4.09s</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">{summary.pipeline1.pass_rate}%</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">0.727</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">$0.000021</TableCell>
              </TableRow>
              <TableRow className="border-b border-border hover:bg-card/50">
                <TableCell className="text-xs font-mono text-foreground font-medium">#f59e0b Basic RAG</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">{summary.pipeline2.avg_tokens}</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">5.60s</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">{summary.pipeline2.pass_rate}%</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">0.710</TableCell>
                <TableCell className="text-xs font-mono text-foreground text-right">$0.000072</TableCell>
              </TableRow>
              <TableRow className="bg-emerald-900/10 hover:bg-emerald-900/20">
                <TableCell className="text-xs font-mono text-accent font-bold">GraphRAG</TableCell>
                <TableCell className="text-xs font-mono text-accent font-bold text-right">{summary.pipeline3.avg_tokens}</TableCell>
                <TableCell className="text-xs font-mono text-accent font-bold text-right">2.32s</TableCell>
                <TableCell className="text-xs font-mono text-accent font-bold text-right">{summary.pipeline3.pass_rate}%</TableCell>
                <TableCell className="text-xs font-mono text-accent font-bold text-right">0.714</TableCell>
                <TableCell className="text-xs font-mono text-accent font-bold text-right">$0.000015</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}
