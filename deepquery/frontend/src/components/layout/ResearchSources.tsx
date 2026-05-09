import { useState } from "react"
import { ChevronDown, ExternalLink, FileText } from "lucide-react"

export interface ResearchSource {
  title: string
  provider: string
  url: string
  year?: number
  citationCount?: number
}

interface ResearchSourcesProps {
  sources: ResearchSource[]
}

export function ResearchSources({ sources }: ResearchSourcesProps) {
  const [isOpen, setIsOpen] = useState(true)

  return (
    <section className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)]">
      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 rounded-lg border border-brand-accent/15 bg-brand-highlight/45 px-2 py-1.5 text-left transition-colors hover:border-brand-accent/30 hover:bg-brand-highlight"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-brand-ink">
          <FileText size={16} className="text-brand-accent" />
          Sources
        </span>
        <span className="flex items-center gap-2 text-xs text-brand-muted">
          {sources.length}
          <ChevronDown size={15} className={`transition-transform text-brand-muted ${isOpen ? "rotate-180" : ""}`} />
        </span>
      </button>

      {isOpen && (
        <div className="mt-4 space-y-2">
          {sources.length === 0 ? (
            <div className="rounded-lg border border-[#E5E7EB] bg-brand-surface px-3 py-4 text-sm text-brand-muted">
              No sources fetched yet.
            </div>
          ) : (
            sources.map((source) => (
              <a
                key={`${source.provider}-${source.title}`}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-lg border border-[#E5E7EB] bg-brand-surface p-3 transition-all hover:border-brand-accent/40 hover:bg-brand-highlight/40 hover:-translate-y-0.5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="line-clamp-2 text-sm font-medium leading-5 text-brand-ink">
                      {source.title}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-brand-muted">
                      <span>{source.provider}</span>
                      {source.year && <span>{source.year}</span>}
                      {typeof source.citationCount === "number" && (
                        <span>{source.citationCount.toLocaleString()} citations</span>
                      )}
                    </div>
                  </div>
                  <ExternalLink size={14} className="mt-0.5 shrink-0 text-brand-accent" />
                </div>
              </a>
            ))
          )}
        </div>
      )}
    </section>
  )
}
