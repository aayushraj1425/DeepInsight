import { useEffect, useRef } from "react"
import * as d3 from "d3"
import { BarChart3 } from "lucide-react"
import { cn } from "../lib/utils"
import type { ChartSpec } from "../types/events"

export type { ChartSpec, PlotlyFigure } from "../types/events"

interface Props {
  chart: ChartSpec
  className?: string
}

export function ChartCard({ chart, className }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current || !chart.figure?.data || chart.figure.data.length === 0) return

    const container = containerRef.current
    const dataObj = chart.figure.data[0] as any
    const type = dataObj.type

    const margin = { top: 20, right: 30, bottom: 40, left: 40 }
    const width = container.clientWidth - margin.left - margin.right
    const height = container.clientHeight - margin.top - margin.bottom

    d3.select(container).selectAll("*").remove()

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

    if (type === "bar") {
      const data = dataObj.x.map((xVal: string, i: number) => ({
        x: xVal,
        y: dataObj.y[i],
        color: Array.isArray(dataObj.marker?.color)
          ? dataObj.marker.color[i]
          : dataObj.marker?.color || "#E25A3D",
      }))

      const x = d3.scaleBand().domain(data.map((d: any) => d.x)).range([0, width]).padding(0.3)
      const y = d3.scaleLinear().domain([Math.min(0, d3.min(data, (d: any) => Number(d.y)) ?? 0), d3.max(data, (d: any) => Number(d.y)) ?? 0]).nice().range([height, 0])

      svg.append("g")
        .attr("class", "grid")
        .call(d3.axisLeft(y).tickSize(-width).tickFormat(() => ""))
        .selectAll("line")
        .attr("stroke", "#E5E7EB")
        .attr("stroke-dasharray", "3,3")

      svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(0))
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

      const defs = svg.append("defs")
      data.forEach((d: any, i: number) => {
        const gradient = defs.append("linearGradient")
          .attr("id", `gradient-bar-${i}`)
          .attr("x1", "0%").attr("x2", "0%")
          .attr("y1", "100%").attr("y2", "0%")
        gradient.append("stop").attr("offset", "0%").attr("stop-color", "#FFEDD5").attr("stop-opacity", 1)
        gradient.append("stop").attr("offset", "100%").attr("stop-color", "#E25A3D").attr("stop-opacity", 1)
      })

      svg.selectAll(".bar")
        .data(data)
        .enter()
        .append("path")
        .attr("class", "bar")
        .attr("fill", (_d: any, i: number) => `url(#gradient-bar-${i})`)
        .attr("d", (d: any) => {
          const zero = y(0)
          const barY = Math.min(y(d.y), zero)
          const barHeight = Math.abs(y(d.y) - zero)
          const r = 4
          const xVal = x(d.x)!
          const w = x.bandwidth()
          if (d.y >= 0) {
            return `M${xVal},${barY+barHeight} L${xVal},${barY+r} Q${xVal},${barY} ${xVal+r},${barY} L${xVal+w-r},${barY} Q${xVal+w},${barY} ${xVal+w},${barY+r} L${xVal+w},${barY+barHeight} Z`
          } else {
            return `M${xVal},${zero} L${xVal},${barY+barHeight-r} Q${xVal},${barY+barHeight} ${xVal+r},${barY+barHeight} L${xVal+w-r},${barY+barHeight} Q${xVal+w},${barY+barHeight} ${xVal+w},${barY+barHeight-r} L${xVal+w},${zero} Z`
          }
        })
        .style("opacity", 0)
        .on("mouseover", function (event, d: any) {
          tooltip.html(`<b>${d.x}</b><br/>Value: ${d.y}`)
                 .style("left", `${event.pageX + 10}px`)
                 .style("top", `${event.pageY - 28}px`)
                 .classed("hidden", false)
          d3.select(this).style("filter", "drop-shadow(0 4px 12px rgba(226,90,61,0.3))")
        })
        .on("mouseout", function () {
          tooltip.classed("hidden", true)
          d3.select(this).style("filter", "none")
        })
        .transition()
        .duration(800)
        .delay((_, i) => i * 100)
        .style("opacity", 1)

    } else if (type === "scatter") {
      const data = dataObj.x.map((xVal: number, i: number) => ({
        x: xVal,
        y: dataObj.y[i]
      }))
      const color = "#E25A3D"

      const x = d3.scaleLinear().domain((d3.extent(data, (d: any) => d.x) as unknown) as [number, number]).range([0, width])
      x.domain([x.domain()[0], x.domain()[1] + 1])

      const y = d3.scaleLinear().domain([Math.min(0, d3.min(data, (d: any) => Number(d.y)) ?? 0), d3.max(data, (d: any) => Number(d.y)) ?? 0]).nice().range([height, 0])

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

      const line = d3.line<any>()
        .x(d => x(d.x))
        .y(d => y(d.y))
        .curve(d3.curveMonotoneX)

      const area = d3.area<any>()
        .x(d => x(d.x))
        .y0(y(Math.min(0, d3.min(data, (d: any) => Number(d.y)) ?? 0)))
        .y1(d => y(d.y))
        .curve(d3.curveMonotoneX)

      const defs = svg.append("defs")
      const gradient = defs.append("linearGradient")
        .attr("id", "area-gradient")
        .attr("x1", "0%").attr("y1", "0%")
        .attr("x2", "0%").attr("y2", "100%")
      gradient.append("stop").attr("offset", "0%").attr("stop-color", color).attr("stop-opacity", 0.2)
      gradient.append("stop").attr("offset", "100%").attr("stop-color", color).attr("stop-opacity", 0)

      svg.append("path")
        .datum(data)
        .attr("fill", "url(#area-gradient)")
        .attr("d", area)
        .style("opacity", 0)
        .transition().duration(1000).style("opacity", 1)

      const path = svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2.5)
        .attr("d", line)

      const totalLength = (path.node() as SVGPathElement).getTotalLength()
      path
        .attr("stroke-dasharray", totalLength + " " + totalLength)
        .attr("stroke-dashoffset", totalLength)
        .transition().duration(1500).ease(d3.easeLinear).attr("stroke-dashoffset", 0)

      svg.selectAll(".dot")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", (d: any) => x(d.x))
        .attr("cy", (d: any) => y(d.y))
        .attr("r", 5)
        .attr("fill", "#FFFFFF")
        .attr("stroke", color)
        .attr("stroke-width", 2)
        .on("mouseover", function (event, d: any) {
          tooltip.html(`<b>${d.x}</b><br/>Value: ${d.y}`)
                 .style("left", `${event.pageX + 10}px`)
                 .style("top", `${event.pageY - 28}px`)
                 .classed("hidden", false)
          d3.select(this).transition().duration(200).attr("r", 7).attr("fill", color)
        })
        .on("mouseout", function () {
          tooltip.classed("hidden", true)
          d3.select(this).transition().duration(200).attr("r", 5).attr("fill", "#FFFFFF")
        })
        .style("opacity", 0)
        .transition().delay((_, i) => 1500 + i * 100).duration(500).style("opacity", 1)
    }

    return () => {
      d3.selectAll(".absolute.hidden.rounded-md").remove()
    }
  }, [chart])

  return (
    <section className={cn("animate-slide-in rounded-xl border border-[#E5E7EB] bg-white p-5 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.06)] transition-all duration-200 hover:shadow-[0_15px_30px_-10px_rgba(0,0,0,0.1)] hover:-translate-y-0.5", className)}>
      <div className="mb-4 flex items-center gap-3 text-sm font-medium text-brand-ink">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-highlight text-brand-accent">
          <BarChart3 size={16} />
        </div>
        <span className="truncate font-serif text-base font-bold text-brand-ink">{chart.title ?? "Chart"}</span>
      </div>
      <div
        ref={containerRef}
        className="relative h-[420px] w-full min-w-0 bg-brand-surface rounded-lg"
      />
      {chart.insight && (
        <div className="mt-4 pt-4 border-t border-[#E5E7EB]">
          <p className="text-sm leading-relaxed text-brand-muted font-light flex items-start gap-2">
            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-brand-accent shrink-0" />
            {chart.insight}
          </p>
        </div>
      )}
    </section>
  )
}
