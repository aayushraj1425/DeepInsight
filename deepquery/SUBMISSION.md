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
| Alok Thakur | backend / agents / product | (https://www.linkedin.com/in/alokthakur012/) |
| Aayush Raj Sah | frontend / UI/UX / product | https://www.linkedin.com/in/aayush-raj-sah-01b24b364/?skipRedirect=true |


## Short Write-Up

DeepQuery helps researchers, students, and analysts move from a broad research question to a defensible answer. Traditional search gives users papers to read, while general chatbots often summarize without showing enough evidence. DeepQuery bridges that gap with a multi-agent research pipeline: a planner decomposes the question, discovery agents search scholarly sources, an extractor pulls numeric findings with exact quotes, an analyst runs comparisons, a critic checks whether the evidence is grounded, and a reporter produces an executive summary, charts, and a cited markdown report.

The workspace is designed for decision support rather than passive data display. Results include significance highlighting, sample-size weighting, and a Source Peek panel that links chart points back to the extracted quote behind them. For hackathon reliability, DeepQuery includes cached demo runs that stream the full agent workflow in seconds while preserving the same UI and event flow as live research mode. The impact is a faster, more transparent path from question to evidence-backed insight, especially for users who need to understand both the answer and why they should trust it.



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

## Known Limitations

- Live research can be slow because it performs search, PDF/full-text fetching, LLM extraction, analysis, critique, visualization, and synthesis.
- The app currently runs best as a single backend process because SSE sessions are in memory.
- Source Peek shows the extracted quote and source metadata, but does not yet scroll to exact PDF page offsets.
- Cached demos are synthetic and intended for demonstration, not factual evaluation.
- No public hosted deployment is configured yet unless the team adds one before submission.


