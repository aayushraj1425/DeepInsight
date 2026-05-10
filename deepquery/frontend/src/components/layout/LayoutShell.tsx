import { useState, useRef, useEffect } from "react"
import { Clock, ArrowRight, FlaskConical } from "lucide-react"
import type { AgentEvent, ChartSpec, EvidenceSelection, SynthesisSummary } from "../../types/events"
import { ChartsGrid } from "./ChartsGrid"
import { ExecutiveSummaryCard } from "./ExecutiveSummaryCard"
import { HeroCard } from "./HeroCard"
import { KeyTakeaways } from "./KeyTakeaways"
import { ResearchSidebar } from "./ResearchSidebar"
import type { ResearchSource } from "./ResearchSources"
import { ReportSection } from "./ReportSection"
import { Topbar } from "./Topbar"
import { InputView } from "./InputView"
import { AgentDAG } from "../AgentDAG"

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

function latestAgentEvent(events: AgentEvent[], agent: string, type: string) {
  return [...events].reverse().find((e) => e.agent === agent && e.type === type) ?? null
}

function cleanMarkdownText(value: string) {
  return value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/_(.*?)_/g, "$1")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .replace(/^[-*]\s+/gm, "")
    .trim()
}

function fallbackSynthesisFromReport(markdown: string): SynthesisSummary | null {
  const match = markdown.match(/##\s+Bottom line\s+([\s\S]*?)(?=\n##\s+|\s*$)/i)
  const source = cleanMarkdownText(match ? match[1] : markdown.split("\n\n")[0] || "")
  if (!source) return null
  return {
    answer: source,
    confidence: "moderate",
  }
}

// ── Shell ─────────────────────────────────────────────────────────────────────

export function LayoutShell() {
  const [isInputMode, setIsInputMode] = useState(true)
  const [isExiting, setIsExiting] = useState(false)
  const [query, setQuery] = useState("")
  const [charts, setCharts] = useState<ChartSpec[]>([])
  const [report, setReport] = useState<string>("")
  const [synthesis, setSynthesis] = useState<SynthesisSummary | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [sources, setSources] = useState<ResearchSource[]>([])
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory)
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceSelection | null>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    return () => {
      esRef.current?.close()
    }
  }, [])

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

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handleAnalyze = async (q: string, files: File[]) => {
    if (isInputMode) {
      setIsExiting(true)
      await new Promise<void>((resolve) => setTimeout(resolve, 300))
    }

    setQuery(q)
    setIsInputMode(false)
    setIsExiting(false)
    setIsLoading(true)
    setCharts([])
    setReport("")
    setSynthesis(null)
    setEvents([])
    setSources([])
    setSelectedEvidence(null)
    esRef.current?.close()
    esRef.current = null

    try {
      let uploadedSessionId: string | null = null
      if (files.length > 0) {
        const formData = new FormData()
        files.forEach((f) => formData.append("files", f))
        const uploadRes = await fetch("http://127.0.0.1:8000/api/upload", {
          method: "POST", body: formData,
        })
        uploadedSessionId = (await uploadRes.json()).session_id
      }

      const res = await fetch("http://127.0.0.1:8000/api/investigations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, session_id: uploadedSessionId }),
      })
      const { id: sessionId } = await res.json()

      const es = new EventSource(`http://127.0.0.1:8000/api/stream/${sessionId}`)
      esRef.current = es

      es.onmessage = (e) => {
        const event = JSON.parse(e.data) as AgentEvent
        setEvents((prev) => [...prev.slice(-199), event])

        if (event.type === "sources_ready") {
          setSources((event.payload.sources as ResearchSource[]) || [])
        } else if (event.type === "synthesis_ready") {
          setSynthesis((event.payload.synthesis as SynthesisSummary | undefined) ?? null)
        } else if (event.type === "chart_ready") {
          setCharts((event.payload.chart_specs as ChartSpec[]) || [])
        } else if (event.type === "report_ready") {
          const nextReport = (event.payload.report as string) || ""
          setReport(nextReport)
          setSynthesis(
            (event.payload.synthesis as SynthesisSummary | undefined) ??
            fallbackSynthesisFromReport(nextReport)
          )
        } else if (event.type === "done") {
          setIsLoading(false)
          es.close()
          if (esRef.current === es) esRef.current = null
          const canonical = (event.payload.canonical_question as string | undefined) ?? q
          saveToHistory({ query: q, canonical, ts: Date.now() })
          setHistory(loadHistory())
        } else if (event.type === "error" && event.agent === "system") {
          setIsLoading(false)
          es.close()
          if (esRef.current === es) esRef.current = null
        }
      }

      es.onerror = () => {
        setIsLoading(false)
        es.close()
        if (esRef.current === es) esRef.current = null
      }
    } catch (err) {
      console.error(err)
      setIsLoading(false)
    }
  }

  const handleHome = () => {
    esRef.current?.close()
    esRef.current = null
    setIsLoading(false)
    setSelectedEvidence(null)
    setHistory(loadHistory())
    setIsInputMode(true)
  }

  const handleDownload = () => {
    if (!report) return
    const filename = canonicalQuestion.slice(0, 50).replace(/[^a-z0-9]+/gi, "-").toLowerCase()
    const blob = new Blob([`# ${canonicalQuestion}\n\n${report}`], { type: "text/markdown;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `deepquery-${filename}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleShare = async () => {
    await navigator.clipboard.writeText(`DeepQuery: ${canonicalQuestion}`)
  }

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-brand-background text-brand-ink font-sans">
      <Topbar
        onHome={handleHome}
        onDownload={report ? handleDownload : undefined}
        onShare={handleShare}
        showActions={!isInputMode}
      />

      <div className={`grid h-[calc(100svh-3.5rem)] grid-cols-1 overflow-hidden ${!isInputMode ? "lg:grid-cols-[260px_minmax(0,1fr)]" : ""}`}>

        {/* Left sidebar — history + live agent pipeline */}
        {!isInputMode && (
          <aside className="hidden lg:flex lg:flex-col border-r border-[#F3D5CC] bg-[#FFFAF8]">
            <div className="flex h-[calc(100svh-3.5rem)] flex-col overflow-y-auto p-4 gap-5">

              {/* Live Agent Pipeline */}
              <div className="rounded-xl border border-brand-border bg-white p-4 shadow-[0_4px_20px_-4px_rgba(226,90,61,0.08)]">
                <div className="mb-3 flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-highlight">
                    <FlaskConical size={13} className="text-brand-accent" />
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
                    Agent Pipeline
                  </span>
                </div>
                <AgentDAG events={events} isRunning={isLoading} />
              </div>

              {/* Research History */}
              <div className="flex-1">
                <div className="mb-2 flex items-center gap-2">
                  <Clock size={12} className="text-brand-accent" />
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
                    Recent
                  </span>
                </div>
                <nav className="space-y-1" aria-label="Research history">
                  {history.length === 0 ? (
                    <p className="px-2 text-xs text-brand-muted/60 italic">No history yet.</p>
                  ) : (
                    history.map((h) => (
                      <button
                        key={h.ts}
                        type="button"
                        onClick={() => handleAnalyze(h.query, [])}
                        className="group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition-all hover:bg-brand-highlight"
                      >
                        <ArrowRight size={11} className="shrink-0 text-brand-muted/40 transition-colors group-hover:text-brand-accent" />
                        <span className="truncate text-brand-muted group-hover:text-brand-ink transition-colors leading-snug">
                          {h.canonical || h.query}
                        </span>
                      </button>
                    ))
                  )}
                </nav>
              </div>
            </div>
          </aside>
        )}

        {/* Main content */}
        <main className="min-w-0 overflow-y-auto bg-brand-background" aria-label="Main content">
          {isInputMode ? (
            <div
              className="min-h-full transition-all duration-300"
              style={isExiting ? { opacity: 0, transform: "translateY(-16px)" } : { opacity: 1 }}
            >
              <InputView onAnalyze={handleAnalyze} />
            </div>
          ) : (
            <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6 lg:px-8 animate-slide-in">
              <HeroCard
                status={isLoading ? "running" : "done"}
                title={canonicalQuestion}
                summary={isLoading ? (lastMessage ?? "Agents are working on your research...") : "Research complete."}
                metrics={metrics}
              />

              {synthesis && <ExecutiveSummaryCard synthesis={synthesis} />}

              {isLoading && !report && charts.length === 0 ? (
                /* Loading state */
                <div className="flex flex-col items-center justify-center py-16 space-y-8">
                  {/* Spinner */}
                  <div className="relative h-16 w-16">
                    <div className="absolute inset-0 rounded-full border-4 border-brand-highlight" />
                    <div className="absolute inset-0 rounded-full border-4 border-brand-accent border-t-transparent animate-spin" />
                  </div>
                  <div className="text-center space-y-2">
                    <p className="text-lg font-semibold text-brand-ink">
                      {lastMessage ?? "Running Research Pipeline..."}
                    </p>
                    <p className="text-sm text-brand-muted">Extracting findings and comparing outcomes</p>
                  </div>

                  {/* Mobile agent pipeline — visible while loading on small screens */}
                  <div className="w-full max-w-sm lg:hidden rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                    <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
                      Agent Pipeline
                    </p>
                    <AgentDAG events={events} isRunning={isLoading} />
                  </div>
                </div>
              ) : (
                <>
                  {report && <KeyTakeaways markdown={report} />}
                  <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
                    <div className="space-y-6">
                      <ChartsGrid charts={charts} onEvidenceSelect={setSelectedEvidence} />
                      {report && <ReportSection markdown={report} />}
                    </div>
                    <ResearchSidebar sources={sources} selectedEvidence={selectedEvidence} />
                  </section>
                </>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
