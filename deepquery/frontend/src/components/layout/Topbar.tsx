import { RotateCcw, Sparkles } from "lucide-react"

interface TopbarProps {
  onReset: () => void
  canReset: boolean
  status: string
}

export function Topbar({ onReset, canReset, status }: TopbarProps) {
  return (
    <header className="sticky top-0 z-40 h-14 border-b border-slate-800 bg-[#0b0d10]/95 backdrop-blur">
      <div className="flex h-full items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-cyan-400 text-[11px] font-extrabold text-slate-950">
              DQ
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold leading-4 tracking-tight">DeepQuery</div>
              <div className="truncate text-[11px] leading-4 text-slate-500">{status}</div>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            className="flex h-8 items-center gap-2 rounded-md border border-cyan-500/30 bg-cyan-500/10 px-3 text-xs font-medium text-cyan-100"
            title="Live research"
            type="button"
            disabled
          >
            <Sparkles size={14} />
            <span className="hidden sm:inline">Live research</span>
          </button>
          <button
            className="flex h-8 items-center gap-2 rounded-md border border-slate-800 px-3 text-xs font-medium text-slate-300 transition-colors hover:border-cyan-500/50 hover:text-cyan-200 disabled:cursor-not-allowed disabled:opacity-50"
            title="Reset workspace"
            type="button"
            onClick={onReset}
            disabled={!canReset}
          >
            <RotateCcw size={14} />
            <span className="hidden sm:inline">Reset</span>
          </button>
        </div>
      </div>
    </header>
  )
}
