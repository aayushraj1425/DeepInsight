import ReactMarkdown from "react-markdown"
import { FileText } from "lucide-react"

interface Props {
  report: string | null
}

export function ReportPanel({ report }: Props) {
  if (!report) return null

  return (
    <section className="animate-slide-in rounded-xl border border-[#E5E7EB] bg-white p-6 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)]">
      <div className="mb-5 flex items-center gap-2 text-sm font-semibold text-brand-ink">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-highlight">
          <FileText size={16} className="text-brand-accent" />
        </div>
        <span className="font-serif text-base font-bold">Research Report</span>
      </div>
      <article className="space-y-4 text-sm leading-7 text-brand-ink">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h2 className="font-serif text-xl font-bold text-brand-ink mt-6">{children}</h2>,
            h2: ({ children }) => <h3 className="font-serif text-base font-bold text-brand-ink mt-5 border-b border-[#E5E7EB] pb-2">{children}</h3>,
            h3: ({ children }) => <h4 className="text-sm font-semibold text-brand-ink mt-4">{children}</h4>,
            p: ({ children }) => <p className="text-brand-muted leading-7">{children}</p>,
            ul: ({ children }) => <ul className="list-disc space-y-2 pl-5 text-brand-muted">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal space-y-2 pl-5 text-brand-muted">{children}</ol>,
            li: ({ children }) => <li>{children}</li>,
            strong: ({ children }) => <strong className="font-semibold text-brand-ink">{children}</strong>,
            a: ({ href, children }) => (
              <a href={href} className="text-brand-accent underline decoration-brand-accent/40 underline-offset-4 hover:decoration-brand-accent transition-colors">
                {children}
              </a>
            ),
          }}
        >
          {report}
        </ReactMarkdown>
      </article>
    </section>
  )
}
