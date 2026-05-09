import { ArrowLeft, Download, Share2 } from "lucide-react"

interface TopbarProps {
  onBack?: () => void
}

export function Topbar({ onBack }: TopbarProps) {
  return (
    <header className="sticky top-0 z-40 h-14 border-b border-[#E5E7EB] bg-brand-background/95 backdrop-blur">
      <div className="flex h-full items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <button
            onClick={onBack}
            disabled={!onBack}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[#E5E7EB] text-brand-muted transition-colors hover:border-brand-accent/50 hover:text-brand-accent disabled:opacity-30 disabled:cursor-default"
            aria-label="Go back"
            title="Go back"
            type="button"
          >
            <ArrowLeft size={16} />
          </button>

          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-brand-accent text-[11px] font-extrabold text-white">
              DQ
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold leading-4 tracking-tight text-brand-ink">DeepQuery</div>
              <div className="truncate text-[11px] leading-4 text-brand-muted">Research workspace</div>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            className="flex h-8 items-center gap-2 rounded-md border border-[#E5E7EB] px-3 text-xs font-medium text-brand-muted transition-colors hover:border-brand-accent/50 hover:text-brand-accent"
            title="Download"
            type="button"
          >
            <Download size={14} />
            <span className="hidden sm:inline">Download</span>
          </button>
          <button
            className="flex h-8 items-center gap-2 rounded-md border border-[#E5E7EB] px-3 text-xs font-medium text-brand-muted transition-colors hover:border-brand-accent/50 hover:text-brand-accent"
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
