import {
  startTransition,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react"
import { FilePlus2, Play, RotateCcw, X } from "lucide-react"

import type {
  AgentEvent,
  ChartSpec,
  DatasetSource,
  SemanticScholarSource,
  UploadedDocument,
} from "../../types/events"
import { ChartsGrid } from "./ChartsGrid"
import { HeroCard, type HeroStatus } from "./HeroCard"
import { KeyTakeaways } from "./KeyTakeaways"
import { ResearchSidebar } from "./ResearchSidebar"
import type { DatasetCard, ResearchSource, UploadedDocumentCard } from "./ResearchSources"
import { ReportSection } from "./ReportSection"
import { Topbar } from "./Topbar"

const API_BASE =
  (
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    (import.meta.env.VITE_API_URL as string | undefined)
  )?.replace(/\/$/, "") ??
  (typeof window === "undefined"
    ? "http://127.0.0.1:8000"
    : `${window.location.protocol}//${window.location.hostname}:8000`)

const ACCEPTED_FILES = ".pdf,.docx,.txt,.md"

function asString(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback
}

function formatDuration(startedAt: number | null, endedAt: number | null, now: number) {
  if (!startedAt) return "--"
  const totalSeconds = Math.max(0, Math.floor(((endedAt ?? now) - startedAt) / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`
}

function latestEventCount(events: AgentEvent[], agent: string, key: string) {
  const match = [...events].reverse().find((event) => event.agent === agent && typeof event.payload[key] === "number")
  return match ? Number(match.payload[key]) : 0
}

function toDocumentCards(documents: UploadedDocument[]): UploadedDocumentCard[] {
  return documents.map((document) => ({
    source_id: document.source_id,
    name: document.name,
    kind: document.kind,
    excerpt: document.excerpt,
  }))
}

function toPaperCards(papers: SemanticScholarSource[]): ResearchSource[] {
  return papers.map((paper) => ({
    source_id: paper.source_id,
    title: paper.title,
    provider: paper.provider ?? "Research paper",
    url: paper.url,
    year: paper.year,
    citationCount: paper.citation_count,
    authors: paper.authors,
  }))
}

function toDatasetCards(datasets: DatasetSource[]): DatasetCard[] {
  return datasets.map((dataset) => ({
    source_id: dataset.source_id,
    title: dataset.title,
    provider: dataset.provider ?? "Dataset",
    description: dataset.description,
    url: dataset.url,
    resourceCount: dataset.resource_count,
    credibility: dataset.credibility,
    latestYear: dataset.latest_year,
  }))
}

function EmptyState() {
  return (
    <section className="rounded-lg border border-slate-800 bg-[#11151b] p-5">
      <h2 className="text-sm font-semibold text-slate-100">Start a live research run</h2>
      <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
        Ask a research question and DeepQuery will plan an evidence-first investigation, search scholarly and public
        data sources, validate source quality, fact-check claims, build cautious scenarios, and write a grounded report.
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {[
          "Investigate labor, market, policy, technical, or academic questions with multi-source evidence.",
          "Attach a draft only when you want the agent to refine or ground a paper you already have.",
          "Use charts as evidence explainers, not decorative output.",
        ].map((hint) => (
          <div key={hint} className="rounded-md border border-slate-800 bg-slate-950/50 p-3 text-sm text-slate-300">
            {hint}
          </div>
        ))}
      </div>
    </section>
  )
}

export function LayoutShell() {
  const [query, setQuery] = useState("")
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [submittedQuery, setSubmittedQuery] = useState("")
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [charts, setCharts] = useState<ChartSpec[]>([])
  const [report, setReport] = useState("")
  const [paperSources, setPaperSources] = useState<ResearchSource[]>([])
  const [documentSources, setDocumentSources] = useState<UploadedDocumentCard[]>([])
  const [datasetSources, setDatasetSources] = useState<DatasetCard[]>([])
  const [status, setStatus] = useState<HeroStatus>("idle")
  const [isRunning, setIsRunning] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [runStartedAt, setRunStartedAt] = useState<number | null>(null)
  const [runEndedAt, setRunEndedAt] = useState<number | null>(null)
  const [now, setNow] = useState(() => Date.now())

  const eventSourceRef = useRef<EventSource | null>(null)
  const closedByUsRef = useRef(false)

  function closeStream() {
    if (eventSourceRef.current) {
      closedByUsRef.current = true
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }

  function resetWorkspace() {
    closeStream()
    setQuery("")
    setSelectedFiles([])
    setSubmittedQuery("")
    setEvents([])
    setCharts([])
    setReport("")
    setPaperSources([])
    setDocumentSources([])
    setDatasetSources([])
    setStatus("idle")
    setIsRunning(false)
    setErrorMessage("")
    setRunStartedAt(null)
    setRunEndedAt(null)
  }

  function handleIncomingEvent(event: AgentEvent) {
    startTransition(() => {
      setEvents((current) => [...current, event])
    })

    if (event.type === "documents_ready") {
      const documents = Array.isArray(event.payload.documents) ? (event.payload.documents as UploadedDocument[]) : []
      setDocumentSources(toDocumentCards(documents))
      return
    }

    if (event.type === "sources_ready") {
      const papers = Array.isArray(event.payload.papers) ? (event.payload.papers as SemanticScholarSource[]) : []
      setPaperSources(toPaperCards(papers))
      return
    }

    if (event.type === "datasets_ready") {
      const datasets = Array.isArray(event.payload.datasets) ? (event.payload.datasets as DatasetSource[]) : []
      setDatasetSources(toDatasetCards(datasets))
      return
    }

    if (event.type === "chart_ready") {
      const nextCharts = Array.isArray(event.payload.chart_specs) ? (event.payload.chart_specs as ChartSpec[]) : []
      setCharts(nextCharts)
      return
    }

    if (event.type === "report_ready") {
      setReport(asString(event.payload.report))
      return
    }

    if (event.type === "error") {
      setErrorMessage(asString(event.payload.message, "The run failed."))
      setStatus("error")
      setIsRunning(false)
      setRunEndedAt(Date.now())
      closeStream()
      return
    }

    if (event.type === "done") {
      setStatus("done")
      setIsRunning(false)
      setRunEndedAt(Date.now())
      closeStream()
    }
  }

  useEffect(() => {
    if (!isRunning || !runStartedAt) return

    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [isRunning, runStartedAt])

  useEffect(() => () => closeStream(), [])

  function handleFileSelection(event: ChangeEvent<HTMLInputElement>) {
    const nextFiles = Array.from(event.target.files ?? [])
    if (nextFiles.length === 0) return

    setSelectedFiles((current) => {
      const seen = new Set(current.map((file) => `${file.name}:${file.size}:${file.lastModified}`))
      const merged = [...current]
      for (const file of nextFiles) {
        const key = `${file.name}:${file.size}:${file.lastModified}`
        if (!seen.has(key)) {
          seen.add(key)
          merged.push(file)
        }
      }
      return merged
    })
    event.target.value = ""
  }

  function removeFile(target: File) {
    setSelectedFiles((current) =>
      current.filter(
        (file) => !(file.name === target.name && file.size === target.size && file.lastModified === target.lastModified)
      )
    )
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextQuery = query.trim()
    if (!nextQuery || isRunning) return

    closeStream()
    setSubmittedQuery(nextQuery)
    setEvents([])
    setCharts([])
    setReport("")
    setPaperSources([])
    setDocumentSources([])
    setDatasetSources([])
    setErrorMessage("")
    setStatus("running")
    setIsRunning(true)
    setRunStartedAt(Date.now())
    setRunEndedAt(null)
    setNow(Date.now())

    const formData = new FormData()
    formData.append("query", nextQuery)
    for (const file of selectedFiles) {
      formData.append("files", file)
    }

    try {
      const response = await fetch(`${API_BASE}/api/investigations`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const failure = await response.text()
        throw new Error(failure || "Could not start research run.")
      }

      const payload = (await response.json()) as { id?: string }
      if (!payload.id) {
        throw new Error("Server did not return a session id.")
      }

      closedByUsRef.current = false
      const stream = new EventSource(`${API_BASE}/api/stream/${payload.id}`)
      eventSourceRef.current = stream
      stream.onmessage = (message) => {
        try {
          handleIncomingEvent(JSON.parse(message.data) as AgentEvent)
        } catch {
          // Ignore malformed events; the next event will usually recover the stream.
        }
      }
      stream.onerror = () => {
        if (closedByUsRef.current) {
          return
        }
        setErrorMessage("The live event stream was interrupted.")
        setStatus("error")
        setIsRunning(false)
        setRunEndedAt(Date.now())
        closeStream()
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not start research run.")
      setStatus("error")
      setIsRunning(false)
      setRunEndedAt(Date.now())
    }
  }

  const findingsCount =
    latestEventCount(events, "extractor", "total_findings") || latestEventCount(events, "extractor", "findings_extracted")
  const averageCredibility = latestEventCount(events, "validator", "average_credibility")
  const checkedClaims = latestEventCount(events, "factchecker", "checked_claims")
  const metrics = [
    { label: "Papers", value: paperSources.length.toString() },
    { label: "Datasets", value: datasetSources.length.toString() },
    { label: "Uploads", value: documentSources.length.toString() },
    { label: "Findings", value: findingsCount.toLocaleString() },
    { label: "Credibility", value: averageCredibility ? averageCredibility.toFixed(2) : "--" },
    { label: "Claims checked", value: checkedClaims ? checkedClaims.toString() : "--" },
    { label: "Charts", value: charts.length.toString() },
    { label: "Duration", value: formatDuration(runStartedAt, runEndedAt, now) },
  ]

  const summary = errorMessage
    ? errorMessage
    : isRunning
      ? "Streaming a live intelligence run: planning, source discovery, dataset validation, extraction, statistical analysis, causal synthesis, scenario modeling, fact-checking, and evidence-led visualization."
      : report
        ? "Live run complete. Review the intelligence report, validation-aware sources, scenario charts, and evidence trail below."
        : "Submit a research prompt. Uploads are optional and are best used for drafts, papers, or source material you want the investigation to consider."

  const topbarStatus = isRunning
    ? "Streaming live run"
    : errorMessage
      ? "Run needs attention"
      : report
        ? "Last run complete"
        : "Ready for prompt + files"

  const canReset = Boolean(
    query || selectedFiles.length > 0 || events.length > 0 || report || paperSources.length > 0 || documentSources.length > 0 || datasetSources.length > 0
  )

  return (
    <div className="min-h-screen bg-[#0b0d10] text-slate-100">
      <Topbar onReset={resetWorkspace} canReset={canReset} status={topbarStatus} />

      <main className="min-w-0 bg-[#0b0d10]" aria-label="Main content">
        <div className="mx-auto max-w-7xl space-y-5 px-4 py-5 sm:px-6 lg:px-8">
          <section className="rounded-lg border border-slate-800 bg-[#11151b] p-5">
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label htmlFor="research-query" className="text-sm font-semibold text-slate-100">
                  Research prompt
                </label>
                <textarea
                  id="research-query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Example: Compare retrieval-augmented generation evaluation methods for biomedical research assistants."
                  className="min-h-[130px] w-full rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm leading-7 text-slate-100 outline-none transition focus:border-cyan-500/60"
                />
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-slate-800 px-3 py-2 text-sm text-slate-300 transition hover:border-cyan-500/50 hover:text-cyan-200">
                  <FilePlus2 size={16} />
                  Attach files
                  <input type="file" multiple accept={ACCEPTED_FILES} className="hidden" onChange={handleFileSelection} />
                </label>

                <button
                  type="submit"
                  disabled={isRunning || !query.trim()}
                  className="inline-flex items-center gap-2 rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300"
                >
                  <Play size={16} />
                  {isRunning ? "Running..." : "Run research"}
                </button>

                <button
                  type="button"
                  onClick={resetWorkspace}
                  disabled={!canReset}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-800 px-3 py-2 text-sm text-slate-300 transition hover:border-cyan-500/50 hover:text-cyan-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <RotateCcw size={16} />
                  Clear
                </button>

                <span className="text-xs text-slate-500">Optional: PDF, DOCX, TXT, or Markdown context.</span>
              </div>

              {selectedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {selectedFiles.map((file) => (
                    <div
                      key={`${file.name}-${file.size}-${file.lastModified}`}
                      className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/60 px-3 py-1 text-xs text-slate-300"
                    >
                      <span>{file.name}</span>
                      <button
                        type="button"
                        onClick={() => removeFile(file)}
                        className="rounded-full text-slate-500 transition hover:text-slate-100"
                        aria-label={`Remove ${file.name}`}
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </form>
          </section>

          <HeroCard
            status={status}
            title={submittedQuery || "DeepQuery live research workspace"}
            summary={summary}
            metrics={metrics}
          />

          {report ? <KeyTakeaways markdown={report} /> : null}
          {!events.length && !isRunning && !report ? <EmptyState /> : null}

          <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
            <div className="space-y-5">
              <ChartsGrid charts={charts} />
              {report ? (
                <ReportSection markdown={report} />
              ) : (
                <section className="rounded-lg border border-slate-800 bg-[#11151b] p-5">
                  <h2 className="text-sm font-semibold text-slate-100">Report</h2>
                  <p className="mt-3 text-sm leading-7 text-slate-500">
                    {isRunning ? "The report will stream in after analysis completes." : "No report generated yet."}
                  </p>
                </section>
              )}
            </div>

            <ResearchSidebar
              events={events}
              isRunning={isRunning}
              sources={paperSources}
              documents={documentSources}
              datasets={datasetSources}
            />
          </section>
        </div>
      </main>
    </div>
  )
}
