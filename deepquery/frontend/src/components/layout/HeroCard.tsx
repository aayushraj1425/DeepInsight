import { AlertTriangle, CheckCircle2, Loader2, Sparkles } from "lucide-react"

export type HeroStatus = "running" | "done" | "error"

export interface HeroMetric {
  label: string
  value: string
}

interface HeroCardProps {
  status: HeroStatus
  title: string
  summary: string
  metrics: HeroMetric[]
}

export function HeroCard({ status, title, summary, metrics }: HeroCardProps) {
  return (
    <section className="rounded-2xl border border-brand-border bg-white p-6 shadow-[0_8px_30px_-8px_rgba(226,90,61,0.12)]">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          {/* Status badge */}
          <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold border ${
            status === "running" ? "border-brand-border bg-brand-highlight text-brand-accent" :
            status === "done"    ? "border-green-200 bg-green-50 text-green-700" :
                                   "border-red-200 bg-red-50 text-red-700"
          }`}>
            {status === "running" && <Loader2 size={13} className="animate-spin" />}
            {status === "done"    && <CheckCircle2 size={13} />}
            {status === "error"   && <AlertTriangle size={13} />}
            {status === "running" ? "Running" : status === "done" ? "Complete" : "Error"}
          </div>

          <h1 className="mt-4 font-serif text-2xl font-bold leading-tight tracking-tight text-brand-ink flex items-start gap-3">
            <span>{title}</span>
            {status === "done" && <Sparkles size={20} className="shrink-0 mt-1 text-brand-accent" />}
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-brand-muted">{summary}</p>
        </div>

        {/* Metrics */}
        <div className="grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-4 lg:w-[340px] lg:grid-cols-2">
          {metrics.slice(0, 4).map((metric, i) => (
            <div
              key={metric.label}
              className="rounded-xl border border-brand-border bg-brand-surface px-4 py-3.5 transition-all hover:border-brand-accent/40 hover:-translate-y-0.5 hover:shadow-[0_8px_20px_-4px_rgba(226,90,61,0.15)]"
              style={{ animation: `slideUp 0.4s ease-out ${i * 80}ms both` }}
            >
              <div className="text-[10px] font-semibold uppercase tracking-widest text-brand-muted">{metric.label}</div>
              <div className="mt-1.5 font-mono text-2xl font-bold text-brand-ink">{metric.value}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
