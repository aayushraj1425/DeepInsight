import ReactMarkdown from "react-markdown"
import { BookOpen } from "lucide-react"

interface Props {
  report: string | null
}

export function ReportPanel({ report }: Props) {
  if (!report) return null

  return (
    <section className="animate-slide-in rounded-2xl border border-brand-border bg-white p-6 shadow-[0_8px_30px_-8px_rgba(226,90,61,0.08)]">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-highlight border border-brand-border">
          <BookOpen size={17} className="text-brand-accent" />
        </div>
        <h2 className="font-serif text-base font-bold text-brand-ink">Research Report</h2>
      </div>

      <article className="prose prose-sm max-w-none text-brand-ink">
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <h2 className="mt-8 mb-3 font-serif text-xl font-bold text-brand-ink first:mt-0">{children}</h2>
            ),
            h2: ({ children }) => (
              <h3 className="mt-6 mb-2 flex items-center gap-2 font-serif text-base font-bold text-brand-ink border-b border-brand-border pb-2 first:mt-0">
                <span className="inline-block h-3 w-1 rounded-full bg-brand-accent" />
                {children}
              </h3>
            ),
            h3: ({ children }) => (
              <h4 className="mt-4 mb-1.5 text-sm font-semibold text-brand-ink">{children}</h4>
            ),
            p: ({ children }) => (
              <p className="mb-4 text-sm leading-7 text-brand-muted">{children}</p>
            ),
            ul: ({ children }) => (
              <ul className="mb-4 space-y-2 pl-0 list-none">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="mb-4 space-y-2 pl-5 list-decimal text-sm text-brand-muted">{children}</ol>
            ),
            li: ({ children }) => (
              <li className="flex items-start gap-2 text-sm text-brand-muted">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-accent" />
                <span>{children}</span>
              </li>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-brand-ink">{children}</strong>
            ),
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="text-brand-accent underline decoration-brand-accent/30 underline-offset-4 hover:decoration-brand-accent transition-colors"
              >
                {children}
              </a>
            ),
            blockquote: ({ children }) => (
              <blockquote className="my-4 border-l-2 border-brand-accent pl-4 text-sm italic text-brand-muted">
                {children}
              </blockquote>
            ),
          }}
        >
          {report}
        </ReactMarkdown>
      </article>
    </section>
  )
}
