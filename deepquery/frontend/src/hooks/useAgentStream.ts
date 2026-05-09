import { useState, useCallback, useRef } from "react"
import type { AgentEvent } from "../types/events"

function getApiBase() {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  const host = window.location.hostname || "127.0.0.1"
  return `${window.location.protocol}//${host}:8000`
}

function makeErrorEvent(message: string): AgentEvent {
  return {
    type: "error",
    agent: "system",
    payload: { message },
    timestamp: new Date().toISOString(),
  }
}

export function useAgentStream() {
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const esRef = useRef<EventSource | null>(null)

  const start = useCallback(async (query: string) => {
    esRef.current?.close()
    setEvents([])
    setIsRunning(true)
    setSessionId(null)

    let id: string
    try {
      const api = getApiBase()
      const res = await fetch(`${api}/api/investigations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      })
      if (!res.ok) throw new Error(`Backend returned ${res.status}`)
      ;({ id } = await res.json())
      if (!id) throw new Error("Backend did not return a session id")

      setSessionId(id)
      const es = new EventSource(`${api}/api/stream/${id}`)
      esRef.current = es

      es.onmessage = (e: MessageEvent) => {
        const event: AgentEvent = JSON.parse(e.data)
        setEvents((prev) => [...prev, event])
        if (event.type === "done" || event.type === "error") {
          es.close()
          setIsRunning(false)
        }
      }

      es.onerror = () => {
        es.close()
        setIsRunning(false)
        setEvents((prev) => {
          if (prev.some((event) => event.type === "error" || event.type === "done")) return prev
          return [...prev, makeErrorEvent("Connection to backend stream closed")]
        })
      }
    } catch {
      setIsRunning(false)
      setEvents([makeErrorEvent("Could not reach backend. Is uvicorn running on port 8000?")])
      return
    }
  }, [])

  const stop = useCallback(() => {
    esRef.current?.close()
    setIsRunning(false)
  }, [])

  return { events, isRunning, sessionId, start, stop }
}
