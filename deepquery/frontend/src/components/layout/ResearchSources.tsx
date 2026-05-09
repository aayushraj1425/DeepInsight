import { useState, type ReactNode } from "react"
import { ChevronDown, Database, ExternalLink, FileText, FolderOpen } from "lucide-react"

export interface ResearchSource {
  source_id: string
  title: string
  provider: string
  url?: string
  year?: number
  citationCount?: number
  authors?: string[]
}

export interface UploadedDocumentCard {
  source_id: string
  name: string
  kind: string
  excerpt: string
}

export interface DatasetCard {
  source_id: string
  title: string
  provider: string
  description?: string
  url?: string
  resourceCount?: number
  credibility?: number
  latestYear?: number
}

interface ResearchSourcesProps {
  documents: UploadedDocumentCard[]
  sources: ResearchSource[]
  datasets: DatasetCard[]
}

function SectionHeader({
  icon,
  label,
  count,
  isOpen,
  onToggle,
}: {
  icon: ReactNode
  label: string
  count: number
  isOpen: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex w-full items-center justify-between gap-3 text-left"
      aria-expanded={isOpen}
    >
      <span className="flex items-center gap-2 text-sm font-semibold text-gray-100">
        {icon}
        {label}
      </span>
      <span className="flex items-center gap-2 text-xs text-gray-500">
        {count}
        <ChevronDown size={15} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </span>
    </button>
  )
}

export function ResearchSources({ documents, sources, datasets }: ResearchSourcesProps) {
  const [documentsOpen, setDocumentsOpen] = useState(true)
  const [sourcesOpen, setSourcesOpen] = useState(true)
  const [datasetsOpen, setDatasetsOpen] = useState(true)

  return (
    <section className="space-y-4 rounded-lg border border-gray-800 bg-gray-900/50 p-4">
      <div className="text-sm font-semibold text-gray-100">Evidence</div>

      <div className="space-y-3">
        <SectionHeader
          icon={<FolderOpen size={16} className="text-indigo-300" />}
          label="Uploaded files"
          count={documents.length}
          isOpen={documentsOpen}
          onToggle={() => setDocumentsOpen((value) => !value)}
        />
        {documentsOpen && (
          <div className="space-y-2">
            {documents.length === 0 ? (
              <div className="rounded-md border border-gray-800 bg-gray-950/50 px-3 py-4 text-sm text-gray-500">
                No uploaded files yet.
              </div>
            ) : (
              documents.map((document) => (
                <div
                  key={document.source_id}
                  className="rounded-md border border-gray-800 bg-gray-950/50 p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="line-clamp-2 text-sm font-medium leading-5 text-gray-100">{document.name}</div>
                      <div className="mt-1 text-[11px] uppercase tracking-wide text-gray-500">{document.kind}</div>
                      <div className="mt-2 text-xs leading-5 text-gray-400">{document.excerpt}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <SectionHeader
          icon={<FileText size={16} className="text-cyan-300" />}
          label="Research papers"
          count={sources.length}
          isOpen={sourcesOpen}
          onToggle={() => setSourcesOpen((value) => !value)}
        />
        {sourcesOpen && (
          <div className="space-y-2">
            {sources.length === 0 ? (
              <div className="rounded-md border border-gray-800 bg-gray-950/50 px-3 py-4 text-sm text-gray-500">
                No papers fetched yet.
              </div>
            ) : (
              sources.map((source) => (
                <a
                  key={source.source_id}
                  href={source.url ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-md border border-gray-800 bg-gray-950/50 p-3 transition-colors hover:border-cyan-500/40 hover:bg-cyan-500/5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="line-clamp-2 text-sm font-medium leading-5 text-gray-100">{source.title}</div>
                      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-gray-500">
                        <span>{source.provider}</span>
                        {source.year && <span>{source.year}</span>}
                        {typeof source.citationCount === "number" && (
                          <span>{source.citationCount.toLocaleString()} citations</span>
                        )}
                      </div>
                      {source.authors && source.authors.length > 0 && (
                        <div className="mt-2 text-xs leading-5 text-gray-400">{source.authors.join(", ")}</div>
                      )}
                    </div>
                    <ExternalLink size={14} className="mt-0.5 shrink-0 text-gray-500" />
                  </div>
                </a>
              ))
            )}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <SectionHeader
          icon={<Database size={16} className="text-teal-300" />}
          label="Public datasets"
          count={datasets.length}
          isOpen={datasetsOpen}
          onToggle={() => setDatasetsOpen((value) => !value)}
        />
        {datasetsOpen && (
          <div className="space-y-2">
            {datasets.length === 0 ? (
              <div className="rounded-md border border-gray-800 bg-gray-950/50 px-3 py-4 text-sm text-gray-500">
                No public datasets found yet.
              </div>
            ) : (
              datasets.map((dataset) => (
                <a
                  key={dataset.source_id}
                  href={dataset.url ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-md border border-gray-800 bg-gray-950/50 p-3 transition-colors hover:border-teal-500/40 hover:bg-teal-500/5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="line-clamp-2 text-sm font-medium leading-5 text-gray-100">{dataset.title}</div>
                      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-gray-500">
                        <span>{dataset.provider}</span>
                        {typeof dataset.resourceCount === "number" && (
                          <span>{dataset.resourceCount.toLocaleString()} resources</span>
                        )}
                        {typeof dataset.credibility === "number" && <span>{dataset.credibility.toFixed(2)} credibility</span>}
                        {dataset.latestYear && <span>latest {dataset.latestYear}</span>}
                      </div>
                      {dataset.description && (
                        <div className="mt-2 line-clamp-3 text-xs leading-5 text-gray-400">{dataset.description}</div>
                      )}
                    </div>
                    <ExternalLink size={14} className="mt-0.5 shrink-0 text-gray-500" />
                  </div>
                </a>
              ))
            )}
          </div>
        )}
      </div>
    </section>
  )
}
