import { ChartCard } from "../ChartCard"
import type { ChartSpec } from "../../types/events"

interface ChartsGridProps {
  charts: ChartSpec[]
}

export function ChartsGrid({ charts }: ChartsGridProps) {
  if (charts.length === 0) {
    return (
      <section className="rounded-xl border border-[#E5E7EB] bg-brand-surface p-5">
        <h2 className="text-sm font-semibold text-brand-ink">Charts</h2>
        <p className="mt-3 text-sm text-brand-muted">No charts available.</p>
      </section>
    )
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-serif text-base font-bold text-brand-ink">Charts</h2>
        <span className="font-mono text-[11px] text-brand-muted">
          {charts.length} chart{charts.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="grid gap-6">
        {charts.map((chart, index) => (
          <ChartCard key={`${chart.template ?? "chart"}-${index}`} chart={chart} />
        ))}
      </div>
    </section>
  )
}
