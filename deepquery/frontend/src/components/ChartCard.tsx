import _Plot from "react-plotly.js"
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Plot = ((_Plot as any).default ?? _Plot) as typeof _Plot
import type { Config, Data, Layout } from "plotly.js"
import { BarChart3, Info, ShieldCheck } from "lucide-react"
import { cn } from "../lib/utils"
import type { ChartSpec } from "../types/events"

export type { ChartSpec, PlotlyFigure } from "../types/events"

interface Props {
  chart: ChartSpec
  className?: string
}

export function ChartCard({ chart, className }: Props) {
  const figure = chart.figure ?? {}
  const layout = {
    ...(figure.layout ?? {}),
    autosize: true,
    paper_bgcolor: "#111111",
    plot_bgcolor: "#111111",
    font: {
      color: "#e5e7eb",
      family: "Inter, ui-sans-serif, system-ui",
      ...((figure.layout?.font as object | undefined) ?? {}),
    },
    margin: {
      l: 64,
      r: 24,
      t: 56,
      b: 52,
      ...((figure.layout?.margin as object | undefined) ?? {}),
    },
  } as Partial<Layout>

  const config = {
    responsive: true,
    displayModeBar: false,
    ...(figure.config ?? {}),
  } as Partial<Config>

  return (
    <section className={cn("animate-slide-in rounded-lg border border-gray-800 bg-gray-900/60 p-4", className)}>
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-200">
        <BarChart3 size={16} className="text-green-400" />
        <span className="truncate">{chart.title ?? "Chart"}</span>
        {chart.argument_role && (
          <span className="ml-auto shrink-0 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-cyan-200">
            {chart.argument_role}
          </span>
        )}
      </div>
      <div className="h-[340px] min-w-0 overflow-hidden rounded bg-[#111111]">
        <Plot
          data={(figure.data ?? []) as Data[]}
          layout={layout}
          config={config}
          useResizeHandler
          style={{ width: "100%", height: "100%" }}
        />
      </div>
      {chart.insight && (
        <p className="mt-3 border-t border-gray-800 pt-3 text-sm leading-6 text-gray-300">
          {chart.insight}
        </p>
      )}
      {(chart.explanation || chart.selection_reason || chart.confidence || chart.caveat || chart.source_titles?.length) && (
        <div className="mt-3 space-y-2 rounded-md border border-gray-800 bg-gray-950/50 p-3 text-xs leading-5 text-gray-400">
          {chart.selection_reason && (
            <div>
              <span className="font-semibold text-cyan-200">Why this chart:</span> {chart.selection_reason}
              {typeof chart.impact_score === "number" && (
                <span className="ml-2 text-gray-500">Impact score {chart.impact_score.toFixed(1)}</span>
              )}
            </div>
          )}
          {chart.explanation && (
            <div className="flex gap-2">
              <Info size={14} className="mt-0.5 shrink-0 text-cyan-300" />
              <span>{chart.explanation}</span>
            </div>
          )}
          {chart.confidence && (
            <div className="flex gap-2">
              <ShieldCheck size={14} className="mt-0.5 shrink-0 text-emerald-300" />
              <span>
                <span className="font-semibold text-gray-300">Confidence:</span> {chart.confidence}
              </span>
            </div>
          )}
          {chart.source_titles && chart.source_titles.length > 0 && (
            <div>
              <span className="font-semibold text-gray-300">Sources:</span> {chart.source_titles.join("; ")}
            </div>
          )}
          {chart.caveat && (
            <div>
              <span className="font-semibold text-amber-200">Caveat:</span> {chart.caveat}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
