'use client'

import { Database, Zap, Network } from 'lucide-react'
import { ThemeToggle } from './theme-toggle'

export function DashboardHeader() {
  return (
    <div className="border-b border-border bg-background px-8 py-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-lg font-medium text-foreground">
            🐯 <span className="ml-1">MediGraph</span>
          </div>
          <div className="text-xs text-muted-foreground">/</div>
          <div className="text-sm text-muted-foreground">GraphRAG Inference Benchmark</div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-secondary rounded border border-border">
              <Database className="w-3 h-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">CORD-19</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-secondary rounded border border-border">
              <Zap className="w-3 h-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Gemini 2.5 Flash</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-secondary rounded border border-border">
              <Network className="w-3 h-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">TigerGraph</span>
            </div>
          </div>
          <div className="w-px h-6 bg-border"></div>
          <ThemeToggle />
        </div>
      </div>
    </div>
  )
}
