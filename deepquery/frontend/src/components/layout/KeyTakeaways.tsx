import { Flame } from "lucide-react"

interface KeyTakeawaysProps {
  markdown: string
  maxItems?: number
}

function cleanBullet(line: string) {
  return line
    .replace(/^[-*]\s+/, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/_(.*?)_/g, "$1")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .trim()
}

function extractBullets(markdown: string, maxItems: number) {
  const match = markdown.match(/##\s+Key Findings\s+([\s\S]*?)(?=\n##\s+|\s*$)/i)
  const source = match ? match[1] : markdown
  return source
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => /^[-*]\s+/.test(l))
    .map(cleanBullet)
    .filter(Boolean)
    .slice(0, maxItems)
}

export function KeyTakeaways({ markdown, maxItems = 4 }: KeyTakeawaysProps) {
  const takeaways = extractBullets(markdown, maxItems)
  if (takeaways.length === 0) return null

  return (
    <section className="rounded-2xl border border-brand-border bg-white p-6 shadow-[0_8px_30px_-8px_rgba(226,90,61,0.10)]">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-accent shadow-[0_4px_12px_rgba(226,90,61,0.3)]">
          <Flame size={18} className="text-white" />
        </div>
        <div>
          <h2 className="font-serif text-base font-bold text-brand-ink">Key Takeaways</h2>
          <p className="text-[11px] text-brand-muted">Extracted from research synthesis</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {takeaways.map((takeaway, i) => (
          <div
            key={i}
            className="group flex items-start gap-3 rounded-xl border border-brand-border bg-brand-surface p-4 transition-all hover:border-brand-accent/40 hover:bg-brand-highlight/40 hover:-translate-y-0.5"
            style={{ animation: `slideUp 0.4s ease-out ${i * 100}ms both` }}
          >
            <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-accent/10 text-brand-accent group-hover:bg-brand-accent group-hover:text-white transition-all">
              <span className="text-[10px] font-bold">{i + 1}</span>
            </div>
            <p className="text-sm leading-relaxed text-brand-ink">{takeaway}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
