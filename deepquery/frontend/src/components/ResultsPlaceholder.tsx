import { BarChart3, FileText } from "lucide-react"

export function ResultsPlaceholder({ isRunning }: { isRunning: boolean }) {
  return (
    <section className="rounded-lg border border-dashed border-gray-800 bg-gray-900/30 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-gray-800 text-gray-400">
          {isRunning ? <BarChart3 size={20} /> : <FileText size={20} />}
        </div>
        <div>
          <h2 className="text-sm font-semibold text-gray-100">
            {isRunning ? "Results will appear here" : "No investigation yet"}
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">
            {isRunning
              ? "Charts and the final markdown report are streamed into this workspace after the critic approves the analysis or retry budget is reached."
              : "Start with one of the prepared research questions or enter your own query."}
          </p>
        </div>
      </div>
    </section>
  )
}
