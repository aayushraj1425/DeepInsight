export type EventType =
  | "node_start"
  | "node_end"
  | "tool_call"
  | "tool_result"
  | "critic_decision"
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
  figure?: PlotlyFigure
}
