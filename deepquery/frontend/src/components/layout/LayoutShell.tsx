import { useState, useRef, useEffect } from "react"
import { Clock, ArrowRight } from "lucide-react"
import type { ChartSpec, AgentEvent } from "../../types/events"
import { ChartsGrid } from "./ChartsGrid"
import { HeroCard } from "./HeroCard"
import { KeyTakeaways } from "./KeyTakeaways"
import { ResearchSidebar } from "./ResearchSidebar"
import type { ResearchSource } from "./ResearchSources"
import { ReportSection } from "./ReportSection"
import { Topbar } from "./Topbar"
import { InputView } from "./InputView"

// ── History ──────────────────────────────────────────────────────────────────

interface HistoryEntry {
  query: string
  canonical: string
  ts: number
}

function loadHistory(): HistoryEntry[] {
  try { return JSON.parse(localStorage.getItem("dq_history") || "[]") } catch { return [] }
}

function saveToHistory(entry: HistoryEntry) {
  const prev = loadHistory().filter((h) => h.query !== entry.query)
  localStorage.setItem("dq_history", JSON.stringify([entry, ...prev].slice(0, 8)))
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function latestAgentEvent(events: AgentEvent[], agent: string, type: string) {
  return [...events].reverse().find((e) => e.agent === agent && e.type === type) ?? null
}

// ── Shell ─────────────────────────────────────────────────────────────────────

export function LayoutShell() {
  const [isInputMode, setIsInputMode] = useState(true)
  const [isExiting, setIsExiting] = useState(false)
  const [query, setQuery] = useState("")
  const [charts, setCharts] = useState<ChartSpec[]>([])
  const [report, setReport] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [sources, setSources] = useState<ResearchSource[]>([])
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory)
  const esRef = useRef<EventSource | null>(null)

  const plannerEnd   = latestAgentEvent(events, "planner",   "node_end")
  const discoveryEnd = latestAgentEvent(events, "discovery", "node_end")
  const extractorEnd = latestAgentEvent(events, "extractor", "node_end")
  const analystEnd   = latestAgentEvent(events, "analyst",   "node_end")

  const canonicalQuestion =
    (plannerEnd?.payload.canonical_question as string | undefined) ?? query

  const lastMessage = [...events].reverse().find(
    (e) => typeof e.payload.message === "string"
  )?.payload.message as string | undefined

  const metrics = [
    { label: "Papers",   value: String((discoveryEnd?.payload.total_papers  as number) ?? 0) },
    { label: "Findings", value: String((extractorEnd?.payload.total_findings as number) ?? 0) },
    { label: "Tools",    value: String(Array.isArray(analystEnd?.payload.tools_run) ? (analystEnd!.payload.tools_run as unknown[]).length : 0) },
    { label: "Charts",   value: String(charts.length) },
  ]

  // Refresh history display when returning to input mode
  useEffect(() => {
    if (isInputMode) setHistory(loadHistory())
  }, [isInputMode])

  // ── Handlers ────────────────────────────────────────────────────────────────

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
    setSources([])

    esRef.current?.close()

    try {
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

        if (event.type === "sources_ready") {
          setSources((event.payload.sources as ResearchSource[]) || [])
        } else if (event.type === "chart_ready") {
          setCharts((event.payload.chart_specs as ChartSpec[]) || [])
        } else if (event.type === "report_ready") {
          setReport((event.payload.report as string) || "")
        } else if (event.type === "done") {
          setIsLoading(false)
          es.close()
          // Save to history when research completes
          const canonical =
            (event.payload.canonical_question as string | undefined) ?? q
          const entry = { query: q, canonical, ts: Date.now() }
          saveToHistory(entry)
          setHistory(loadHistory())
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

  const handleHome = () => {
    esRef.current?.close()
    setIsLoading(false)
    setIsInputMode(true)
  }

  const handleDownload = () => {
    if (!report) return
    const filename = canonicalQuestion
      .slice(0, 50)
      .replace(/[^a-z0-9]+/gi, "-")
      .toLowerCase()
    const blob = new Blob(
      [`# ${canonicalQuestion}\n\n${report}`],
      { type: "text/markdown;charset=utf-8" }
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `deepquery-${filename}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleShare = async () => {
    const text = `DeepQuery: ${canonicalQuestion}`
    await navigator.clipboard.writeText(text)
  }

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-brand-background text-brand-ink relative font-sans">
      <div className="relative z-10">
        <Topbar
          onHome={handleHome}
          onDownload={report ? handleDownload : undefined}
          onShare={handleShare}
          showActions={!isInputMode}
        />

        <div className={`grid h-[calc(100svh-3.5rem)] grid-cols-1 overflow-hidden ${!isInputMode ? "lg:grid-cols-[240px_minmax(0,1fr)]" : ""}`}>

          {/* Sidebar — history, only on results page */}
          <aside className={`border-r border-[#E5E7EB] bg-brand-surface ${isInputMode ? "hidden" : "hidden lg:flex lg:flex-col"}`}>
            <div className="flex h-[calc(100svh-3.5rem)] flex-col overflow-y-auto p-4">

              <div className="mb-3 flex items-center gap-2">
                <Clock size={13} className="text-brand-accent" />
                <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
                  Recent
                </span>
              </div>

              <nav className="flex-1 space-y-1" aria-label="Research history">
                {history.length === 0 ? (
                  <p className="px-2 text-xs text-brand-muted/60 italic">No history yet.</p>
                ) : (
                  history.map((h) => (
                    <button
                      key={h.ts}
                      type="button"
                      onClick={() => handleAnalyze(h.query, [])}
                      className="group flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition-all hover:bg-brand-highlight"
                    >
                      <ArrowRight
                        size={12}
                        className="shrink-0 text-brand-muted/40 transition-colors group-hover:text-brand-accent"
                      />
                      <span className="truncate text-brand-muted group-hover:text-brand-ink transition-colors leading-snug">
                        {h.canonical || h.query}
                      </span>
                    </button>
                  ))
                )}
              </nav>

              {/* System status */}
              <div className="mt-4 rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)]">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-[11px] font-semibold text-brand-ink uppercase tracking-wider">
                    System status
                  </div>
                  <div className="h-2 w-2 rounded-full bg-brand-accent animate-pulse" />
                </div>
                <div className="h-1.5 rounded-full bg-[#E5E7EB] overflow-hidden">
                  <div className="h-full w-2/3 rounded-full bg-brand-accent" />
                </div>
              </div>
            </div>
          </aside>

          {/* Main */}
          <main className="min-w-0 overflow-y-auto bg-brand-background" aria-label="Main content">
            {isInputMode ? (
              <div
                className="h-full transition-all duration-300 ease-in"
                style={isExiting
                  ? { opacity: 0, transform: "translateY(-20px)" }
                  : { opacity: 1, transform: "translateY(0)" }}
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
                    <div className="text-xl font-medium text-brand-ink animate-pulse">
                      Running Research Pipeline...
                    </div>
                    <p className="text-sm text-brand-muted max-w-xs text-center">
                      {lastMessage ?? "Extracting findings and comparing outcomes"}
                    </p>
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
