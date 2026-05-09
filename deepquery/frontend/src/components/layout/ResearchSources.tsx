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
    <section className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 text-left"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-gray-100">
          <FileText size={16} className="text-cyan-300" />
          Sources
        </span>
        <span className="flex items-center gap-2 text-xs text-gray-500">
          {sources.length}
          <ChevronDown size={15} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
        </span>
      </button>

      {isOpen && (
        <div className="mt-4 space-y-2">
          {sources.length === 0 ? (
            <div className="rounded-md border border-gray-800 bg-gray-950/50 px-3 py-4 text-sm text-gray-500">
              No sources fetched yet.
            </div>
          ) : (
            sources.map((source) => (
              <a
                key={`${source.provider}-${source.title}`}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-md border border-gray-800 bg-gray-950/50 p-3 transition-colors hover:border-cyan-500/40 hover:bg-cyan-500/5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="line-clamp-2 text-sm font-medium leading-5 text-gray-100">
                      {source.title}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-gray-500">
                      <span>{source.provider}</span>
                      {source.year && <span>{source.year}</span>}
                      {typeof source.citationCount === "number" && (
                        <span>{source.citationCount.toLocaleString()} citations</span>
                      )}
                    </div>
                  </div>
                  <ExternalLink size={14} className="mt-0.5 shrink-0 text-gray-500" />
                </div>
              </a>
            ))
          )}
        </div>
      )}
    </section>
  )
}
