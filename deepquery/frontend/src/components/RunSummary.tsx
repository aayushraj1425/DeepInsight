import { Activity, BarChart3, BookOpen, FileSearch, Sigma } from "lucide-react"
import type { AgentEvent } from "../types/events"
import { cn } from "../lib/utils"

function latest(events: AgentEvent[], predicate: (event: AgentEvent) => boolean) {
  return [...events].reverse().find(predicate) ?? null
}

function payloadNumber(event: AgentEvent | null, key: string) {
  const value = event?.payload[key]
  return typeof value === "number" && Number.isFinite(value) ? value : 0
}

function payloadArrayLength(event: AgentEvent | null, key: string) {
  const value = event?.payload[key]
  return Array.isArray(value) ? value.length : 0
}

function activeMessage(events: AgentEvent[], isRunning: boolean) {
  if (!events.length) return "Ready for a research question"
  const last = latest(events, (event) => typeof event.payload.message === "string")
  if (!last) return isRunning ? "Agents are working" : "Run complete"
  return String(last.payload.message)
}

export function RunSummary({ events, isRunning }: { events: AgentEvent[]; isRunning: boolean }) {
  const discoveryEnd = latest(events, (event) => event.agent === "discovery" && event.type === "node_end")
  const extractorEnd = latest(events, (event) => event.agent === "extractor" && event.type === "node_end")
  const analystEnd = latest(events, (event) => event.agent === "analyst" && event.type === "node_end")
  const chartReady = latest(events, (event) => event.type === "chart_ready")
  const errored = events.some((event) => event.type === "error")
  const done = events.some((event) => event.type === "done")

  const items = [
    { label: "Papers", value: payloadNumber(discoveryEnd, "total_papers"), Icon: BookOpen },
    { label: "Findings", value: payloadNumber(extractorEnd, "total_findings"), Icon: FileSearch },
    { label: "Tools", value: payloadArrayLength(analystEnd, "tools_run"), Icon: Sigma },
    { label: "Charts", value: payloadNumber(chartReady, "charts"), Icon: BarChart3 },
  ]

  return (
    <section className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-100">
            <Activity size={16} className={cn(isRunning && "animate-pulse text-blue-300")} />
            {errored ? "Run failed" : done ? "Run complete" : isRunning ? "Investigation running" : "Investigation idle"}
          </div>
          <p className="mt-1 truncate text-sm text-gray-400">{activeMessage(events, isRunning)}</p>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:w-[460px]">
          {items.map(({ label, value, Icon }) => (
            <div key={label} className="rounded-lg border border-gray-800 bg-gray-950/50 px-3 py-2">
              <div className="mb-1 flex items-center gap-1.5 text-xs text-gray-500">
                <Icon size={13} />
                {label}
              </div>
              <div className="font-mono text-lg font-semibold text-gray-100">{value}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
