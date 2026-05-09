import { useState, useRef } from "react"
import { ArrowRight, Paperclip, X, FileText, FileSpreadsheet } from "lucide-react"
import logo from "../../assets/logo.png"

export const EXAMPLE_QUERIES = [
  "GLP-1 effects on cognition",
  "Microplastics and gut microbiome",
  "Vitamin D and depression",
]

interface InputViewProps {
  onAnalyze: (query: string, files: File[]) => void
}

export function InputView({ onAnalyze }: InputViewProps) {
  const [query, setQuery] = useState("")
  const [files, setFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (q = query) => {
    if (q.trim() || files.length > 0) {
      onAnalyze(q.trim(), files)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)])
    }
  }

  return (
    <div className="flex h-full w-full flex-col items-center justify-center px-6 py-20 bg-brand-background">
      {/* Logo */}
      <div className="mb-14 flex items-center gap-3 animate-slide-in">
        <img src={logo} alt="DeepQuery" className="h-14 w-14 rounded-xl object-contain" />
        <span className="font-serif text-2xl font-bold text-brand-ink">DeepQuery</span>
      </div>

      {/* Hook */}
      <h1
        className="font-serif text-center font-bold text-brand-ink leading-tight animate-slide-in"
        style={{ fontSize: "clamp(2rem, 5vw, 3.5rem)", animationDelay: "60ms", maxWidth: "760px" }}
      >
        Ask any research question. Watch six agents argue until the evidence holds up.
      </h1>

      {/* Motto */}
      <p
        className="mt-5 text-center text-brand-muted italic animate-slide-in"
        style={{ fontSize: "clamp(1rem, 2vw, 1.25rem)", animationDelay: "120ms" }}
      >
        Research that argues with itself.
      </p>

      {/* Search bar */}
      <div
        className="mt-12 w-full max-w-2xl animate-slide-in"
        style={{ animationDelay: "180ms" }}
      >
        <div className="flex items-center gap-3 rounded-2xl border border-[#E5E7EB] bg-white px-5 py-3.5 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)] transition-all focus-within:border-brand-accent/50 focus-within:shadow-[0_10px_40px_-10px_rgba(226,90,61,0.18)]">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="e.g. Does intermittent fasting reduce inflammation markers?"
            className="flex-1 bg-transparent text-base text-brand-ink placeholder-brand-muted/50 focus:outline-none"
            autoFocus
          />

          {/* Attach files */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="shrink-0 text-brand-muted transition-colors hover:text-brand-accent"
            title="Attach PDF or CSV"
          >
            <Paperclip size={18} />
          </button>
          <input
            type="file"
            multiple
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileChange}
            accept=".pdf,.csv,.txt"
          />

          {/* Submit */}
          <button
            onClick={() => handleSubmit()}
            disabled={!query.trim() && files.length === 0}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-accent text-white shadow-[0_4px_14px_rgba(226,90,61,0.35)] transition-all hover:opacity-90 hover:shadow-[0_4px_20px_rgba(226,90,61,0.5)] disabled:opacity-30 disabled:shadow-none"
          >
            <ArrowRight size={18} />
          </button>
        </div>

        {/* Attached files */}
        {files.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {files.map((file, idx) => (
              <span
                key={idx}
                className="flex items-center gap-1.5 rounded-full border border-[#E5E7EB] bg-brand-surface px-3 py-1 text-xs font-medium text-brand-ink"
              >
                {file.name.endsWith(".csv")
                  ? <FileSpreadsheet size={12} className="text-emerald-500" />
                  : <FileText size={12} className="text-brand-accent" />}
                {file.name}
                <button
                  onClick={() => setFiles((prev) => prev.filter((_, i) => i !== idx))}
                  className="ml-1 text-brand-muted hover:text-red-500 transition-colors"
                >
                  <X size={11} />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Example queries */}
      <div
        className="mt-10 flex flex-col items-center gap-3 animate-slide-in"
        style={{ animationDelay: "240ms" }}
      >
        <p className="text-[11px] font-semibold uppercase tracking-widest text-brand-muted/60">
          Try one of these
        </p>
        <div className="flex flex-col items-center gap-2">
          {EXAMPLE_QUERIES.map((eq) => (
            <button
              key={eq}
              onClick={() => handleSubmit(eq)}
              className="group flex items-center gap-2 text-sm text-brand-muted transition-all hover:text-brand-accent"
            >
              <span className="h-px w-4 rounded bg-brand-muted/30 transition-all group-hover:w-5 group-hover:bg-brand-accent" />
              <span className="underline underline-offset-4 decoration-transparent group-hover:decoration-brand-accent/50 transition-all">
                "{eq}"
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
