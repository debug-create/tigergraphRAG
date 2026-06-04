"use client";
import { useEffect, useState } from "react";
import { getScaleComparison } from "@/lib/api";

function MetricRow({
  label, r1, r2, higherIsBetter = true, suffix = "%"
}: {
  label: string; r1: number | null; r2: number | null;
  higherIsBetter?: boolean; suffix?: string;
}) {
  const delta = r1 != null && r2 != null ? r2 - r1 : null;
  const improved = delta != null ? (higherIsBetter ? delta > 0 : delta < 0) : null;

  return (
    <div className="flex items-center justify-between gap-4 py-2.5
      border-b border-border last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <div className="flex items-center gap-6">
        <span className="w-20 text-right text-sm text-muted-foreground">
          {r1 != null ? `${r1}${suffix}` : "—"}
        </span>
        <span className="w-20 text-right text-sm font-medium text-foreground">
          {r2 != null ? `${r2}${suffix}` : "—"}
        </span>
        {delta != null && (
          <span className={`w-16 text-right text-xs font-medium ${
            improved ? "text-emerald-400" : "text-rose-400"
          }`}>
            {improved ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}{suffix}
          </span>
        )}
      </div>
    </div>
  );
}

export function ScaleComparisonPanel() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    getScaleComparison().then(setData).catch(() => {});
  }, []);

  const r1 = data?.round1;
  const r2 = data?.round2;

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <h3 className="mb-1 text-base font-semibold text-foreground">Scaling story</h3>
      <p className="mb-5 text-sm text-muted-foreground">
        How MediGraph&apos;s metrics changed from Round 1 (2M tokens) to Round 2 (100M+ tokens)
      </p>

      <div className="mb-4 flex items-center justify-end gap-6 text-xs text-muted-foreground">
        <span className="w-20 text-right">Round 1</span>
        <span className="w-20 text-right text-foreground/60">Round 2</span>
        <span className="w-16 text-right">Delta</span>
      </div>

      <MetricRow
        label="Corpus size"
        r1={r1 ? 2 : null}
        r2={r2?.corpus_tokens ? Math.round(r2.corpus_tokens / 1_000_000) : null}
        suffix="M tok"
        higherIsBetter={true}
      />
      <MetricRow
        label="Token reduction vs Basic RAG"
        r1={null}
        r2={r2?.avg_token_reduction_pct ?? null}
      />
      <MetricRow
        label="LLM-judge pass rate"
        r1={null}
        r2={r2?.llm_judge_pass_rate ?? null}
      />
      <MetricRow
        label="BERTScore F1 rescaled"
        r1={null}
        r2={r2?.bertscore_f1 != null ? Math.round(r2.bertscore_f1 * 100) / 100 : null}
        suffix=""
      />
    </div>
  );
}
