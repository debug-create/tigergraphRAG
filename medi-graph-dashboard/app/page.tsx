'use client'

import { useState } from 'react'
import { DashboardHeader } from '@/components/dashboard/header'
import { LiveQueryTab } from '@/components/dashboard/live-query-tab'
import { BenchmarkResultsTab } from '@/components/dashboard/benchmark-results-tab'
import { ScaleComparisonPanel } from '@/components/dashboard/scale-comparison-panel'
import { CostCalculator } from '@/components/dashboard/cost-calculator'
import { HeroStats } from '@/components/HeroStats'

export default function Home() {
  const [activeTab, setActiveTab] = useState('query')

  return (
    <div className="min-h-screen bg-background text-foreground">
      <DashboardHeader />
      <HeroStats />
      
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Minimal Tab Navigation */}
        <div className="flex gap-8 border-b border-border mb-8">
          <button
            onClick={() => setActiveTab('query')}
            className={`pb-3 text-sm font-medium transition-colors ${
              activeTab === 'query'
                ? 'text-foreground border-b-2 border-accent'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Live Query
          </button>
          <button
            onClick={() => setActiveTab('results')}
            className={`pb-3 text-sm font-medium transition-colors ${
              activeTab === 'results'
                ? 'text-foreground border-b-2 border-accent'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Benchmark Results
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'query' && <LiveQueryTab />}
        {activeTab === 'results' && <BenchmarkResultsTab />}

        {/* Scale Story Section */}
        <section className="mt-12">
          <h2 className="mb-4 text-lg font-semibold text-foreground">Scale story</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            <ScaleComparisonPanel />
            <CostCalculator />
          </div>
        </section>
      </div>
    </div>
  )
}
