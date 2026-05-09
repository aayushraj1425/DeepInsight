import type { AgentEvent, ChartSpec } from "../../types/events"
import { ChartsGrid } from "./ChartsGrid"
import { HeroCard } from "./HeroCard"
import { KeyTakeaways } from "./KeyTakeaways"
import { ResearchSidebar } from "./ResearchSidebar"
import type { ResearchSource } from "./ResearchSources"
import { ReportSection } from "./ReportSection"
import { Topbar } from "./Topbar"

const NAV_ITEMS = ["Dashboard", "Runs", "Agents", "Reports", "Settings"]

const HERO_METRICS = [
  { label: "Papers", value: "247" },
  { label: "Findings", value: "1,843" },
  { label: "Tools", value: "6" },
  { label: "Charts", value: "3" },
  { label: "Duration", value: "4m 12s" },
]

const REPORT_MARKDOWN = `# Research Report

## Bottom line
Sleep deprivation is associated with worse cognitive performance across extracted abstract-level findings.

## Evidence
- Reaction time and vigilance outcomes show the clearest deterioration signals.
- Working-memory accuracy trends downward after restricted sleep.
- Executive-control measures decline after acute sleep loss.
- The available findings mix outcome units, so charts should be read as directional evidence.

## Limitations
The pipeline uses abstract-derived findings and needs full-text review for publication-grade synthesis.`

const CHART_SPECS: ChartSpec[] = [
  {
    template: "bar_comparison",
    title: "Average extracted value by metric",
    insight: "Reaction-time slowing has the highest extracted value in the fixture data.",
    figure: {
      data: [
        {
          type: "bar",
          x: ["Reaction time", "Working memory", "Attention lapses", "Executive control"],
          y: [18.5, -9.2, 6.8, -0.42],
          marker: { color: ["#22d3ee", "#38bdf8", "#2dd4bf", "#64748b"] },
          hovertemplate: "<b>%{x}</b><br>Value: %{y}<extra></extra>",
        },
      ],
      layout: {
        title: { text: "Average extracted value by metric", x: 0.02 },
        xaxis: { gridcolor: "#111827" },
        yaxis: { gridcolor: "#1f2937", zerolinecolor: "#475569" },
      },
    },
  },
  {
    template: "timeline",
    title: "Extracted values over publication time",
    insight: "The fixture spans 2019 through 2023 across four extracted findings.",
    figure: {
      data: [
        {
          type: "scatter",
          mode: "markers+lines",
          x: [2019, 2020, 2021, 2023],
          y: [18.5, -9.2, 6.8, -0.42],
          marker: { color: "#22d3ee", size: 10 },
          line: { color: "#0e7490", width: 2 },
          hovertemplate: "Year: %{x}<br>Value: %{y}<extra></extra>",
        },
      ],
      layout: {
        title: { text: "Extracted values over publication time", x: 0.02 },
        xaxis: { gridcolor: "#1f2937", dtick: 1 },
        yaxis: { gridcolor: "#1f2937", zerolinecolor: "#475569" },
      },
    },
  },
]

const AGENT_EVENTS: AgentEvent[] = [
  {
    type: "node_start",
    agent: "planner",
    payload: { message: "Decomposing research question" },
    timestamp: "2026-05-09T15:00:00.000Z",
  },
  {
    type: "node_end",
    agent: "planner",
    payload: { subqueries: ["sleep deprivation cognition", "sleep loss vigilance"] },
    timestamp: "2026-05-09T15:00:04.000Z",
  },
  {
    type: "node_start",
    agent: "discovery",
    payload: { message: "Searching academic sources" },
    timestamp: "2026-05-09T15:00:05.000Z",
  },
  {
    type: "node_end",
    agent: "discovery",
    payload: { total_papers: 247 },
    timestamp: "2026-05-09T15:00:18.000Z",
  },
  {
    type: "node_start",
    agent: "extractor",
    payload: { message: "Extracting structured findings" },
    timestamp: "2026-05-09T15:00:19.000Z",
  },
  {
    type: "node_end",
    agent: "extractor",
    payload: { total_findings: 1843 },
    timestamp: "2026-05-09T15:01:02.000Z",
  },
  {
    type: "node_start",
    agent: "analyst",
    payload: { message: "Running aggregate and comparison tools" },
    timestamp: "2026-05-09T15:01:03.000Z",
  },
  {
    type: "tool_call",
    agent: "analyst",
    payload: { tool: "aggregate", findings_count: 1843 },
    timestamp: "2026-05-09T15:01:06.000Z",
  },
  {
    type: "node_end",
    agent: "analyst",
    payload: { tools_run: ["aggregate", "compare"], result_keys: ["aggregate", "compare"] },
    timestamp: "2026-05-09T15:01:22.000Z",
  },
  {
    type: "node_start",
    agent: "critic",
    payload: { message: "Reviewing analysis quality" },
    timestamp: "2026-05-09T15:01:23.000Z",
  },
  {
    type: "critic_decision",
    agent: "critic",
    payload: { decision: "approve", reasoning: "The analysis addresses the research question." },
    timestamp: "2026-05-09T15:01:35.000Z",
  },
  {
    type: "node_end",
    agent: "critic",
    payload: { approved: true },
    timestamp: "2026-05-09T15:01:36.000Z",
  },
  {
    type: "node_start",
    agent: "visualizer",
    payload: { message: "Rendering chart evidence" },
    timestamp: "2026-05-09T15:01:37.000Z",
  },
  {
    type: "chart_ready",
    agent: "visualizer",
    payload: { charts: 2, message: "Rendered chart evidence" },
    timestamp: "2026-05-09T15:01:49.000Z",
  },
  {
    type: "node_end",
    agent: "visualizer",
    payload: { chart_count: 2 },
    timestamp: "2026-05-09T15:01:50.000Z",
  },
  {
    type: "node_start",
    agent: "reporter",
    payload: { message: "Writing markdown report" },
    timestamp: "2026-05-09T15:01:51.000Z",
  },
  {
    type: "report_ready",
    agent: "reporter",
    payload: { length: REPORT_MARKDOWN.length, message: "Report ready" },
    timestamp: "2026-05-09T15:02:12.000Z",
  },
  {
    type: "node_end",
    agent: "reporter",
    payload: {},
    timestamp: "2026-05-09T15:02:13.000Z",
  },
  {
    type: "error",
    agent: "system",
    payload: { message: "Example recoverable stream warning" },
    timestamp: "2026-05-09T15:02:14.000Z",
  },
  {
    type: "done",
    agent: "system",
    payload: { message: "Research complete" },
    timestamp: "2026-05-09T15:02:15.000Z",
  },
]

const RESEARCH_SOURCES: ResearchSource[] = [
  {
    title: "Total sleep deprivation and sustained attention",
    provider: "Semantic Scholar",
    year: 2019,
    citationCount: 142,
    url: "https://www.semanticscholar.org/search?q=Total%20sleep%20deprivation%20and%20sustained%20attention",
  },
  {
    title: "Sleep restriction and working memory in adults",
    provider: "Semantic Scholar",
    year: 2020,
    citationCount: 96,
    url: "https://www.semanticscholar.org/search?q=Sleep%20restriction%20and%20working%20memory%20in%20adults",
  },
  {
    title: "Vigilance after overnight wakefulness",
    provider: "Semantic Scholar",
    year: 2021,
    citationCount: 73,
    url: "https://www.semanticscholar.org/search?q=Vigilance%20after%20overnight%20wakefulness",
  },
]

export function LayoutShell() {
  return (
    <div className="min-h-screen bg-[#0b0d10] text-slate-100">
      <Topbar />

      <div className="grid h-[calc(100svh-3.5rem)] grid-cols-1 overflow-hidden lg:grid-cols-[240px_minmax(0,1fr)]">
        <aside className="hidden border-r border-slate-800 bg-[#0f1217] lg:block">
          <div className="sticky top-14 flex h-[calc(100svh-3.5rem)] flex-col overflow-y-auto p-3">
            <nav className="space-y-1" aria-label="Primary navigation">
              {NAV_ITEMS.map((item, index) => (
                <a
                  key={item}
                  href="#"
                  className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                    index === 0
                      ? "bg-cyan-400/10 text-cyan-200 ring-1 ring-cyan-400/20"
                      : "text-slate-400 hover:bg-slate-800/70 hover:text-slate-100"
                  }`}
                >
                  {item}
                </a>
              ))}
            </nav>

            <div className="mt-auto rounded-md border border-slate-800 bg-slate-950/50 p-3">
              <div className="text-xs font-medium text-slate-300">System status</div>
              <div className="mt-2 h-2 rounded-full bg-slate-800">
                <div className="h-2 w-2/3 rounded-full bg-cyan-400" />
              </div>
            </div>
          </div>
        </aside>

        <main className="min-w-0 overflow-y-auto bg-[#0b0d10]" aria-label="Main content">
          <div className="mx-auto max-w-6xl space-y-5 px-4 py-5 sm:px-6 lg:px-8">
            <HeroCard
              status="running"
              title="Sleep deprivation and cognitive performance"
              summary="A structured research run comparing abstract-level findings across attention, working memory, vigilance, and executive-control outcomes."
              metrics={HERO_METRICS}
            />

            <KeyTakeaways markdown={REPORT_MARKDOWN} />

            <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
              <div className="space-y-5">
                <ChartsGrid charts={CHART_SPECS} />
                <ReportSection markdown={REPORT_MARKDOWN} />
              </div>
              <ResearchSidebar events={AGENT_EVENTS} isRunning sources={RESEARCH_SOURCES} />
            </section>
          </div>
        </main>
      </div>
    </div>
  )
}
