export type EventType =
  | "node_start"
  | "node_end"
  | "tool_call"
  | "tool_result"
  | "critic_decision"
  | "documents_ready"
  | "plan_ready"
  | "sources_ready"
  | "datasets_ready"
  | "validation_ready"
  | "reasoning_ready"
  | "model_ready"
  | "factcheck_ready"
  | "chart_ready"
  | "report_ready"
  | "error"
  | "done"

export interface AgentEvent {
  type: EventType
  agent: string
  payload: Record<string, unknown>
  timestamp: string
}

export interface PlotlyFigure {
  data?: unknown[]
  layout?: Record<string, unknown>
  config?: Record<string, unknown>
}

export interface ChartSpec {
  template?: string
  title?: string
  insight?: string
  argument_role?: string
  selection_reason?: string
  impact_score?: number
  explanation?: string
  source_titles?: string[]
  caveat?: string
  confidence?: string
  figure?: PlotlyFigure
}

export interface UploadedDocument {
  source_id: string
  name: string
  kind: string
  excerpt: string
}

export interface SemanticScholarSource {
  source_id: string
  paper_id?: string
  provider?: string
  source_type?: string
  title: string
  year?: number
  citation_count?: number
  authors?: string[]
  url?: string
}

export interface DatasetSource {
  source_id: string
  provider?: string
  title: string
  description?: string
  url?: string
  resource_count?: number
  credibility?: number
  latest_year?: number
}
