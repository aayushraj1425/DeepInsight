

import { ResearchSources, type ResearchSource } from "./ResearchSources"

interface ResearchSidebarProps {
  sources: ResearchSource[]
}

export function ResearchSidebar({ sources }: ResearchSidebarProps) {
  return (
    <aside className="min-w-0 space-y-5 xl:sticky xl:top-5 xl:self-start" aria-label="Agent activity">
      <ResearchSources sources={sources} />
    </aside>
  )
}
