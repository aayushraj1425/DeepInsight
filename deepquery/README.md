# DeepQuery

DeepQuery is a multi-agent research pipeline. A user submits a research question, the backend searches papers, extracts structured findings, runs analysis, generates charts, and writes a markdown report while streaming every step over SSE.

## What Exists Now

- Backend: FastAPI + LangGraph pipeline
- Transport: SSE event stream per investigation session
- Frontend: static layout shell built component by component
- Demo support: cached runs for known queries

## Backend

The backend is in `deepquery/backend/`.

### Endpoints

- `GET /api/health`
- `POST /api/investigations`
- `GET /api/stream/{session_id}`

### Pipeline

The LangGraph pipeline runs these agents in order:

`planner -> discovery -> extractor -> analyst -> critic -> visualizer -> reporter`

The critic can route back to `analyst` for retries before continuing to `visualizer`.

### Agent Responsibilities

- `planner`: decomposes the research question into 2 to 4 subqueries
- `discovery`: searches Semantic Scholar and deduplicates papers
- `extractor`: turns paper abstracts into structured findings
- `analyst`: runs aggregate, compare, and correlate analysis
- `critic`: approves or rejects the analysis and can force a retry
- `visualizer`: chooses Plotly chart templates and builds chart specs
- `reporter`: writes the final markdown report

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

### SSE Event Types

- `node_start`
- `node_end`
- `tool_call`
- `tool_result`
- `critic_decision`
- `chart_ready`
- `report_ready`
- `error`
- `done`

Each event includes `type`, `agent`, `payload`, and `timestamp`.

## Frontend

The frontend is in `deepquery/frontend/`.

Current shell sections:

- sticky top bar
- left navigation rail
- hero card with status and metrics
- key takeaways panel
- charts grid
- report section
- sidebar with agent activity and research sources

The shell is currently fixture-driven so the layout and component work can be tested independently of live backend data.

## Running It

### Backend

```bash
cd deepquery/backend
source .venv/bin/activate
uvicorn deepquery.backend.main:app --host 127.0.0.1 --port 8000
```

The backend expects `deepquery/backend/.env` to contain `OPENAI_API_KEY`.

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
- `demo_cache.py` can bypass live OpenAI and Semantic Scholar calls for known demo queries.

