import { BadgeCheck, FileSearch, Gauge, ShieldCheck } from "lucide-react"
import type { SynthesisSummary } from "../../types/events"

interface ExecutiveSummaryCardProps {
  synthesis: SynthesisSummary
}

function confidenceLabel(value?: string) {
  if (!value) return "Reviewing"
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export function ExecutiveSummaryCard({ synthesis }: ExecutiveSummaryCardProps) {
  return (
    <section className="rounded-2xl border border-brand-border bg-white p-5 shadow-[0_8px_30px_-8px_rgba(226,90,61,0.12)] sm:p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-accent text-white shadow-[0_4px_12px_rgba(226,90,61,0.28)]">
              <BadgeCheck size={17} />
            </div>
            <span className="text-[11px] font-semibold uppercase tracking-widest text-brand-muted">
              Executive Summary
            </span>
          </div>
          <p className="text-base leading-7 text-brand-ink sm:text-lg">
            {synthesis.answer}
          </p>
        </div>

        <div className="grid shrink-0 gap-2 sm:grid-cols-3 lg:w-[330px] lg:grid-cols-1">
          <div className="rounded-xl border border-brand-border bg-brand-surface px-3 py-2.5">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
              <Gauge size={13} className="text-brand-accent" />
              Confidence
            </div>
            <div className="mt-1 text-sm font-semibold text-brand-ink">
              {confidenceLabel(synthesis.confidence)}
            </div>
          </div>
          <div className="rounded-xl border border-brand-border bg-brand-surface px-3 py-2.5">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
              <FileSearch size={13} className="text-brand-accent" />
              Evidence
            </div>
            <div className="mt-1 text-sm font-semibold text-brand-ink">
              {(synthesis.evidenceCount ?? 0).toLocaleString()} findings
              {typeof synthesis.studiesCount === "number" && ` / ${synthesis.studiesCount.toLocaleString()} sources`}
            </div>
          </div>
          {synthesis.mostReliableResult && (
            <div className="rounded-xl border border-brand-border bg-brand-surface px-3 py-2.5">
              <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
                <ShieldCheck size={13} className="text-brand-accent" />
                Most Reliable
              </div>
              <div className="mt-1 text-sm leading-5 text-brand-ink">
                {synthesis.mostReliableResult}
              </div>
            </div>
          )}
        </div>
      </div>

      {synthesis.mainLimitation && (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-800">
          {synthesis.mainLimitation}
        </div>
      )}
    </section>
  )
}
