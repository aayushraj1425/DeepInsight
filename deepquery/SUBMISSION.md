# DeepQuery Hackathon Submission

## Required Fields

- **Project title:** DeepQuery
- **Team name:** DeepInsight
- **Track selected:** Agents Track
- **Repo link:** https://github.com/aayushraj1425/DeepInsight
- **Deployed URL:** TBD. Local demo URL: `http://127.0.0.1:5174/` or Vite fallback `http://127.0.0.1:5175/`
- **Loom video:** TODO: paste Loom URL after recording

## Team Roster

Replace placeholders before submission.

| Name | Role | Contact |
| --- | --- | --- |
| Alok Thakur | Full-stack / agents / product | TODO |
| TODO | TODO | TODO |
| TODO | TODO | TODO |

## Short Write-Up

DeepQuery helps researchers, students, and analysts move from a broad research question to a defensible answer. Traditional search gives users papers to read, while general chatbots often summarize without showing enough evidence. DeepQuery bridges that gap with a multi-agent research pipeline: a planner decomposes the question, discovery agents search scholarly sources, an extractor pulls numeric findings with exact quotes, an analyst runs comparisons, a critic checks whether the evidence is grounded, and a reporter produces an executive summary, charts, and a cited markdown report.

The workspace is designed for decision support rather than passive data display. Results include significance highlighting, sample-size weighting, and a Source Peek panel that links chart points back to the extracted quote behind them. For hackathon reliability, DeepQuery includes cached demo runs that stream the full agent workflow in seconds while preserving the same UI and event flow as live research mode. The impact is a faster, more transparent path from question to evidence-backed insight, especially for users who need to understand both the answer and why they should trust it.

## Loom Video Plan

Target length: 2-5 minutes. Record with Loom only.

1. **0:00-0:20** - Introduce DeepQuery and the problem: research answers are slow to verify and hard to trust.
2. **0:20-0:45** - Show the homepage and enter the cached demo query: `GLP-1 effects on cognition`.
3. **0:45-1:30** - Show the live agent pipeline streaming through planner, discovery, extractor, analyst, critic, visualizer, and reporter.
4. **1:30-2:15** - Show the Executive Summary card and explain the decision-support layer.
5. **2:15-3:00** - Show charts with significance/sample-size visual cues.
6. **3:00-3:40** - Click a chart bar or point and show Source Peek with the exact evidence quote.
7. **3:40-4:20** - Show the final markdown report and explain the critic/retry loop.
8. **4:20-4:45** - Mention limitations and next steps: Fast Mode, exact PDF offsets, deployment, persistent history.

## Demo Commands

Backend:

```bash
cd deepquery/backend
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd deepquery/frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5174/
```

If `5174` is occupied, use the Vite fallback shown in the terminal, commonly:

```text
http://127.0.0.1:5175/
```

## Cached Demo Queries

Use these exact queries to get fast cached runs:

```text
GLP-1 effects on cognition
Microplastics and gut microbiome
Vitamin D and depression
what is the effect of sleep deprivation on cognitive performance?
what are the economic effects of minimum wage increases?
```

## Architecture Summary

```text
React/Vite UI
  -> FastAPI backend
  -> LangGraph pipeline
  -> planner -> file_ingestor -> discovery -> extractor -> analyst -> critic
  -> critic routes to visualizer, analyst retry, or discovery retry
  -> visualizer -> reporter/synthesis
  -> SSE stream back to UI
```

## Environment

Sample env file:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

Do not commit a real API key. Use [backend/.env.example](backend/.env.example) as the safe sample.

## Data / Synthetic Data Provenance

- Live mode uses public research APIs: Semantic Scholar, PubMed, arXiv, OpenAlex, and optional web search.
- Cached hackathon demos are hand-authored synthetic examples in [backend/demo_cache.py](backend/demo_cache.py). They are included to make judging reproducible and should be described as synthetic demo data.
- Uploaded PDFs/CSVs/text files are parsed locally and stored in memory only for the active session.

## Known Limitations

- Live research can be slow because it performs search, PDF/full-text fetching, LLM extraction, analysis, critique, visualization, and synthesis.
- The app currently runs best as a single backend process because SSE sessions are in memory.
- Source Peek shows the extracted quote and source metadata, but does not yet scroll to exact PDF page offsets.
- Cached demos are synthetic and intended for demonstration, not factual evaluation.
- No public hosted deployment is configured yet unless the team adds one before submission.

## Submission Checklist

- [ ] Project title: DeepQuery
- [ ] Team name: DeepInsight
- [ ] Track: Agents Track
- [ ] Loom video URL added
- [ ] Repo public
- [ ] README includes quick start, architecture, env vars, data provenance, limitations
- [ ] Deployed URL or screen capture added
- [ ] Team roster completed
- [ ] 150-300 word write-up included
