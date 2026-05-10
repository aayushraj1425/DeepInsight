import { BarChart3, Brain, Check, FileJson, FileText, Loader2, RotateCcw, Search, ShieldCheck, Sigma, X } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import type { AgentEvent } from "../types/events"
import { cn } from "../lib/utils"

type AgentId = "planner" | "discovery" | "extractor" | "analyst" | "critic" | "visualizer" | "reporter"
type NodeStatus = "idle" | "running" | "done" | "rejected" | "error"

interface AgentStep {
  id: AgentId
  label: string
  Icon: LucideIcon
}

const AGENTS: AgentStep[] = [
  { id: "planner",    label: "Planner",    Icon: Brain },
  { id: "discovery",  label: "Discovery",  Icon: Search },
  { id: "extractor",  label: "Extractor",  Icon: FileJson },
  { id: "analyst",    label: "Analyst",    Icon: Sigma },
  { id: "critic",     label: "Critic",     Icon: ShieldCheck },
  { id: "visualizer", label: "Visualizer", Icon: BarChart3 },
  { id: "reporter",   label: "Reporter",   Icon: FileText },
]

function lastAgentEvent(events: AgentEvent[], agent: AgentId) {
  return [...events].reverse().find((e) => e.agent === agent) ?? null
}

function statusFor(events: AgentEvent[], agent: AgentId): NodeStatus {
  const last = lastAgentEvent(events, agent)
  if (!last) return "idle"
  if (last.type === "error") return "error"
  if (last.type === "node_start") return "running"
  if (agent === "critic") {
    const decision = [...events].reverse().find((e) => e.type === "critic_decision")
    if (decision?.payload.decision === "reject") {
      const hasVisualizer = events.some((e) => e.agent === "visualizer")
      if (!hasVisualizer) return "rejected"
    }
  }
  return "done"
}

function attemptsFor(events: AgentEvent[], agent: AgentId) {
  return events.filter((e) => e.agent === agent && e.type === "node_start").length
}

export function AgentDAG({ events, isRunning }: { events: AgentEvent[]; isRunning: boolean }) {
  const criticRejects = events.filter(
    (e) => e.type === "critic_decision" && e.payload.decision === "reject"
  ).length

  return (
    <div className="space-y-1">
      {AGENTS.map(({ id, label, Icon }) => {
        const status = statusFor(events, id)
        const attempts = attemptsFor(events, id)
        const isRetried = attempts > 1

        return (
          <div
            key={id}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-300",
              status === "idle"     && "text-brand-muted/50",
              status === "running"  && "bg-brand-highlight border border-brand-border text-brand-accent shadow-sm",
              status === "done"     && "text-brand-ink",
              status === "rejected" && "bg-amber-50 border border-amber-200 text-amber-700",
              status === "error"    && "bg-red-50 border border-red-200 text-red-700",
            )}
          >
            {/* Status dot */}
            <div className={cn(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded-full transition-all",
              status === "idle"     && "bg-gray-100 text-gray-300",
              status === "running"  && "bg-brand-accent text-white shadow-[0_0_10px_rgba(226,90,61,0.4)]",
              status === "done"     && "bg-green-100 text-green-600",
              status === "rejected" && "bg-amber-100 text-amber-600",
              status === "error"    && "bg-red-100 text-red-600",
            )}>
              {status === "running"  && <Loader2 size={12} className="animate-spin" />}
              {status === "done"     && <Check size={11} strokeWidth={3} />}
              {status === "rejected" && <X size={11} strokeWidth={3} />}
              {status === "error"    && <X size={11} strokeWidth={3} />}
              {status === "idle"     && <Icon size={11} />}
            </div>

            {/* Label */}
            <span className={cn(
              "flex-1 text-xs font-medium",
              status === "running" && "text-brand-accent font-semibold",
              status === "idle"    && "text-brand-muted/50",
            )}>
              {label}
            </span>

            {/* Retry badge */}
            {isRetried && (
              <span className="flex items-center gap-1 rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700">
                <RotateCcw size={8} />
                ×{attempts}
              </span>
            )}
          </div>
        )
      })}

      {/* Critic rejection summary */}
      {criticRejects > 0 && (
        <div className="mt-2 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-700">
          <ShieldCheck size={12} />
          {criticRejects} rejection{criticRejects > 1 ? "s" : ""} — re-searching with broader queries
        </div>
      )}

      {/* Running pulse */}
      {isRunning && (
        <div className="flex items-center gap-2 px-3 py-2 text-[11px] text-brand-muted/60">
          <span className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-1.5 w-1.5 rounded-full bg-brand-accent/50 animate-pulse-dot"
                style={{ animationDelay: `${i * 160}ms` }}
              />
            ))}
          </span>
          Agents working...
        </div>
      )}
    </div>
  )
}
