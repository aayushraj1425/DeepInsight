import { ChartCard } from "../ChartCard"
import type { ChartSpec } from "../../types/events"

interface ChartsGridProps {
  charts: ChartSpec[]
}

export function ChartsGrid({ charts }: ChartsGridProps) {
  if (charts.length === 0) {
    return (
      <section className="rounded-lg border border-slate-800 bg-[#11151b] p-5">
        <h2 className="text-sm font-semibold text-slate-100">Charts</h2>
        <p className="mt-3 text-sm text-slate-500">No charts available.</p>
      </section>
    )
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-slate-100">Charts</h2>
        <span className="font-mono text-[11px] text-slate-500">
          {charts.length} chart{charts.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className={charts.length === 1 ? "grid gap-4" : "grid gap-4 xl:grid-cols-2"}>
        {charts.map((chart, index) => (
          <ChartCard key={`${chart.template ?? "chart"}-${index}`} chart={chart} />
        ))}
      </div>
    </section>
  )
}
