import { AgentDAG } from "../AgentDAG"
import { AgentLog } from "../AgentLog"
import type { AgentEvent } from "../../types/events"
import { ResearchSources, type ResearchSource } from "./ResearchSources"

interface ResearchSidebarProps {
  events: AgentEvent[]
  isRunning: boolean
  sources: ResearchSource[]
}

export function ResearchSidebar({ events, isRunning, sources }: ResearchSidebarProps) {
  return (
    <aside className="min-w-0 space-y-5 xl:sticky xl:top-5 xl:self-start" aria-label="Agent activity">
      <AgentDAG events={events} isRunning={isRunning} />
      <ResearchSources sources={sources} />
      <AgentLog events={events} isRunning={isRunning} />
    </aside>
  )
}
