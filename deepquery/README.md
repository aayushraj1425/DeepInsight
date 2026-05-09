# DeepQuery

DeepQuery is a multi-agent research intelligence workspace. A user submits a research question and optional files; the backend plans an investigation, searches scholarly and public data sources, validates evidence quality, extracts findings, runs analysis, reasons across sources, fact-checks claims, generates explanatory charts, and writes a professional markdown intelligence report while streaming every step over SSE.

## What Exists Now

- Backend: FastAPI + LangGraph pipeline
- Transport: SSE event stream per investigation session
- Frontend: live prompt workspace with SSE streaming, charts, sources, and optional uploads
- Data discovery: Semantic Scholar, OpenAlex, arXiv, Crossref, Data.gov, DataCite, and trusted public time-series adapters for sources such as BLS, FRED, and World Bank

## Backend

The backend is in `deepquery/backend/`.

### Endpoints

- `GET /api/health`
- `POST /api/investigations`
- `GET /api/stream/{session_id}`

### Pipeline

The LangGraph pipeline runs these agents in order:

`ingestor -> orchestrator -> discovery -> datafinder -> validator -> extractor -> analyst -> reasoner -> economist -> factchecker -> visualizer -> reporter`

The pipeline prioritizes source quality and claim verification over fast chart generation.

### Agent Responsibilities

- `ingestor`: reads optional PDF, DOCX, TXT, and Markdown context
- `orchestrator`: decomposes the research question into subproblems, source priorities, dataset targets, fact checks, and scenario axes
- `discovery`: searches Semantic Scholar, OpenAlex, arXiv, and Crossref, then deduplicates and ranks papers
- `datafinder`: searches public dataset catalogs and trusted public time series, then profiles loadable CSV/JSON resources
- `validator`: scores source credibility, freshness, methodology risk, and primary-source coverage
- `extractor`: turns papers, uploaded files, and dataset summaries into structured findings
- `analyst`: runs deterministic aggregate, comparison, trend, and source-triangulation analysis
- `reasoner`: synthesizes causal mechanisms, contradictions, historical comparisons, and evidence gaps
- `economist`: builds cautious scenarios without unsupported productivity-to-job-loss arithmetic
- `factchecker`: verifies major claims and numerical assertions before reporting
- `visualizer`: builds evidence-led Plotly charts such as trusted time-series trends, scenario confidence, and source-quality views
- `reporter`: writes the final intelligence report with inline source-title citations

### Data Captured

The backend works with these core research fields:

- `paper_id`
- `title`
- `abstract`
- `year`
- `citation_count`
- `metric`
- `value`
- `sample_size`
- `ci`
- `p_value`
- `intervention`
- `source_quote`
- `paper_title`
- `analysis`
- `chart_specs`
- `report`
- `source_type`
- `source_title`
- `dataset_analysis`
- `research_plan`
- `validation_report`
- `reasoning`
- `economic_model`
- `fact_check_report`

### SSE Event Types

- `node_start`
- `node_end`
- `tool_call`
- `tool_result`
- `critic_decision`
- `documents_ready`
- `plan_ready`
- `sources_ready`
- `datasets_ready`
- `validation_ready`
- `reasoning_ready`
- `model_ready`
- `factcheck_ready`
- `chart_ready`
- `report_ready`
- `error`
- `done`

Each event includes `type`, `agent`, `payload`, and `timestamp`.

## Frontend

The frontend is in `deepquery/frontend/`.

Current live workspace sections:

- sticky top bar
- left navigation rail
- hero card with status and metrics
- key takeaways panel
- charts grid
- report section
- sidebar with agent activity, uploaded document cards, research papers, and public dataset candidates
- prompt composer with optional PDF, DOCX, TXT, and Markdown uploads

## Running It

### Backend

```bash
cd deepquery/backend
source .venv/bin/activate
uvicorn deepquery.backend.main:app --host 127.0.0.1 --port 8000
```

The backend expects `deepquery/backend/.env` to contain `OPENAI_API_KEY`.
For live Semantic Scholar retrieval, set `SEMANTIC_SCHOLAR_API_KEY` as well.

If Windows reports `[WinError 10013]` while starting Uvicorn, check whether the backend is already running:

```powershell
netstat -ano | findstr :8000
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health
```

If `/api/health` returns `{"status":"ok"}`, keep using the running backend instead of starting a second one. To move the backend to another port, start Uvicorn with that port and set `VITE_API_URL` or `VITE_API_BASE_URL` in `deepquery/frontend/.env`.

### Frontend

```bash
cd deepquery/frontend
npm install
npm run dev
```

The frontend uses Vite and will bind to `127.0.0.1:5174`, falling back to the next available `517x` port if needed.

## Notes

- SSE sessions are stored in memory, so run a single backend process.
- `deepquery/backend/llm.py` strips whitespace from `OPENAI_API_KEY` before creating the client.
- `deepquery/backend/main.py` allows localhost Vite dev origins through CORS.
- Semantic Scholar requests are rate-limited and paced in the backend. With an API key, DeepQuery assumes roughly `1 request/second` across Semantic Scholar endpoints.
- Cached demo playback is not used by the live investigation path.

