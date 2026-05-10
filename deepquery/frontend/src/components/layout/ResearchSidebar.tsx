import type { EvidenceSelection } from "../../types/events"
import { EvidenceTracePanel } from "./EvidenceTracePanel"
import { ResearchSources, type ResearchSource } from "./ResearchSources"

interface ResearchSidebarProps {
  sources: ResearchSource[]
  selectedEvidence: EvidenceSelection | null
}

export function ResearchSidebar({ sources, selectedEvidence }: ResearchSidebarProps) {
  return (
    <aside className="min-w-0 space-y-5 xl:sticky xl:top-5 xl:self-start" aria-label="Agent activity">
      <EvidenceTracePanel selection={selectedEvidence} />
      <ResearchSources sources={sources} />
    </aside>
  )
}
