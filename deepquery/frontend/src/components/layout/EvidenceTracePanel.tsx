import { useEffect, useRef } from "react"
import { ExternalLink, Quote, ShieldCheck } from "lucide-react"
import type { EvidenceItem, EvidenceSelection } from "../../types/events"

interface EvidenceTracePanelProps {
  selection: EvidenceSelection | null
}

function formatPValue(value?: number | null) {
  if (typeof value !== "number") return "p not stated"
  return `p=${value < 0.001 ? "<0.001" : value.toLocaleString(undefined, { maximumFractionDigits: 4 })}`
}

function formatSample(value?: number | null) {
  if (typeof value !== "number") return "n not stated"
  return `n=${value.toLocaleString()}`
}

function EvidenceCard({ evidence }: { evidence: EvidenceItem }) {
  const significant = evidence.significant === true

  return (
    <article className="rounded-lg border border-[#E5E7EB] bg-brand-surface p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] text-brand-muted">
        <span className="rounded-full bg-white px-2 py-0.5 font-semibold text-brand-ink">
          {evidence.value || "value not stated"}
        </span>
        <span>{formatSample(evidence.sampleSize)}</span>
        <span>{formatPValue(evidence.pValue)}</span>
        {typeof evidence.significant === "boolean" && (
          <span className={significant ? "text-emerald-700" : "text-amber-700"}>
            {significant ? "significant" : "not significant"}
          </span>
        )}
      </div>

      <blockquote className="rounded-md border-l-2 border-brand-accent bg-white px-3 py-2 text-sm leading-6 text-brand-ink">
        <Quote size={13} className="mb-1 text-brand-accent" />
        {evidence.sourceQuote || "No exact quote available for this datum."}
      </blockquote>

      <div className="mt-3 text-xs leading-5 text-brand-muted">
        <div className="font-medium text-brand-ink">
          {evidence.paperTitle || "Untitled source"}
        </div>
        <div>
          {[evidence.provider, evidence.year].filter(Boolean).join(" / ")}
        </div>
        {evidence.url && (
          <a
            href={evidence.url}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1 font-semibold text-brand-accent underline decoration-brand-accent/30 underline-offset-4"
          >
            Open source
            <ExternalLink size={12} />
          </a>
        )}
      </div>
    </article>
  )
}

export function EvidenceTracePanel({ selection }: EvidenceTracePanelProps) {
  const panelRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (selection) {
      panelRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" })
    }
  }, [selection])

  return (
    <section
      ref={panelRef}
      className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)]"
    >
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-highlight text-brand-accent">
          <ShieldCheck size={15} />
        </div>
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-brand-ink">Source Peek</h2>
          <p className="truncate text-[11px] text-brand-muted">
            {selection?.label || "Click a chart point"}
          </p>
        </div>
      </div>

      {!selection || selection.evidence.length === 0 ? (
        <div className="rounded-lg border border-[#E5E7EB] bg-brand-surface px-3 py-4 text-sm leading-6 text-brand-muted">
          Select a bar, marker, or point to inspect the exact extracted quote behind it.
        </div>
      ) : (
        <div className="space-y-3">
          <div className="rounded-lg border border-brand-border bg-brand-highlight/45 px-3 py-2 text-xs leading-5 text-brand-muted">
            {selection.chartTitle}
          </div>
          {selection.evidence.slice(0, 4).map((evidence, index) => (
            <EvidenceCard
              key={evidence.id || `${evidence.paperTitle}-${evidence.metric}-${index}`}
              evidence={evidence}
            />
          ))}
        </div>
      )}
    </section>
  )
}
