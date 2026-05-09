import { useMemo } from "react"
import "./index.css"
import { useAgentStream } from "./hooks/useAgentStream"
import { QueryInput } from "./components/QueryInput"
import { AgentLog } from "./components/AgentLog"
import { ChartCard, type ChartSpec } from "./components/ChartCard"
import { ReportPanel } from "./components/ReportPanel"
import { CriticBanner } from "./components/CriticBanner"
import { AgentDAG } from "./components/AgentDAG"
import { RunSummary } from "./components/RunSummary"
import { ResultsPlaceholder } from "./components/ResultsPlaceholder"
import type { AgentEvent } from "./types/events"

function isChartSpec(value: unknown): value is ChartSpec {
  if (!value || typeof value !== "object") return false
  return "figure" in value
}

function latestEvent(events: AgentEvent[], type: AgentEvent["type"]) {
  return [...events].reverse().find((event) => event.type === type) ?? null
}

export default function App() {
  const { events, isRunning, sessionId, start, stop } = useAgentStream()
  const chartSpecs = useMemo(() => {
    const event = latestEvent(events, "chart_ready")
    const specs = event?.payload.chart_specs
    return Array.isArray(specs) ? specs.filter(isChartSpec) : []
  }, [events])

  const report = useMemo(() => {
    const event = latestEvent(events, "report_ready")
    return typeof event?.payload.report === "string" ? event.payload.report : null
  }, [events])

  const criticEvent = useMemo(() => {
    const event = latestEvent(events, "critic_decision")
    return event?.payload.decision === "reject" ? event : null
  }, [events])
  const hasResults = chartSpecs.length > 0 || Boolean(report)

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold">
              DQ
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">DeepQuery</h1>
          </div>
          <p className="text-gray-400 text-sm">
            Autonomous multi-agent research — watch agents think in real time
          </p>
        </div>

        <QueryInput onSubmit={start} onStop={stop} disabled={isRunning} />
        <CriticBanner event={criticEvent} />

        {sessionId && (
          <div className="mt-3 text-xs text-gray-600 font-mono">
            session: {sessionId}
          </div>
        )}

        <div className="mt-6 space-y-4">
          <RunSummary events={events} isRunning={isRunning} />
          <AgentDAG events={events} isRunning={isRunning} />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_420px]">
          <main className="min-w-0 space-y-5">
            {!hasResults && <ResultsPlaceholder isRunning={isRunning} />}
            {chartSpecs.length > 0 && (
              <div className={chartSpecs.length === 1 ? "grid gap-4" : "grid gap-4 xl:grid-cols-2"}>
                {chartSpecs.map((chart, index) => (
                  <ChartCard key={`${chart.template ?? "chart"}-${index}`} chart={chart} />
                ))}
              </div>
            )}
            <ReportPanel report={report} />
          </main>

          <aside className="min-w-0">
            <AgentLog events={events} isRunning={isRunning} />
          </aside>
        </div>
      </div>
    </div>
  )
}
