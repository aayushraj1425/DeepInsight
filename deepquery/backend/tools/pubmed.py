import asyncio
import httpx

_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_HEADERS = {"User-Agent": "DeepQuery research demo"}


async def search_pubmed(query: str, limit: int = 6) -> list[dict]:
    """
    Search PubMed via NCBI eutils. No API key needed.
    Returns paper dicts in the same shape as search_papers().
    """
    async with httpx.AsyncClient(timeout=20.0, headers=_HEADERS) as http:
        # Step 1: get PMIDs
        search_resp = await http.get(
            f"{_BASE}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": min(limit * 2, 20),
                "retmode": "json",
                "sort": "relevance",
            },
        )
        search_resp.raise_for_status()
        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        await asyncio.sleep(0.4)

        # Step 2: fetch abstracts in MEDLINE format (has AB  - field tags)
        fetch_resp = await http.get(
            f"{_BASE}/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(ids),
                "rettype": "medline",
                "retmode": "text",
            },
        )
        fetch_resp.raise_for_status()
        raw_text = fetch_resp.text

        await asyncio.sleep(0.4)

        # Step 3: fetch structured summary (title, year, journal)
        summary_resp = await http.get(
            f"{_BASE}/esummary.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
            },
        )
        summary_resp.raise_for_status()
        summaries = summary_resp.json().get("result", {})

    # Parse the plain-text abstract dump — each record is separated by blank lines
    records = _parse_abstract_text(raw_text, ids)

    papers = []
    for pmid in ids:
        info = summaries.get(pmid, {})
        title = info.get("title", "").strip().rstrip(".")
        year_str = info.get("pubdate", "")[:4]
        year = int(year_str) if year_str.isdigit() else None
        journal = info.get("source", "")
        abstract = records.get(pmid, "")

        if not title or len(abstract) < 150:
            continue

        papers.append({
            "paper_id":       f"pmid:{pmid}",
            "title":          title,
            "abstract":       abstract,
            "tldr":           "",
            "year":           year,
            "citation_count": 0,
            "venue":          journal,
            "pub_types":      ["JournalArticle"],
            "openAccessPdf":  None,
            "externalIds":    {"PubMed": pmid},
            "url":            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "source":         "pubmed",
        })

    return papers[:limit]


def _parse_abstract_text(text: str, ids: list[str]) -> dict[str, str]:
    """
    Parse NCBI efetch plain-text output into a {pmid: abstract} dict.
    The text format has 'AB  - ' lines for abstracts and 'PMID- ' for IDs.
    """
    result: dict[str, str] = {}
    current_pmid: str | None = None
    abstract_lines: list[str] = []
    in_abstract = False

    for line in text.splitlines():
        if line.startswith("PMID- "):
            if current_pmid and abstract_lines:
                result[current_pmid] = " ".join(abstract_lines).strip()
            current_pmid = line[6:].strip()
            abstract_lines = []
            in_abstract = False

        elif line.startswith("AB  - "):
            in_abstract = True
            abstract_lines.append(line[6:].strip())

        elif in_abstract and line.startswith("      "):
            # continuation of abstract
            abstract_lines.append(line.strip())

        elif in_abstract and line.strip() == "":
            in_abstract = False

        elif in_abstract and not line.startswith(" "):
            in_abstract = False

    if current_pmid and abstract_lines:
        result[current_pmid] = " ".join(abstract_lines).strip()

    return result
