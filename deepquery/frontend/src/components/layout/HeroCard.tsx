import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react"

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
    className: "border-cyan-400/30 bg-cyan-400/10 text-cyan-200",
    Icon: Loader2,
  },
  done: {
    label: "Done",
    className: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
    Icon: CheckCircle2,
  },
  error: {
    label: "Error",
    className: "border-red-400/30 bg-red-400/10 text-red-200",
    Icon: AlertTriangle,
  },
}

export function HeroCard({ status, title, summary, metrics }: HeroCardProps) {
  const statusConfig = STATUS_COPY[status]
  const StatusIcon = statusConfig.Icon

  return (
    <section className="rounded-lg border border-slate-800 bg-[#11151b] p-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${statusConfig.className}`}
          >
            <StatusIcon size={14} className={status === "running" ? "animate-spin" : ""} />
            {statusConfig.label}
          </div>

          <h1 className="mt-4 max-w-3xl text-2xl font-semibold leading-tight tracking-tight text-white">
            {title}
          </h1>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-400">
            {summary}
          </p>
        </div>

        <div className="grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-5 lg:w-[380px] lg:grid-cols-2">
          {metrics.slice(0, 5).map((metric) => (
            <div key={metric.label} className="rounded-md border border-slate-800 bg-slate-950/50 px-3 py-3">
              <div className="text-[11px] text-slate-500">{metric.label}</div>
              <div className="mt-1 truncate font-mono text-lg font-semibold text-slate-100">
                {metric.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
