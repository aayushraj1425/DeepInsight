const NODES = [
  {
    id: "planner",
    label: "Planner",
    description: "Rewrites vague queries into precise academic + web subqueries",
    ambiguity: "Expands keywords; reframes non-academic topics toward empirical angles",
  },
  {
    id: "discovery",
    label: "Discovery",
    description: "Searches Semantic Scholar; falls back to web if rate-limited or empty",
    ambiguity: "Silent failover to DuckDuckGo + full page fetch on 429 or 0 results",
  },
  {
    id: "extractor",
    label: "Extractor",
    description: "Fetches full paper text; parses out explicit numbers verbatim",
    ambiguity: "Returns empty list rather than inventing; substring-validates every quote",
  },
  {
    id: "analyst",
    label: "Analyst",
    description: "Runs aggregate / compare / correlate on validated findings",
    ambiguity: "Skips analysis tools that don't fit the data; accepts critic feedback on retry",
  },
  {
    id: "critic",
    label: "Critic",
    description: "Rejects hallucinated quotes; approves sparse-but-honest results",
    ambiguity: "Sends specific feedback to Analyst; approves after 2 retries to avoid loops",
  },
  {
    id: "reporter",
    label: "Reporter",
    description: "Writes from findings + paper abstracts; never invents numbers",
    ambiguity: "Synthesizes qualitative context when quantitative evidence is thin",
  },
]

export function PipelineDiagram() {
  return (
    <div className="w-full max-w-4xl px-0 sm:px-4">
      <p className="mb-4 text-center text-[11px] font-semibold uppercase tracking-widest text-brand-muted/50 md:mb-6">
        How it works
      </p>

      <div className="space-y-2 md:hidden">
        {NODES.map((node, i) => (
          <div key={node.id} className="relative pl-6">
            {i < NODES.length - 1 && (
              <span className="absolute left-[7px] top-6 h-[calc(100%+0.5rem)] w-px bg-brand-border" />
            )}
            <span className="absolute left-0 top-3 h-3.5 w-3.5 rounded-full border border-brand-accent/35 bg-brand-highlight" />
            <div className="rounded-lg border border-[#E5E7EB] bg-white px-3 py-2.5 shadow-sm">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-brand-accent">
                {node.label}
              </div>
              <p className="mt-1 text-xs leading-snug text-brand-muted">
                {node.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="hidden md:block">
        {/* Node row */}
        <div className="relative flex items-start justify-between gap-0">
          {NODES.map((node, i) => (
            <div key={node.id} className="relative flex flex-1 flex-col items-center">
              {/* Connector line (not after last) */}
              {i < NODES.length - 1 && (
                <div className="absolute top-[18px] left-[calc(50%+20px)] right-0 z-0 h-px bg-gradient-to-r from-brand-accent/40 to-brand-accent/10" />
              )}

              {/* Node pill */}
              <div className="relative z-10 flex flex-col items-center gap-2">
                <div className="whitespace-nowrap rounded-full border border-brand-accent/30 bg-brand-highlight/70 px-3 py-1 text-[11px] font-semibold text-brand-accent shadow-sm">
                  {node.label}
                </div>
                <p className="max-w-[90px] text-center text-[10px] leading-snug text-brand-muted/70">
                  {node.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Retry loop annotation — spans Analyst ↔ Critic */}
        <div className="relative mt-2 flex justify-center">
          {/* Position the loop under Analyst and Critic (nodes 3 & 4, 0-indexed) */}
          <div
            className="flex flex-col items-center"
            style={{ marginLeft: `calc(${(3 / NODES.length) * 100}% - 12px)`, width: `calc(${(2 / NODES.length) * 100}% + 24px)` }}
          >
            {/* Top border of loop */}
            <div className="flex w-full items-center">
              <div className="flex-1 border-t border-dashed border-brand-accent/40" />
              <svg width="10" height="8" viewBox="0 0 10 8" className="shrink-0 text-brand-accent/60">
                <path d="M0 4 L10 4 M6 1 L10 4 L6 7" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="mt-0.5 whitespace-nowrap rounded border border-brand-accent/20 bg-brand-highlight/50 px-2 py-0.5 text-[9px] font-medium text-brand-accent/80">
              reject → feedback → retry (max 2×)
            </div>
          </div>
        </div>

        {/* Ambiguity / failure handling row */}
        <div className="mt-6 flex justify-between gap-1">
          {NODES.map((node) => (
            <div
              key={`${node.id}-ambiguity`}
              className="flex-1 rounded-lg border border-[#E5E7EB] bg-white px-2 py-2 text-[9px] leading-snug text-brand-muted/80"
            >
              <span className="mb-0.5 block text-[9px] font-semibold uppercase tracking-wide text-brand-ink/60">
                on failure
              </span>
              {node.ambiguity}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
