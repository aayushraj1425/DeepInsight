import { ArrowLeft, Download, Share2 } from "lucide-react"

export function Topbar() {
  return (
    <header className="sticky top-0 z-40 h-14 border-b border-slate-800 bg-[#0b0d10]/95 backdrop-blur">
      <div className="flex h-full items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <button
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-slate-800 text-slate-400 transition-colors hover:border-cyan-500/50 hover:text-cyan-200"
            aria-label="Go back"
            title="Go back"
            type="button"
          >
            <ArrowLeft size={16} />
          </button>

          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-cyan-400 text-[11px] font-extrabold text-slate-950">
              DQ
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold leading-4 tracking-tight">DeepQuery</div>
              <div className="truncate text-[11px] leading-4 text-slate-500">Research workspace</div>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            className="flex h-8 items-center gap-2 rounded-md border border-slate-800 px-3 text-xs font-medium text-slate-300 transition-colors hover:border-cyan-500/50 hover:text-cyan-200"
            title="Download"
            type="button"
          >
            <Download size={14} />
            <span className="hidden sm:inline">Download</span>
          </button>
          <button
            className="flex h-8 items-center gap-2 rounded-md border border-slate-800 px-3 text-xs font-medium text-slate-300 transition-colors hover:border-cyan-500/50 hover:text-cyan-200"
            title="Share"
            type="button"
          >
            <Share2 size={14} />
            <span className="hidden sm:inline">Share</span>
          </button>
        </div>
      </div>
    </header>
  )
}
