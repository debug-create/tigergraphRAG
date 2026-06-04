"use client";
import { useEffect, useState, useCallback } from "react";
import { getCostProjection } from "@/lib/api";

export function CostCalculator() {
  const [dailyQueries, setDailyQueries] = useState(100_000);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getCostProjection(dailyQueries, 65);
      setData(res);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dailyQueries]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const fmt = (n: number) =>
    n >= 1000
      ? `$${(n / 1000).toFixed(1)}K`
      : `$${n.toFixed(2)}`;

  const displayLabels: Record<number, string> = {
    1_000: "1K",
    10_000: "10K",
    100_000: "100K",
    1_000_000: "1M",
    10_000_000: "10M",
  };
  const steps = Object.keys(displayLabels).map(Number);
  const sliderIdx = steps.indexOf(dailyQueries);

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <h3 className="mb-1 text-base font-semibold text-foreground">Cost savings calculator</h3>
      <p className="mb-5 text-sm text-muted-foreground">
        Annual LLM spend: GraphRAG vs Basic RAG (Gemini 1.5 Flash pricing)
      </p>

      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Daily queries</span>
          <span className="text-sm font-medium text-foreground">
            {dailyQueries.toLocaleString()}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={steps.length - 1}
          step={1}
          value={sliderIdx >= 0 ? sliderIdx : 2}
          onChange={(e) => setDailyQueries(steps[parseInt(e.target.value)])}
          className="w-full accent-accent"
        />
        <div className="mt-1 flex justify-between text-xs text-muted-foreground">
          {steps.map((s) => (
            <span key={s}>{displayLabels[s]}</span>
          ))}
        </div>
      </div>

      {data && !loading ? (
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl bg-secondary p-4">
            <p className="mb-1 text-xs text-muted-foreground">Basic RAG / year</p>
            <p className="text-xl font-semibold text-red-400">
              {fmt(data.basic_rag_annual_cost_usd)}
            </p>
          </div>
          <div className="rounded-xl bg-secondary p-4">
            <p className="mb-1 text-xs text-muted-foreground">GraphRAG / year</p>
            <p className="text-xl font-semibold text-emerald-400">
              {fmt(data.graphrag_annual_cost_usd)}
            </p>
          </div>
          <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4">
            <p className="mb-1 text-xs text-emerald-400/70">Annual savings</p>
            <p className="text-xl font-semibold text-emerald-400">
              {fmt(data.annual_savings_usd)}
            </p>
          </div>
        </div>
      ) : (
        <div className="h-20 animate-pulse rounded-xl bg-secondary" />
      )}
    </div>
  );
}
