import { AgentDAG } from "../AgentDAG"
import { AgentLog } from "../AgentLog"
import type { AgentEvent } from "../../types/events"
import {
  ResearchSources,
  type DatasetCard,
  type ResearchSource,
  type UploadedDocumentCard,
} from "./ResearchSources"

interface ResearchSidebarProps {
  events: AgentEvent[]
  isRunning: boolean
  sources: ResearchSource[]
  documents: UploadedDocumentCard[]
  datasets: DatasetCard[]
}

export function ResearchSidebar({ events, isRunning, sources, documents, datasets }: ResearchSidebarProps) {
  return (
    <aside className="min-w-0 space-y-5 xl:sticky xl:top-5 xl:self-start" aria-label="Agent activity">
      <AgentDAG events={events} isRunning={isRunning} />
      <ResearchSources sources={sources} documents={documents} datasets={datasets} />
      <AgentLog events={events} isRunning={isRunning} />
    </aside>
  )
}
