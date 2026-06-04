"use client";
import { useEffect, useState } from "react";
import { getScaleComparison } from "@/lib/api";

export function TokenVerificationBadge() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getScaleComparison()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return null;

  const verified = data?.token_verification;
  const tokens = verified?.total_tokens;

  if (!verified || !tokens) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-border
        bg-secondary px-3 py-1 text-xs text-muted-foreground">
        Token count pending
      </span>
    );
  }

  const millions = (tokens / 1_000_000).toFixed(1);
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30
      bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
      {millions}M tokens — verified via Gemini count_tokens
    </span>
  );
}
