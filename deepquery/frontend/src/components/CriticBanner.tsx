import { AlertTriangle, RotateCcw } from "lucide-react"
import type { AgentEvent } from "../types/events"

interface Props {
  event: AgentEvent | null
}

function text(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value : fallback
}

function number(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null
}

export function CriticBanner({ event }: Props) {
  if (!event || event.payload.decision !== "reject") return null

  const feedback = text(event.payload.feedback, text(event.payload.reasoning, "Analysis needs another pass."))
  const retryCount = number(event.payload.retry_count) ?? number(event.payload.retries_used) ?? 0
  const maxRetries = number(event.payload.max_retries) ?? 2

  return (
    <div className="mt-5 animate-slide-in rounded-lg border border-red-800 bg-red-950/60 p-4 shadow-lg shadow-red-950/20">
      <div className="flex items-start gap-3">
        <AlertTriangle size={18} className="mt-0.5 shrink-0 text-red-300" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-red-100">
            Critic rejected analyst output
            <span className="inline-flex items-center gap-1 rounded bg-red-900/80 px-2 py-0.5 text-xs text-red-100">
              <RotateCcw size={12} />
              retry {Math.min(retryCount, maxRetries)}/{maxRetries}
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-red-100/90">{feedback}</p>
        </div>
      </div>
    </div>
  )
}
