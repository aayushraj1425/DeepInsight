export type EventType =
  | "node_start"
  | "node_end"
  | "tool_call"
  | "tool_result"
  | "critic_decision"
  | "sources_ready"
  | "synthesis_ready"
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

export interface EvidenceItem {
  id?: string
  metric?: string
  value?: string | number
  sampleSize?: number | null
  ci?: string | null
  pValue?: number | null
  significant?: boolean | null
  intervention?: string
  sourceQuote?: string
  paperTitle?: string
  paperId?: string
  year?: string | number | null
  url?: string
  provider?: string
  groupLabel?: string
}

export interface EvidenceSelection {
  chartTitle?: string
  label?: string
  evidence: EvidenceItem[]
}

export interface ChartDatumMeta {
  label?: string
  value?: number
  sampleSize?: number | null
  pValue?: number | null
  significant?: boolean | null
  significantCount?: number
  evidenceCount?: number
  evidence?: EvidenceItem[]
}

export interface ChartSpec {
  template?: string
  title?: string
  insight?: string
  figure?: PlotlyFigure
}

export interface SynthesisSummary {
  answer: string
  confidence?: "high" | "moderate" | "low" | string
  mostReliableResult?: string
  mainLimitation?: string
  evidenceCount?: number
  studiesCount?: number
}
