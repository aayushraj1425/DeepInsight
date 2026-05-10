import { BarChart2 } from "lucide-react"
import { ChartCard } from "../ChartCard"
import type { ChartSpec, EvidenceSelection } from "../../types/events"

interface ChartsGridProps {
  charts: ChartSpec[]
  onEvidenceSelect?: (selection: EvidenceSelection) => void
}

export function ChartsGrid({ charts, onEvidenceSelect }: ChartsGridProps) {
  if (charts.length === 0) return null

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-accent shadow-[0_4px_12px_rgba(226,90,61,0.25)]">
          <BarChart2 size={15} className="text-white" />
        </div>
        <h2 className="font-serif text-base font-bold text-brand-ink">
          Visual Analysis
          <span className="ml-2 font-mono text-xs font-normal text-brand-muted">
            {charts.length} chart{charts.length !== 1 ? "s" : ""}
          </span>
        </h2>
      </div>

      <div className="grid gap-5">
        {charts.map((chart, i) => (
          <ChartCard
            key={`${chart.template ?? "chart"}-${i}`}
            chart={chart}
            onEvidenceSelect={onEvidenceSelect}
          />
        ))}
      </div>
    </section>
  )
}
