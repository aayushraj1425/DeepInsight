import type { LucideIcon } from "lucide-react"
import { BarChart3, Brain, Check, FileJson, FileText, Loader2, Search, ShieldCheck, Sigma, X } from "lucide-react"
import type { AgentEvent } from "../types/events"
import { cn } from "../lib/utils"

type AgentId = "planner" | "discovery" | "extractor" | "analyst" | "critic" | "visualizer" | "reporter"
type NodeStatus = "idle" | "running" | "done" | "rejected" | "error"

interface AgentStep {
  id: AgentId
  label: string
  detail: string
  Icon: LucideIcon
}

const AGENTS: AgentStep[] = [
  { id: "planner", label: "Planner", detail: "Splits the question", Icon: Brain },
  { id: "discovery", label: "Discovery", detail: "Searches papers", Icon: Search },
  { id: "extractor", label: "Extractor", detail: "Pulls findings", Icon: FileJson },
  { id: "analyst", label: "Analyst", detail: "Runs tools", Icon: Sigma },
  { id: "critic", label: "Critic", detail: "Approves or rejects", Icon: ShieldCheck },
  { id: "visualizer", label: "Visualizer", detail: "Builds charts", Icon: BarChart3 },
  { id: "reporter", label: "Reporter", detail: "Writes report", Icon: FileText },
]

const STATUS_CLASS: Record<NodeStatus, string> = {
  idle: "border-gray-800 bg-gray-900/50 text-gray-500",
  running: "border-blue-700 bg-blue-950/40 text-blue-100 ring-1 ring-blue-500/30",
  done: "border-emerald-800 bg-emerald-950/30 text-emerald-100",
  rejected: "border-red-800 bg-red-950/40 text-red-100",
  error: "border-red-700 bg-red-950/60 text-red-100",
}

function lastAgentEvent(events: AgentEvent[], agent: AgentId) {
  return [...events].reverse().find((event) => event.agent === agent) ?? null
}

function latestCriticDecision(events: AgentEvent[]) {
  return [...events].reverse().find((event) => event.type === "critic_decision") ?? null
}

function hasLaterEvent(events: AgentEvent[], timestamp: string, agent: AgentId) {
  return events.some((event) => event.agent === agent && event.timestamp > timestamp)
}

function statusFor(events: AgentEvent[], agent: AgentId): NodeStatus {
  const last = lastAgentEvent(events, agent)
  if (!last) return "idle"
  if (last.type === "error") return "error"
  if (last.type === "node_start") return "running"

  if (agent === "critic") {
    const decision = latestCriticDecision(events)
    if (
      decision?.payload.decision === "reject" &&
      !hasLaterEvent(events, decision.timestamp, "visualizer")
    ) {
      return "rejected"
    }
  }

  return "done"
}

function attemptsFor(events: AgentEvent[], agent: AgentId) {
  return events.filter((event) => event.agent === agent && event.type === "node_start").length
}

function StatusGlyph({ status }: { status: NodeStatus }) {
  if (status === "running") return <Loader2 size={14} className="animate-spin" />
  if (status === "done") return <Check size={14} />
  if (status === "rejected" || status === "error") return <X size={14} />
  return <span className="h-2 w-2 rounded-full bg-current opacity-50" />
}

export function AgentDAG({ events }: { events: AgentEvent[]; isRunning: boolean }) {
  const criticRejects = events.filter(
    (event) => event.type === "critic_decision" && event.payload.decision === "reject"
  ).length
  const completed = AGENTS.filter((agent) => {
    const status = statusFor(events, agent.id)
    return status === "done" || status === "rejected"
  }).length

  return (
    <section className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-100">Agent graph</h2>
          <p className="mt-1 text-xs text-gray-500">{completed}/7 stages completed</p>
        </div>
        {criticRejects > 0 && (
          <div className="rounded bg-red-950 px-2.5 py-1 text-xs font-medium text-red-200">
            {criticRejects} critic rejection{criticRejects === 1 ? "" : "s"}
          </div>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-7">
        {AGENTS.map(({ id, label, detail, Icon }, index) => {
          const status = statusFor(events, id)
          const attempts = attemptsFor(events, id)

          return (
            <div key={id} className="relative min-w-0">
              {index > 0 && (
                <div className="absolute -left-3 top-8 hidden h-px w-3 bg-gray-800 md:block" />
              )}
              <div className={cn("h-full rounded-lg border p-3 transition-colors", STATUS_CLASS[status])}>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <Icon size={17} className="shrink-0" />
                  <StatusGlyph status={status} />
                </div>
                <div className="truncate text-sm font-semibold">{label}</div>
                <div className="mt-1 min-h-8 text-xs leading-4 opacity-70">{detail}</div>
                {attempts > 1 && (
                  <div className="mt-2 text-[11px] font-medium opacity-80">
                    attempt {attempts}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
