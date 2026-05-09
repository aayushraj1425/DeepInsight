import ReactMarkdown from "react-markdown"
import { FileText } from "lucide-react"

interface Props {
  report: string | null
}

export function ReportPanel({ report }: Props) {
  if (!report) return null

  return (
    <section className="animate-slide-in rounded-lg border border-gray-800 bg-gray-900/60 p-5">
      <div className="mb-4 flex items-center gap-2 text-sm font-medium text-gray-200">
        <FileText size={16} className="text-cyan-400" />
        Research report
      </div>
      <article className="space-y-4 text-sm leading-7 text-gray-300">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h2 className="text-xl font-semibold text-gray-100">{children}</h2>,
            h2: ({ children }) => <h3 className="text-base font-semibold text-gray-100">{children}</h3>,
            h3: ({ children }) => <h4 className="text-sm font-semibold text-gray-100">{children}</h4>,
            p: ({ children }) => <p>{children}</p>,
            ul: ({ children }) => <ul className="list-disc space-y-2 pl-5">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal space-y-2 pl-5">{children}</ol>,
            li: ({ children }) => <li>{children}</li>,
            strong: ({ children }) => <strong className="font-semibold text-gray-100">{children}</strong>,
            a: ({ href, children }) => (
              <a href={href} className="text-blue-300 underline decoration-blue-500/50 underline-offset-4">
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
