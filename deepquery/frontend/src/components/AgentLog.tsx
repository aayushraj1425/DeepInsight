import { useEffect, useRef } from "react"
import { ScrollText } from "lucide-react"

import { cn } from "../lib/utils"
import type { AgentEvent } from "../types/events"

const AGENT_COLOR: Record<string, string> = {
  ingestor: "text-indigo-300 border-indigo-800 bg-indigo-950/40",
  orchestrator: "text-violet-400 border-violet-800 bg-violet-950/40",
  discovery: "text-blue-400 border-blue-800 bg-blue-950/40",
  datafinder: "text-teal-300 border-teal-800 bg-teal-950/40",
  validator: "text-lime-300 border-lime-800 bg-lime-950/40",
  extractor: "text-cyan-400 border-cyan-800 bg-cyan-950/40",
  analyst: "text-yellow-400 border-yellow-800 bg-yellow-950/40",
  reasoner: "text-orange-300 border-orange-800 bg-orange-950/40",
  economist: "text-amber-300 border-amber-800 bg-amber-950/40",
  factchecker: "text-red-400 border-red-800 bg-red-950/40",
  visualizer: "text-green-400 border-green-800 bg-green-950/40",
  reporter: "text-pink-400 border-pink-800 bg-pink-950/40",
  system: "text-gray-400 border-gray-700 bg-gray-900/40",
}

const EVENT_ICON: Record<string, string> = {
  node_start: ">",
  node_end: "=",
  tool_call: "*",
  tool_result: "+",
  critic_decision: "!",
  documents_ready: "D",
  plan_ready: "P",
  sources_ready: "S",
  datasets_ready: "T",
  validation_ready: "V",
  reasoning_ready: "I",
  model_ready: "M",
  factcheck_ready: "F",
  chart_ready: "C",
  report_ready: "R",
  error: "x",
  done: "~",
}

function eventMessage(event: AgentEvent) {
  if (typeof event.payload.message === "string") {
    return event.payload.message
  }
  return JSON.stringify(event.payload)
}

function EventRow({ event, index }: { event: AgentEvent; index: number }) {
  const colors = AGENT_COLOR[event.agent] ?? AGENT_COLOR.system
  const icon = EVENT_ICON[event.type] ?? "."

  return (
    <div
      className={cn(
        "animate-slide-in flex items-start gap-3 rounded-lg border px-4 py-2.5 font-mono text-xs",
        colors
      )}
      style={{ animationDelay: `${index * 20}ms` }}
    >
      <span className="mt-px w-3 shrink-0 text-center opacity-60">{icon}</span>
      <span className="w-20 shrink-0 font-semibold capitalize">{event.agent}</span>
      <span className="w-28 shrink-0 opacity-50">{event.type}</span>
      <span className="truncate opacity-80">{eventMessage(event)}</span>
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
      <div className="max-h-[60vh] space-y-1.5 overflow-y-auto pr-1">
        {events.length === 0 && !isRunning && (
          <div className="rounded-lg border border-gray-800 bg-gray-950/50 px-4 py-6 text-sm text-gray-500">
            Waiting for a run.
          </div>
        )}
        {events.map((event, index) => (
          <EventRow key={`${event.timestamp}-${index}`} event={event} index={index} />
        ))}
        {isRunning && (
          <div className="flex items-center gap-2 px-4 py-2 font-mono text-xs text-gray-500">
            <span className="flex gap-1">
              {[0, 1, 2].map((index) => (
                <span
                  key={index}
                  className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-gray-500"
                  style={{ animationDelay: `${index * 160}ms` }}
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
