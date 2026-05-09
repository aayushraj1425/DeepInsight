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

const STATUS_COPY: Record<HeroStatus, { label: string; className: string; Icon: typeof Loader2 }> = {
  running: {
    label: "Running",
    className: "border-brand-accent/40 bg-brand-highlight text-brand-accent",
    Icon: Loader2,
  },
  done: {
    label: "Done",
    className: "border-emerald-300 bg-emerald-50 text-emerald-700",
    Icon: CheckCircle2,
  },
  error: {
    label: "Error",
    className: "border-red-300 bg-red-50 text-red-700",
    Icon: AlertTriangle,
  },
}

export function HeroCard({ status, title, summary, metrics }: HeroCardProps) {
  const statusConfig = STATUS_COPY[status]
  const StatusIcon = statusConfig.Icon

  return (
    <section className="rounded-2xl border border-[#E5E7EB] bg-white p-8 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)]">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${statusConfig.className}`}
          >
            <StatusIcon size={14} className={status === "running" ? "animate-spin" : ""} />
            {statusConfig.label}
          </div>

          <h1 className="mt-6 max-w-3xl font-serif text-3xl font-bold leading-tight tracking-tight text-brand-ink flex items-center gap-3">
            {title}
            {status === "done" && <Sparkles size={22} className="text-brand-accent" />}
          </h1>
          <p className="mt-4 max-w-4xl text-base leading-relaxed text-brand-muted font-light">
            {summary}
          </p>
        </div>

        <div className="grid shrink-0 grid-cols-2 gap-3 sm:grid-cols-4 lg:w-[380px] lg:grid-cols-2">
          {metrics.slice(0, 4).map((metric, i) => (
            <div
              key={metric.label}
              className="rounded-xl border border-[#E5E7EB] bg-brand-surface px-4 py-4 transition-all duration-200 hover:border-brand-accent/40 hover:shadow-[0_10px_30px_-10px_rgba(0,0,0,0.08)] hover:-translate-y-0.5"
              style={{ animation: `slideUp 0.5s ease-out ${i * 0.1}s both` }}
            >
              <div className="text-[11px] font-medium uppercase tracking-wider text-brand-muted">{metric.label}</div>
              <div className="mt-2 truncate font-mono text-2xl font-bold text-brand-ink">
                {metric.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
