import { useEffect, useId, useRef } from "react"
import * as d3 from "d3"
import { BarChart3 } from "lucide-react"
import { cn } from "../lib/utils"
import type { ChartDatumMeta, ChartSpec, EvidenceSelection } from "../types/events"

export type { ChartSpec, PlotlyFigure } from "../types/events"

interface Props {
  chart: ChartSpec
  className?: string
  onEvidenceSelect?: (selection: EvidenceSelection) => void
}

type ChartValue = string | number

interface ChartTrace {
  type?: string
  mode?: string
  orientation?: string
  x?: ChartValue[]
  y?: ChartValue[]
  text?: ChartValue[]
  customdata?: unknown[]
  marker?: {
    color?: string | string[] | number[]
  }
  error_x?: {
    array?: ChartValue[]
    arrayminus?: ChartValue[]
    visible?: boolean
  }
}

interface BarDatum {
  x: string
  y: number
  color: string
  meta: ChartDatumMeta
}

interface PointDatum {
  x: number
  y: number
  meta: ChartDatumMeta
}

interface ForestDatum {
  label: string
  value: number
  errorPlus: number
  errorMinus: number
  meta: ChartDatumMeta
}

type RenderMode = "bar" | "timeline" | "forest" | "unsupported"

function firstTrace(chart: ChartSpec): ChartTrace | null {
  const trace = chart.figure?.data?.[0]
  return trace && typeof trace === "object" ? trace as ChartTrace : null
}

function numericValue(value: ChartValue | undefined): number | null {
  if (value === undefined || value === null) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function metaAt(trace: ChartTrace, index: number): ChartDatumMeta {
  const value = trace.customdata?.[index]
  return value && typeof value === "object" ? value as ChartDatumMeta : {}
}

function hasEvidence(meta: ChartDatumMeta) {
  return Array.isArray(meta.evidence) && meta.evidence.length > 0
}

function evidenceSelection(chart: ChartSpec, label: string, meta: ChartDatumMeta): EvidenceSelection | null {
  if (!hasEvidence(meta)) return null
  return {
    chartTitle: chart.title ?? "Chart",
    label,
    evidence: meta.evidence ?? [],
  }
}

function sampleWeight(meta: ChartDatumMeta, maxSample: number) {
  const sampleSize = meta.sampleSize ?? 0
  if (!maxSample || sampleSize <= 0) return 1
  return 0.45 + 0.55 * Math.sqrt(sampleSize / maxSample)
}

function metaTooltip(meta: ChartDatumMeta) {
  const parts = []
  if (typeof meta.sampleSize === "number") parts.push(`n: ${meta.sampleSize.toLocaleString()}`)
  if (typeof meta.pValue === "number") parts.push(`p: ${meta.pValue < 0.001 ? "<0.001" : meta.pValue}`)
  if (typeof meta.significant === "boolean") parts.push(meta.significant ? "significant" : "not significant")
  return parts.length ? `<br/>${parts.join("<br/>")}` : ""
}

function displayLabel(value: string, limit = 34) {
  const label = value.replace(/_/g, " ").trim()
  if (label.length <= limit) return label
  return `${label.slice(0, limit - 1).trim()}...`
}

function renderModeFor(chart: ChartSpec): RenderMode {
  const trace = firstTrace(chart)
  if (!trace || !Array.isArray(trace.x) || !Array.isArray(trace.y)) return "unsupported"

  if (trace.type === "bar") return "bar"
  if (trace.type === "scatter") {
    if (chart.template === "forest_plot") return "forest"
    if (trace.y.some((value) => numericValue(value) === null)) return "forest"
    return "timeline"
  }

  return "unsupported"
}

export function ChartCard({ chart, className, onEvidenceSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartId = `chart-${useId().replace(/:/g, "")}`
  const renderMode = renderModeFor(chart)

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    if (renderMode === "unsupported") {
      d3.select(container).selectAll("svg").remove()
      return
    }

    d3.select(container).selectAll("*").remove()

    const dataObj = firstTrace(chart)
    if (!dataObj || !Array.isArray(dataObj.x) || !Array.isArray(dataObj.y)) return

    const type = dataObj.type

    const margin = renderMode === "forest" || renderMode === "bar"
      ? { top: 20, right: 34, bottom: 44, left: 210 }
      : { top: 20, right: 30, bottom: 40, left: 48 }
    const width = container.clientWidth - margin.left - margin.right
    const height = container.clientHeight - margin.top - margin.bottom
    if (width <= 0 || height <= 0) return

    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "absolute hidden rounded-md bg-brand-ink px-3 py-2 text-xs font-medium text-white shadow-xl pointer-events-none z-50")

    const svg = d3
      .select(container)
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    const defs = svg.append("defs")
    const nonSigPatternId = `${chartId}-non-significant`
    const nonSigPattern = defs.append("pattern")
      .attr("id", nonSigPatternId)
      .attr("patternUnits", "userSpaceOnUse")
      .attr("width", 6)
      .attr("height", 6)
    nonSigPattern.append("rect")
      .attr("width", 6)
      .attr("height", 6)
      .attr("fill", "#FFEDD5")
      .attr("opacity", 0.72)
    nonSigPattern.append("path")
      .attr("d", "M0,6 L6,0 M-1,1 L1,-1 M5,7 L7,5")
      .attr("stroke", "#E25A3D")
      .attr("stroke-width", 1)
      .attr("opacity", 0.45)

    if (type === "bar" && renderMode === "bar") {
      const data: BarDatum[] = dataObj.x.map((xVal, i) => ({
        x: String(xVal),
        y: Number(dataObj.y?.[i] ?? 0),
        color: Array.isArray(dataObj.marker?.color)
          ? String(dataObj.marker.color[i])
          : dataObj.marker?.color || "#E25A3D",
        meta: metaAt(dataObj, i),
      })).filter((d) => Number.isFinite(d.y))

      if (data.length === 0) return

      const minX = d3.min(data, (d) => d.y) ?? 0
      const maxX = d3.max(data, (d) => d.y) ?? 0

      const x = d3.scaleLinear().domain([Math.min(0, minX), Math.max(0, maxX)]).nice().range([0, width])
      const y = d3.scaleBand<string>().domain(data.map((d) => d.x)).range([0, height]).padding(0.28)
      const maxSample = d3.max(data, (d) => d.meta.sampleSize ?? 0) ?? 0

      svg.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(-height).tickFormat(() => ""))
        .selectAll("line")
        .attr("stroke", "#E5E7EB")
        .attr("stroke-dasharray", "3,3")

      svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(0).ticks(5))
        .call((g) => g.select(".domain").attr("stroke", "#E5E7EB"))
        .selectAll("text")
        .attr("dy", "1em")
        .attr("fill", "#666666")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")

      svg.append("g")
        .call(d3.axisLeft(y).tickSize(0).tickFormat((value) => displayLabel(String(value))))
        .call((g) => g.select(".domain").attr("stroke", "#E5E7EB"))
        .selectAll("text")
        .attr("dx", "-0.5em")
        .attr("fill", "#666666")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")

      data.forEach((_row, i) => {
        const gradientId = `${chartId}-bar-${i}`
        const gradient = defs.append("linearGradient")
          .attr("id", gradientId)
          .attr("x1", "0%").attr("x2", "100%")
          .attr("y1", "0%").attr("y2", "0%")
        gradient.append("stop").attr("offset", "0%").attr("stop-color", "#FFEDD5").attr("stop-opacity", 1)
        gradient.append("stop").attr("offset", "100%").attr("stop-color", "#E25A3D").attr("stop-opacity", 1)
      })

      svg.selectAll<SVGPathElement, BarDatum>(".bar")
        .data(data)
        .enter()
        .append("path")
        .attr("class", "bar")
        .attr("fill", (d, i) => d.meta.significant === false ? `url(#${nonSigPatternId})` : `url(#${chartId}-bar-${i})`)
        .attr("cursor", (d) => hasEvidence(d.meta) ? "pointer" : "default")
        .attr("d", (d) => {
          const zero = x(0)
          const barX = Math.min(x(d.y), zero)
          const barWidth = Math.abs(x(d.y) - zero)
          const r = 4
          const h = y.bandwidth() * sampleWeight(d.meta, maxSample)
          const yVal = y(d.x)! + (y.bandwidth() - h) / 2
          if (d.y >= 0) {
            return `M${zero},${yVal} L${barX + barWidth - r},${yVal} Q${barX + barWidth},${yVal} ${barX + barWidth},${yVal + r} L${barX + barWidth},${yVal + h - r} Q${barX + barWidth},${yVal + h} ${barX + barWidth - r},${yVal + h} L${zero},${yVal + h} Z`
          }
          return `M${zero},${yVal} L${barX + r},${yVal} Q${barX},${yVal} ${barX},${yVal + r} L${barX},${yVal + h - r} Q${barX},${yVal + h} ${barX + r},${yVal + h} L${zero},${yVal + h} Z`
        })
        .style("opacity", 0)
        .on("mouseover", function (event, d) {
          tooltip.html(`<b>${displayLabel(d.x, 80)}</b><br/>Value: ${d.y}${metaTooltip(d.meta)}`)
                 .style("left", `${event.pageX + 10}px`)
                 .style("top", `${event.pageY - 28}px`)
                 .classed("hidden", false)
          d3.select(this).style("filter", "drop-shadow(0 4px 12px rgba(226,90,61,0.35))")
        })
        .on("click", (_event, d) => {
          const selection = evidenceSelection(chart, d.x, d.meta)
          if (selection) onEvidenceSelect?.(selection)
        })
        .on("mouseout", function () {
          tooltip.classed("hidden", true)
          d3.select(this).style("filter", "none")
        })
        .transition()
        .duration(800)
        .delay((_, i) => i * 100)
        .style("opacity", 1)

    } else if (type === "scatter" && renderMode === "forest") {
      const data: ForestDatum[] = dataObj.x.map((xVal, i) => {
        const value = numericValue(xVal)
        const errorPlus = numericValue(dataObj.error_x?.array?.[i]) ?? 0
        const errorMinus = numericValue(dataObj.error_x?.arrayminus?.[i]) ?? 0
        return {
          label: String(dataObj.y?.[i] ?? `Finding ${i + 1}`),
          value: value ?? Number.NaN,
          errorPlus,
          errorMinus,
          meta: metaAt(dataObj, i),
        }
      }).filter((d) => Number.isFinite(d.value))

      if (data.length === 0) return

      const low = d3.min(data, (d) => d.value - d.errorMinus) ?? 0
      const high = d3.max(data, (d) => d.value + d.errorPlus) ?? 0
      const x = d3.scaleLinear().domain([Math.min(0, low), Math.max(0, high)]).nice().range([0, width])
      const y = d3.scaleBand<string>().domain(data.map((d) => d.label)).range([0, height]).padding(0.34)
      const maxSample = d3.max(data, (d) => d.meta.sampleSize ?? 0) ?? 0

      svg.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(-height).tickFormat(() => ""))
        .selectAll("line")
        .attr("stroke", "#E5E7EB")
        .attr("stroke-dasharray", "3,3")

      svg.append("line")
        .attr("x1", x(0))
        .attr("x2", x(0))
        .attr("y1", 0)
        .attr("y2", height)
        .attr("stroke", "#9CA3AF")
        .attr("stroke-dasharray", "4,4")

      svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(0).ticks(5))
        .call((g) => g.select(".domain").attr("stroke", "#E5E7EB"))
        .selectAll("text")
        .attr("dy", "1em")
        .attr("fill", "#666666")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")

      svg.append("g")
        .call(d3.axisLeft(y).tickSize(0))
        .call((g) => g.select(".domain").attr("stroke", "#E5E7EB"))
        .selectAll("text")
        .attr("dx", "-0.5em")
        .attr("fill", "#666666")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")

      const rows = svg.selectAll<SVGGElement, ForestDatum>(".forest-row")
        .data(data)
        .enter()
        .append("g")
        .attr("class", "forest-row")
        .attr("transform", (d) => `translate(0,${(y(d.label) ?? 0) + y.bandwidth() / 2})`)
        .style("opacity", 0)

      rows.append("line")
        .attr("x1", (d) => x(d.value - d.errorMinus))
        .attr("x2", (d) => x(d.value + d.errorPlus))
        .attr("y1", 0)
        .attr("y2", 0)
        .attr("stroke", "#E25A3D")
        .attr("stroke-width", 2)
        .attr("stroke-linecap", "round")
        .attr("opacity", (d) => d.errorPlus || d.errorMinus ? 1 : 0)

      rows.append("circle")
        .attr("cx", (d) => x(d.value))
        .attr("cy", 0)
        .attr("r", (d) => 4 + 4 * sampleWeight(d.meta, maxSample))
        .attr("fill", (d) => d.meta.significant === false ? `url(#${nonSigPatternId})` : d.meta.significant === true ? "#E25A3D" : "#FFFFFF")
        .attr("stroke", "#E25A3D")
        .attr("stroke-width", 2.5)
        .attr("cursor", (d) => hasEvidence(d.meta) ? "pointer" : "default")
        .on("mouseover", function (event, d) {
          tooltip.html(`<b>${d.label}</b><br/>Value: ${d.value}${metaTooltip(d.meta)}`)
                 .style("left", `${event.pageX + 10}px`)
                 .style("top", `${event.pageY - 28}px`)
                 .classed("hidden", false)
          d3.select(this).transition().duration(200).attr("r", 8).attr("fill", "#E25A3D")
        })
        .on("click", (_event, d) => {
          const selection = evidenceSelection(chart, d.label, d.meta)
          if (selection) onEvidenceSelect?.(selection)
        })
        .on("mouseout", function () {
          tooltip.classed("hidden", true)
          d3.select(this)
            .transition()
            .duration(200)
            .attr("r", (d) => 4 + 4 * sampleWeight((d as ForestDatum).meta, maxSample))
            .attr("fill", (d) => {
              const meta = (d as ForestDatum).meta
              return meta.significant === false ? `url(#${nonSigPatternId})` : meta.significant === true ? "#E25A3D" : "#FFFFFF"
            })
        })

      rows.transition()
        .duration(650)
        .delay((_, i) => i * 80)
        .style("opacity", 1)

    } else if (type === "scatter" && renderMode === "timeline") {
      const data: PointDatum[] = dataObj.x.map((xVal, i) => ({
        x: Number(xVal),
        y: Number(dataObj.y?.[i] ?? 0),
        meta: metaAt(dataObj, i),
      })).filter((d) => Number.isFinite(d.x) && Number.isFinite(d.y))

      if (data.length === 0) return

      const color = "#E25A3D"
      const xExtent = d3.extent(data, (d) => d.x)
      const minX = xExtent[0] ?? 0
      const maxX = xExtent[1] ?? minX + 1
      const minY = d3.min(data, (d) => d.y) ?? 0
      const maxY = d3.max(data, (d) => d.y) ?? 0
      const baseline = Math.min(0, minY)
      const yMax = maxY === baseline ? baseline + 1 : maxY

      const x = d3.scaleLinear().domain([minX, maxX === minX ? minX + 1 : maxX + 1]).range([0, width])

      const y = d3.scaleLinear().domain([baseline, yMax]).nice().range([height, 0])
      const maxSample = d3.max(data, (d) => d.meta.sampleSize ?? 0) ?? 0

      svg.append("g")
        .attr("class", "grid")
        .call(d3.axisLeft(y).tickSize(-width).tickFormat(() => ""))
        .selectAll("line")
        .attr("stroke", "#E5E7EB")
        .attr("stroke-dasharray", "3,3")

      svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickFormat(d3.format("d")).tickSize(0).ticks(5))
        .call((g) => g.select(".domain").attr("stroke", "#E5E7EB"))
        .selectAll("text")
        .attr("dy", "1em")
        .attr("fill", "#666666")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")

      svg.append("g")
        .call(d3.axisLeft(y).tickSize(0).ticks(5))
        .call((g) => g.select(".domain").attr("stroke", "#E5E7EB"))
        .selectAll("text")
        .attr("dx", "-0.5em")
        .attr("fill", "#666666")
        .attr("font-size", "11px")
        .attr("font-family", "Inter, sans-serif")

      const line = d3.line<PointDatum>()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveMonotoneX)

      const area = d3.area<PointDatum>()
        .x(d => x(d.x))
        .y0(y(baseline))
        .y1(d => y(d.y))
        .curve(d3.curveMonotoneX)

      const areaGradientId = `${chartId}-area`
      const gradient = defs.append("linearGradient")
        .attr("id", areaGradientId)
        .attr("x1", "0%").attr("y1", "0%")
        .attr("x2", "0%").attr("y2", "100%")
      gradient.append("stop").attr("offset", "0%").attr("stop-color", color).attr("stop-opacity", 0.2)
      gradient.append("stop").attr("offset", "100%").attr("stop-color", color).attr("stop-opacity", 0)

      svg.append("path")
        .datum(data)
        .attr("fill", `url(#${areaGradientId})`)
        .attr("d", area)
        .style("opacity", 0)
        .transition().duration(1000).style("opacity", 1)

      const path = svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2.5)
        .attr("d", line)

      const pathNode = path.node()
      if (pathNode) {
        const totalLength = pathNode.getTotalLength()
        path
          .attr("stroke-dasharray", totalLength + " " + totalLength)
          .attr("stroke-dashoffset", totalLength)
          .transition().duration(1500).ease(d3.easeLinear).attr("stroke-dashoffset", 0)
      }

      svg.selectAll<SVGCircleElement, PointDatum>(".dot")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", (d) => x(d.x))
        .attr("cy", (d) => y(d.y))
        .attr("r", (d) => 4 + 4 * sampleWeight(d.meta, maxSample))
        .attr("fill", (d) => d.meta.significant === false ? `url(#${nonSigPatternId})` : d.meta.significant === true ? color : "#FFFFFF")
        .attr("stroke", color)
        .attr("stroke-width", 2)
        .attr("cursor", (d) => hasEvidence(d.meta) ? "pointer" : "default")
        .on("mouseover", function (event, d) {
          tooltip.html(`<b>${d.x}</b><br/>Value: ${d.y}${metaTooltip(d.meta)}`)
                 .style("left", `${event.pageX + 10}px`)
                 .style("top", `${event.pageY - 28}px`)
                 .classed("hidden", false)
          d3.select(this).transition().duration(200).attr("r", 7).attr("fill", color)
        })
        .on("click", (_event, d) => {
          const selection = evidenceSelection(chart, String(d.x), d.meta)
          if (selection) onEvidenceSelect?.(selection)
        })
        .on("mouseout", function () {
          tooltip.classed("hidden", true)
          d3.select(this)
            .transition()
            .duration(200)
            .attr("r", (d) => 4 + 4 * sampleWeight((d as PointDatum).meta, maxSample))
            .attr("fill", (d) => {
              const meta = (d as PointDatum).meta
              return meta.significant === false ? `url(#${nonSigPatternId})` : meta.significant === true ? color : "#FFFFFF"
            })
        })
        .style("opacity", 0)
        .transition().delay((_, i) => 1500 + i * 100).duration(500).style("opacity", 1)
    }

    return () => {
      d3.selectAll(".absolute.hidden.rounded-md").remove()
    }
  }, [chart, chartId, onEvidenceSelect, renderMode])

  return (
    <section className={cn(
      "animate-slide-in rounded-2xl border border-brand-border bg-white p-5",
      "shadow-[0_8px_30px_-8px_rgba(226,90,61,0.10)] transition-all duration-200",
      "hover:shadow-[0_12px_36px_-8px_rgba(226,90,61,0.18)] hover:-translate-y-0.5",
      className
    )}>
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-highlight border border-brand-border text-brand-accent">
          <BarChart3 size={15} />
        </div>
        <span className="truncate font-serif text-base font-bold text-brand-ink">{chart.title ?? "Chart"}</span>
      </div>
      <div ref={containerRef} className="relative h-[400px] w-full min-w-0 rounded-xl bg-brand-surface overflow-hidden">
        {renderMode === "unsupported" && (
          <div className="flex h-full items-center justify-center px-6 text-center text-sm text-brand-muted">
            No renderable data for this chart.
          </div>
        )}
      </div>
      {chart.insight && (
        <div className="mt-4 pt-4 border-t border-brand-border">
          <p className="text-xs leading-relaxed text-brand-muted flex items-start gap-2">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-accent" />
            {chart.insight}
          </p>
        </div>
      )}
    </section>
  )
}
