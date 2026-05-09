import { CheckCircle2, Sparkles } from "lucide-react"

interface KeyTakeawaysProps {
  markdown: string
  maxItems?: number
}

function cleanMarkdownBullet(line: string) {
  return line
    .replace(/^[-*]\s+/, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/_(.*?)_/g, "$1")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
    .trim()
}

function extractBullets(markdown: string, maxItems: number) {
  const keyFindingsMatch = markdown.match(/##\s+Key Findings\s+([\s\S]*?)(?=\n##\s+|\s*$)/i)
  const source = keyFindingsMatch ? keyFindingsMatch[1] : markdown

  return source
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^[-*]\s+/.test(line))
    .map(cleanMarkdownBullet)
    .filter(Boolean)
    .slice(0, maxItems)
}

export function KeyTakeaways({ markdown, maxItems = 4 }: KeyTakeawaysProps) {
  const takeaways = extractBullets(markdown, maxItems)

  if (takeaways.length === 0) {
    return null
  }

  return (
    <section className="rounded-2xl border border-[#E5E7EB] bg-white p-6 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.05)]">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-highlight">
          <Sparkles size={20} className="text-brand-accent" />
        </div>
        <div>
          <h2 className="font-serif text-lg font-bold tracking-tight text-brand-ink">Key Takeaways</h2>
          <p className="text-xs text-brand-muted font-medium">Extracted from research synthesis</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {takeaways.map((takeaway, i) => (
          <div
            key={takeaway}
            className="flex items-start gap-4 rounded-xl border border-[#E5E7EB] bg-brand-surface p-4 transition-all duration-200 hover:border-brand-accent/30 hover:shadow-[0_10px_30px_-10px_rgba(0,0,0,0.06)] hover:-translate-y-0.5"
            style={{ animation: `slideUp 0.5s ease-out ${i * 0.15}s both` }}
          >
            <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-highlight text-brand-accent transition-all duration-200">
              <CheckCircle2 size={14} className="stroke-[2.5]" />
            </div>
            <p className="text-sm leading-relaxed text-brand-ink">
              {takeaway}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
