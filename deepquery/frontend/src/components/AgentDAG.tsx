import type { LucideIcon } from "lucide-react"
import {
  BarChart3,
  Brain,
  Check,
  FileCheck2,
  FileJson,
  FileText,
  Loader2,
  Database,
  Search,
  ShieldCheck,
  Sigma,
  Upload,
  X,
} from "lucide-react"

import { cn } from "../lib/utils"
import type { AgentEvent } from "../types/events"

type AgentId =
  | "ingestor"
  | "orchestrator"
  | "discovery"
  | "datafinder"
  | "validator"
  | "extractor"
  | "analyst"
  | "reasoner"
  | "economist"
  | "factchecker"
  | "visualizer"
  | "reporter"
type NodeStatus = "idle" | "running" | "done" | "rejected" | "error"

interface AgentStep {
  id: AgentId
  label: string
  detail: string
  Icon: LucideIcon
}

const AGENTS: AgentStep[] = [
  { id: "ingestor", label: "Ingestor", detail: "Reads uploads", Icon: Upload },
  { id: "orchestrator", label: "Orchestrator", detail: "Plans investigation", Icon: Brain },
  { id: "discovery", label: "Source Discovery", detail: "Searches papers", Icon: Search },
  { id: "datafinder", label: "Datafinder", detail: "Finds datasets", Icon: Database },
  { id: "validator", label: "Validator", detail: "Scores sources", Icon: FileCheck2 },
  { id: "extractor", label: "Extractor", detail: "Pulls findings", Icon: FileJson },
  { id: "analyst", label: "Analyst", detail: "Runs tools", Icon: Sigma },
  { id: "reasoner", label: "Reasoner", detail: "Connects causes", Icon: ShieldCheck },
  { id: "economist", label: "Economist", detail: "Builds scenarios", Icon: Sigma },
  { id: "factchecker", label: "Fact Checker", detail: "Verifies claims", Icon: FileCheck2 },
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

function latestFactCheck(events: AgentEvent[]) {
  return [...events].reverse().find((event) => event.type === "factcheck_ready") ?? null
}

function hasLaterEvent(events: AgentEvent[], timestamp: string, agent: AgentId) {
  return events.some((event) => event.agent === agent && event.timestamp > timestamp)
}

function statusFor(events: AgentEvent[], agent: AgentId): NodeStatus {
  const last = lastAgentEvent(events, agent)
  if (!last) return "idle"
  if (last.type === "error") return "error"
  if (last.type === "node_start") return "running"

  if (agent === "factchecker") {
    const decision = latestFactCheck(events)
    if (decision?.payload.approved_for_report === false && !hasLaterEvent(events, decision.timestamp, "visualizer")) {
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
  const factCheckFlags = events.filter(
    (event) => event.type === "factcheck_ready" && event.payload.approved_for_report === false
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
          <p className="mt-1 text-xs text-gray-500">{completed}/{AGENTS.length} stages completed</p>
        </div>
        {factCheckFlags > 0 && (
          <div className="rounded bg-red-950 px-2.5 py-1 text-xs font-medium text-red-200">
            {factCheckFlags} fact-check flag{factCheckFlags === 1 ? "" : "s"}
          </div>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        {AGENTS.map(({ id, label, detail, Icon }, index) => {
          const status = statusFor(events, id)
          const attempts = attemptsFor(events, id)

          return (
            <div key={id} className="relative min-w-0">
              {index > 0 && <div className="absolute -left-3 top-8 hidden h-px w-3 bg-gray-800 xl:block" />}
              <div className={cn("h-full rounded-lg border p-3 transition-colors", STATUS_CLASS[status])}>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <Icon size={17} className="shrink-0" />
                  <StatusGlyph status={status} />
                </div>
                <div className="truncate text-sm font-semibold">{label}</div>
                <div className="mt-1 min-h-8 text-xs leading-4 opacity-70">{detail}</div>
                {attempts > 1 && <div className="mt-2 text-[11px] font-medium opacity-80">attempt {attempts}</div>}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
