import { CheckCircle2 } from "lucide-react"

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
  return markdown
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
    <section className="rounded-lg border border-slate-800 bg-[#11151b] p-5">
      <div className="mb-4 flex items-center gap-2">
        <CheckCircle2 size={16} className="text-cyan-300" />
        <h2 className="text-sm font-semibold text-slate-100">Key takeaways</h2>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {takeaways.map((takeaway) => (
          <div key={takeaway} className="flex items-start gap-3 rounded-md border border-slate-800 bg-slate-950/50 p-3">
            <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-emerald-300" />
            <p className="text-sm leading-6 text-slate-300">{takeaway}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
