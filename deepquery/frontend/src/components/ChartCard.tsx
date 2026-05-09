import Plot from "react-plotly.js"
import type { Config, Data, Layout } from "plotly.js"
import { BarChart3 } from "lucide-react"
import { cn } from "../lib/utils"

export interface PlotlyFigure {
  data?: unknown[]
  layout?: Record<string, unknown>
  config?: Record<string, unknown>
}

export interface ChartSpec {
  template?: string
  title?: string
  insight?: string
  figure?: PlotlyFigure
}

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
    </section>
  )
}
