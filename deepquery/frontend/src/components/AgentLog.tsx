import { useEffect, useRef } from "react"
import { ScrollText } from "lucide-react"
import type { AgentEvent } from "../types/events"
import { cn } from "../lib/utils"

const AGENT_COLOR: Record<string, string> = {
  planner:    "text-violet-400 border-violet-800 bg-violet-950/40",
  discovery:  "text-blue-400   border-blue-800   bg-blue-950/40",
  extractor:  "text-cyan-400   border-cyan-800   bg-cyan-950/40",
  analyst:    "text-yellow-400 border-yellow-800 bg-yellow-950/40",
  critic:     "text-red-400    border-red-800    bg-red-950/40",
  visualizer: "text-green-400  border-green-800  bg-green-950/40",
  reporter:   "text-pink-400   border-pink-800   bg-pink-950/40",
  system:     "text-gray-400   border-gray-700   bg-gray-900/40",
}

const EVENT_ICON: Record<string, string> = {
  node_start:      "▶",
  node_end:        "■",
  tool_call:       "⚙",
  tool_result:     "✓",
  critic_decision: "⚖",
  chart_ready:     "◈",
  report_ready:    "≡",
  error:           "✗",
  done:            "✦",
}

function EventRow({ event, index }: { event: AgentEvent; index: number }) {
  const colors = AGENT_COLOR[event.agent] ?? AGENT_COLOR.system
  const icon = EVENT_ICON[event.type] ?? "·"
  const msg = typeof event.payload.message === "string"
    ? event.payload.message
    : JSON.stringify(event.payload)

  return (
    <div
      className={cn(
        "animate-slide-in flex items-start gap-3 px-4 py-2.5 rounded-lg border font-mono text-xs",
        colors
      )}
      style={{ animationDelay: `${index * 20}ms` }}
    >
      <span className="opacity-60 mt-px w-3 shrink-0 text-center">{icon}</span>
      <span className="font-semibold w-20 shrink-0 capitalize">{event.agent}</span>
      <span className="opacity-50 w-28 shrink-0">{event.type}</span>
      <span className="opacity-80 truncate">{msg}</span>
    </div>
  )
}

export function AgentLog({ events, isRunning }: { events: AgentEvent[]; isRunning: boolean }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events.length])

  return (
    <section className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-100">
        <ScrollText size={16} className="text-gray-400" />
        Event stream
      </div>
      <div className="space-y-1.5 max-h-[60vh] overflow-y-auto pr-1">
        {events.length === 0 && !isRunning && (
          <div className="rounded-lg border border-gray-800 bg-gray-950/50 px-4 py-6 text-sm text-gray-500">
            Waiting for a run.
          </div>
        )}
        {events.map((e, i) => <EventRow key={`${e.timestamp}-${i}`} event={e} index={i} />)}
        {isRunning && (
          <div className="flex items-center gap-2 px-4 py-2 text-xs text-gray-500 font-mono">
            <span className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-pulse-dot"
                  style={{ animationDelay: `${i * 160}ms` }}
                />
              ))}
            </span>
            agents working...
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </section>
  )
}
