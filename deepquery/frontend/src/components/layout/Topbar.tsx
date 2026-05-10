import { Home, Download, Share2, Check } from "lucide-react"
import { useState } from "react"
import logo from "../../assets/logo.png"

interface TopbarProps {
  onHome: () => void
  onDownload?: () => void
  onShare?: () => void
  showActions?: boolean
}

export function Topbar({ onHome, onDownload, onShare, showActions }: TopbarProps) {
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    await onShare?.()
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <header className="sticky top-0 z-40 h-14 border-b border-[#E5E7EB] bg-brand-background/95 backdrop-blur">
      <div className="flex h-full items-center justify-between gap-3 px-4 sm:px-6">

        {/* Logo — always clickable as Home */}
        <button
          onClick={onHome}
          className="group flex min-w-0 items-center gap-3 rounded-lg bg-brand-highlight/50 px-2 py-1 transition-colors hover:bg-brand-highlight"
          type="button"
          aria-label="Home"
        >
          <img
            src={logo}
            alt="DeepQuery"
            className="h-9 w-9 shrink-0 rounded-lg object-contain transition-transform group-hover:scale-105"
          />
          <div className="min-w-0 text-left">
            <div className="truncate text-sm font-semibold leading-4 tracking-tight text-brand-ink group-hover:text-brand-accent transition-colors">
              DeepQuery
            </div>
            <div className="truncate text-[11px] leading-4 text-brand-muted">Research workspace</div>
          </div>
        </button>

        {/* Action buttons — only on results page */}
        {showActions && (
          <div className="flex shrink-0 items-center gap-2">
            <button
              onClick={onHome}
              className="flex h-8 items-center gap-2 rounded-md border border-brand-accent/30 bg-brand-highlight px-3 text-xs font-semibold text-brand-accent transition-all hover:border-brand-accent hover:bg-brand-accent hover:text-white"
              title="New research"
              type="button"
            >
              <Home size={14} />
              <span className="hidden sm:inline">Home</span>
            </button>

            <button
              onClick={onDownload}
              disabled={!onDownload}
              className="flex h-8 items-center gap-2 rounded-md border border-brand-accent/30 bg-brand-highlight px-3 text-xs font-semibold text-brand-accent transition-all hover:border-brand-accent hover:bg-brand-accent hover:text-white disabled:pointer-events-none disabled:opacity-30"
              title="Download report as Markdown"
              type="button"
            >
              <Download size={14} />
              <span className="hidden sm:inline">Download</span>
            </button>

            <button
              onClick={handleShare}
              className="flex h-8 items-center gap-2 rounded-md bg-brand-accent px-3 text-xs font-semibold text-white shadow-[0_2px_8px_rgba(226,90,61,0.35)] transition-all hover:opacity-90 hover:shadow-[0_4px_14px_rgba(226,90,61,0.45)]"
              title="Copy query to clipboard"
              type="button"
            >
              {copied ? <Check size={14} /> : <Share2 size={14} />}
              <span className="hidden sm:inline">{copied ? "Copied!" : "Share"}</span>
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
