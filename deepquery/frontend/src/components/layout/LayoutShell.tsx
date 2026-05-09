import { useState, useRef } from "react"
import type { ChartSpec, AgentEvent } from "../../types/events"
import { ChartsGrid } from "./ChartsGrid"
import { HeroCard } from "./HeroCard"
import { KeyTakeaways } from "./KeyTakeaways"
import { ResearchSidebar } from "./ResearchSidebar"
import type { ResearchSource } from "./ResearchSources"
import { ReportSection } from "./ReportSection"
import { Topbar } from "./Topbar"
import { InputView } from "./InputView"

const NAV_ITEMS = ["Dashboard", "Runs", "Agents", "Reports", "Settings"]

function latestAgentEvent(events: AgentEvent[], agent: string, type: string) {
  return [...events].reverse().find((e) => e.agent === agent && e.type === type) ?? null
}

export function LayoutShell() {
  const [isInputMode, setIsInputMode] = useState(true)
  const [isExiting, setIsExiting] = useState(false)
  const [query, setQuery] = useState("")
  const [charts, setCharts] = useState<ChartSpec[]>([])
  const [report, setReport] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [sources] = useState<ResearchSource[]>([])
  const [events, setEvents] = useState<AgentEvent[]>([])
  const esRef = useRef<EventSource | null>(null)

  const plannerEnd = latestAgentEvent(events, "planner", "node_end")
  const discoveryEnd = latestAgentEvent(events, "discovery", "node_end")
  const extractorEnd = latestAgentEvent(events, "extractor", "node_end")
  const analystEnd = latestAgentEvent(events, "analyst", "node_end")

  const canonicalQuestion = (plannerEnd?.payload.canonical_question as string | undefined) ?? query

  const lastMessage = [...events].reverse().find(
    (e) => typeof e.payload.message === "string"
  )?.payload.message as string | undefined

  const metrics = [
    { label: "Papers", value: String((discoveryEnd?.payload.total_papers as number) ?? 0) },
    { label: "Findings", value: String((extractorEnd?.payload.total_findings as number) ?? 0) },
    { label: "Tools", value: String(Array.isArray(analystEnd?.payload.tools_run) ? (analystEnd!.payload.tools_run as unknown[]).length : 0) },
    { label: "Charts", value: String(charts.length) },
  ]

  const handleAnalyze = async (q: string, files: File[]) => {
    setIsExiting(true)
    await new Promise<void>((resolve) => setTimeout(resolve, 320))

    setQuery(q)
    setIsInputMode(false)
    setIsExiting(false)
    setIsLoading(true)
    setCharts([])
    setReport("")
    setEvents([])

    esRef.current?.close()

    try {
      // Upload files first (if any), get back a pre-created session_id
      let uploadedSessionId: string | null = null
      if (files.length > 0) {
        const formData = new FormData()
        files.forEach((f) => formData.append("files", f))
        const uploadRes = await fetch("http://127.0.0.1:8000/api/upload", {
          method: "POST",
          body: formData,
        })
        const uploadData = await uploadRes.json()
        uploadedSessionId = uploadData.session_id
      }

      const res = await fetch("http://127.0.0.1:8000/api/investigations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, session_id: uploadedSessionId }),
      })
      const data = await res.json()
      const sessionId = data.id

      const es = new EventSource(`http://127.0.0.1:8000/api/stream/${sessionId}`)
      esRef.current = es

      es.onmessage = (e) => {
        const event = JSON.parse(e.data) as AgentEvent
        setEvents((prev) => [...prev, event])

        if (event.type === "chart_ready") {
          setCharts((event.payload.chart_specs as ChartSpec[]) || [])
        } else if (event.type === "report_ready") {
          setReport((event.payload.report as string) || "")
        } else if (event.type === "done") {
          setIsLoading(false)
          es.close()
        } else if (event.type === "error" && event.agent === "system") {
          setIsLoading(false)
          es.close()
        }
      }

      es.onerror = () => {
        setIsLoading(false)
        es.close()
      }
    } catch (err) {
      console.error(err)
      setIsLoading(false)
    }
  }

  const handleBack = () => {
    esRef.current?.close()
    setIsLoading(false)
    setIsInputMode(true)
  }

  return (
    <div className="min-h-screen bg-brand-background text-brand-ink relative font-sans">
      <div className="relative z-10">
        <Topbar onBack={isInputMode ? undefined : handleBack} />

        <div className={`grid h-[calc(100svh-3.5rem)] grid-cols-1 overflow-hidden ${!isInputMode ? "lg:grid-cols-[240px_minmax(0,1fr)]" : ""}`}>
          <aside className={`border-r border-[#E5E7EB] bg-brand-surface ${isInputMode ? "hidden" : "hidden lg:block"}`}>
            <div className="sticky top-14 flex h-[calc(100svh-3.5rem)] flex-col overflow-y-auto p-4">
              <nav className="space-y-1" aria-label="Primary navigation">
                {NAV_ITEMS.map((item, index) => (
                  <a
                    key={item}
                    href="#"
                    className={`block rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                      index === 0
                        ? "bg-brand-highlight text-brand-accent"
                        : "text-brand-muted hover:bg-brand-highlight/60 hover:text-brand-ink"
                    }`}
                  >
                    {item}
                  </a>
                ))}
              </nav>

              <div className="mt-auto rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)]">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs font-semibold text-brand-ink uppercase tracking-wider">System status</div>
                  <div className="h-2 w-2 rounded-full bg-brand-accent animate-pulse" />
                </div>
                <div className="h-1.5 rounded-full bg-[#E5E7EB] overflow-hidden">
                  <div className="h-full w-2/3 rounded-full bg-brand-accent" />
                </div>
              </div>
            </div>
          </aside>

          <main className="min-w-0 overflow-y-auto bg-brand-background" aria-label="Main content">
            {isInputMode ? (
              <div
                className="h-full transition-all duration-300 ease-in"
                style={isExiting ? { opacity: 0, transform: "translateY(-20px)" } : { opacity: 1, transform: "translateY(0)" }}
              >
                <InputView onAnalyze={handleAnalyze} />
              </div>
            ) : (
              <div className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:px-8 animate-slide-in">
                <HeroCard
                  status={isLoading ? "running" : "done"}
                  title={canonicalQuestion}
                  summary={isLoading ? "Agents are currently running analysis..." : "Research complete."}
                  metrics={metrics}
                />

                {isLoading && !report && charts.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-20 space-y-6">
                    <div className="relative h-20 w-20">
                      <div className="absolute inset-0 rounded-full border-4 border-[#E5E7EB]" />
                      <div className="absolute inset-0 rounded-full border-4 border-brand-accent border-t-transparent animate-spin" />
                    </div>
                    <div className="text-xl font-medium text-brand-ink animate-pulse">Running Research Pipeline...</div>
                    <p className="text-sm text-brand-muted max-w-xs text-center">{lastMessage ?? "Extracting findings and comparing outcomes"}</p>
                  </div>
                ) : (
                  <>
                    {report && <KeyTakeaways markdown={report} />}

                    <section className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_320px]">
                      <div className="space-y-8">
                        <ChartsGrid charts={charts} />
                        {report && <ReportSection markdown={report} />}
                      </div>
                      <ResearchSidebar sources={sources} />
                    </section>
                  </>
                )}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}
