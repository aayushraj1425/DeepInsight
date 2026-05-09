import { useState } from "react"
import { Play, Search, Square } from "lucide-react"
import { cn } from "../lib/utils"

interface Props {
  onSubmit: (query: string) => void
  onStop: () => void
  disabled: boolean
}

const EXAMPLE_QUERIES = [
  {
    label: "Sleep deprivation",
    query: "What is the effect of sleep deprivation on cognitive performance?",
  },
  {
    label: "Minimum wage effects",
    query: "What are the economic effects of minimum wage increases?",
  },
]

export function QueryInput({ onSubmit, onStop, disabled }: Props) {
  const [query, setQuery] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (query.trim()) onSubmit(query.trim())
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What is the effect of sleep deprivation on cognitive performance?"
          disabled={disabled}
          className={cn(
            "min-w-0 flex-1 rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 text-gray-100",
            "placeholder:text-gray-500 focus:outline-none focus:border-blue-500",
            "disabled:opacity-60 transition-colors text-sm"
          )}
        />
        {disabled ? (
          <button
            type="button"
            onClick={onStop}
            className="flex items-center justify-center gap-2 rounded-lg bg-red-600 px-5 py-3 text-sm font-medium transition-colors hover:bg-red-500"
          >
            <Square size={14} />
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={!query.trim()}
            className={cn(
              "flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-medium transition-colors",
              "bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            <Search size={14} />
            Research
          </button>
        )}
      </form>

      <div className="flex flex-wrap gap-2">
        {EXAMPLE_QUERIES.map((example) => (
          <button
            key={example.query}
            type="button"
            disabled={disabled}
            onClick={() => {
              setQuery(example.query)
              onSubmit(example.query)
            }}
            title={example.query}
            className={cn(
              "inline-flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 px-3 py-2 text-xs text-gray-300",
              "transition-colors hover:border-blue-700 hover:text-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
            )}
          >
            <Play size={12} />
            {example.label}
          </button>
        ))}
      </div>
    </div>
  )
}
