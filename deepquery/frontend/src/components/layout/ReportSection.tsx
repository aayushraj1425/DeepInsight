import { ReportPanel } from "../ReportPanel"

interface ReportSectionProps {
  markdown: string
}

export function ReportSection({ markdown }: ReportSectionProps) {
  return <ReportPanel report={markdown} />
}
