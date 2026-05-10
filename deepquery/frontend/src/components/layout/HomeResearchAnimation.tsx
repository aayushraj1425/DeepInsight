import { BarChart3, Brain, CheckCircle2, FileText, Search, ShieldCheck, Sigma } from "lucide-react"
import type { LucideIcon } from "lucide-react"

interface AgentNode {
  Icon: LucideIcon
  className: string
  delay: string
}

const AGENT_NODES: AgentNode[] = [
  { Icon: Brain, className: "left-[18%] top-[16%]", delay: "0ms" },
  { Icon: Search, className: "left-[32%] top-[66%]", delay: "300ms" },
  { Icon: FileText, className: "left-[50%] top-[8%]", delay: "600ms" },
  { Icon: Sigma, className: "right-[32%] top-[66%]", delay: "900ms" },
  { Icon: ShieldCheck, className: "right-[18%] top-[16%]", delay: "1200ms" },
]

export function HomeResearchAnimation() {
  return (
    <div
      className="relative mt-7 h-32 w-full max-w-2xl animate-slide-in overflow-hidden sm:h-36"
      style={{ animationDelay: "160ms" }}
      aria-hidden="true"
    >
      <div className="absolute left-[14%] right-[14%] top-1/2 h-px bg-brand-border" />
      <div className="home-flow-glow absolute left-[14%] right-[14%] top-1/2 h-px bg-brand-accent/50" />

      {[0, 1, 2].map((index) => (
        <span
          key={index}
          className="home-evidence-packet absolute left-1/2 top-1/2 h-2 w-2 rounded-full bg-brand-accent shadow-[0_0_14px_rgba(226,90,61,0.5)]"
          style={{ animationDelay: `${index * 850}ms` }}
        />
      ))}

      <div className="absolute left-0 top-1/2 hidden -translate-y-1/2 flex-col gap-2 sm:flex">
        {[0, 1, 2].map((index) => (
          <div
            key={index}
            className="home-paper-sheet flex h-9 w-24 items-center gap-2 rounded-lg border border-brand-border bg-white px-2 shadow-sm"
            style={{ animationDelay: `${index * 240}ms` }}
          >
            <FileText size={13} className="shrink-0 text-brand-accent" />
            <div className="space-y-1">
              <span className="block h-1 w-12 rounded bg-brand-border" />
              <span className="block h-1 w-8 rounded bg-brand-highlight" />
            </div>
          </div>
        ))}
      </div>

      <div className="absolute right-0 top-1/2 hidden h-20 w-24 -translate-y-1/2 items-end gap-1.5 rounded-lg border border-brand-border bg-white px-3 pb-3 shadow-sm sm:flex">
        {[34, 58, 42, 70].map((height, index) => (
          <span
            key={height}
            className="home-chart-bar w-3 rounded-t bg-brand-accent/80"
            style={{ height: `${height}%`, animationDelay: `${index * 180}ms` }}
          />
        ))}
        <BarChart3 size={13} className="absolute right-2 top-2 text-brand-accent/65" />
      </div>

      <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 sm:h-28 sm:w-28">
        <span className="home-evidence-ring absolute inset-0 rounded-full border border-brand-accent/25" />
        <span className="home-evidence-ring home-evidence-ring-delay absolute inset-2 rounded-full border border-brand-accent/20" />
        <div className="absolute inset-5 flex items-center justify-center rounded-2xl border border-brand-border bg-white shadow-[0_8px_24px_-10px_rgba(226,90,61,0.45)]">
          <ShieldCheck size={26} className="text-brand-accent" />
          <CheckCircle2 size={14} className="home-check-pop absolute right-4 top-4 text-emerald-600" />
          <span className="home-evidence-scan absolute left-4 right-4 top-1/2 h-px bg-brand-accent/55" />
        </div>
      </div>

      {AGENT_NODES.map(({ Icon, className, delay }) => (
        <span
          key={className}
          className={`home-agent-node absolute flex h-8 w-8 items-center justify-center rounded-full border border-brand-border bg-white text-brand-accent shadow-sm ${className}`}
          style={{ animationDelay: delay }}
        >
          <Icon size={14} />
        </span>
      ))}
    </div>
  )
}
