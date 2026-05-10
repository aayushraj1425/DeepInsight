import { useState, useRef } from "react"
import { ArrowRight, Paperclip, X, FileText, FileSpreadsheet } from "lucide-react"
import logo from "../../assets/logo.png"
import { HomeResearchAnimation } from "./HomeResearchAnimation"
import { PipelineDiagram } from "./PipelineDiagram"

const EXAMPLE_QUERIES = [
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
    <div className="flex min-h-full w-full flex-col items-center justify-start bg-brand-background px-4 py-8 sm:px-6 sm:py-10 lg:justify-center lg:py-12">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-3 animate-slide-in sm:mb-10">
        <img src={logo} alt="DeepQuery" className="h-14 w-14 rounded-xl object-contain" />
        <span className="font-serif text-2xl font-bold text-brand-ink">DeepQuery</span>
      </div>

      {/* Hook */}
      <h1
        className="max-w-3xl text-center font-serif text-3xl font-bold leading-tight text-brand-ink animate-slide-in sm:text-4xl lg:text-5xl"
        style={{ animationDelay: "60ms" }}
      >
        Ask any research question. Watch six agents argue until the evidence holds up.
      </h1>

      {/* Motto */}
      <p
        className="mt-5 text-center text-base italic text-brand-muted animate-slide-in sm:text-lg"
        style={{ animationDelay: "120ms" }}
      >
        Research that checks itself.
      </p>

      <HomeResearchAnimation />

      {/* Search bar */}
      <div
        className="mt-6 w-full max-w-2xl animate-slide-in sm:mt-8"
        style={{ animationDelay: "220ms" }}
      >
        <div className="flex items-center gap-2 rounded-2xl border border-[#E5E7EB] bg-white px-3 py-3.5 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)] transition-all focus-within:border-brand-accent/50 focus-within:shadow-[0_10px_40px_-10px_rgba(226,90,61,0.18)] sm:gap-3 sm:px-5">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="e.g. Does intermittent fasting reduce inflammation markers?"
            className="min-w-0 flex-1 bg-transparent text-base text-brand-ink placeholder-brand-muted/50 focus:outline-none"
            autoFocus
          />

          {/* Attach files */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="shrink-0 rounded-lg border border-brand-accent/25 bg-brand-highlight p-1 text-brand-accent shadow-sm transition-all hover:border-brand-accent hover:bg-brand-accent hover:text-white"
            title="Attach PDF or CSV"
            aria-label="Attach PDF or CSV"
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
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-accent text-white shadow-[0_4px_14px_rgba(226,90,61,0.35)] transition-all hover:opacity-90 hover:shadow-[0_4px_20px_rgba(226,90,61,0.45)] disabled:bg-brand-highlight disabled:text-brand-accent/45 disabled:shadow-none"
            aria-label="Start research"
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
                <span className="max-w-[14rem] truncate">{file.name}</span>
                <button
                  onClick={() => setFiles((prev) => prev.filter((_, i) => i !== idx))}
                  className="ml-1 rounded-full bg-rose-50 p-0.5 text-rose-600 transition-colors hover:bg-rose-600 hover:text-white"
                  aria-label={`Remove ${file.name}`}
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
        className="mt-8 flex flex-col items-center gap-3 animate-slide-in"
        style={{ animationDelay: "280ms" }}
      >
        <p className="text-[11px] font-semibold uppercase tracking-widest text-brand-muted/60">
          Try one of these
        </p>
        <div className="flex flex-col items-center gap-2">
          {EXAMPLE_QUERIES.map((eq) => (
            <button
              key={eq}
              onClick={() => handleSubmit(eq)}
              className="group flex max-w-full items-center gap-2 rounded-lg border border-brand-accent/20 bg-brand-highlight/60 px-3 py-1.5 text-sm font-medium text-brand-accent transition-all hover:border-brand-accent hover:bg-brand-accent hover:text-white"
            >
              <span className="h-px w-4 rounded bg-brand-accent/50 transition-all group-hover:w-5 group-hover:bg-white/75" />
              <span className="truncate underline underline-offset-4 decoration-transparent transition-all group-hover:decoration-white/60">
                "{eq}"
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Pipeline diagram */}
      <div
        className="mt-10 flex w-full flex-col items-center animate-slide-in sm:mt-12"
        style={{ animationDelay: "340ms" }}
      >
        <PipelineDiagram />
      </div>
    </div>
  )
}
