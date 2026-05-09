import asyncio
import io
import httpx

_TIMEOUT = 10.0
_MAX_CHARS = 8000  # cap to avoid giant prompts


async def _fetch_pdf_text(url: str, client: httpx.AsyncClient) -> str:
    """Download a PDF and extract its text. Returns '' on any failure."""
    try:
        resp = await client.get(url, follow_redirects=True, timeout=_TIMEOUT)
        resp.raise_for_status()
        if "pdf" not in resp.headers.get("content-type", "").lower() and not url.endswith(".pdf"):
            return ""
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(resp.content))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
            # Stop once we have enough text
            if sum(len(p) for p in pages) >= _MAX_CHARS:
                break
        return "\n\n".join(pages)[:_MAX_CHARS]
    except Exception:
        return ""


async def fetch_full_text(paper: dict) -> str:
    """
    Try to get actual paper body text in priority order:
      1. openAccessPdf URL from Semantic Scholar
      2. arXiv PDF via externalIds.ArXiv
      3. PubMed Central full-text via NCBI API
    Falls back to abstract+tldr if nothing works.
    """
    external_ids = paper.get("externalIds") or {}

    candidates: list[str] = []

    # 1. Semantic Scholar open-access PDF
    oa = paper.get("openAccessPdf") or {}
    if isinstance(oa, dict) and oa.get("url"):
        candidates.append(oa["url"])

    # 2. arXiv PDF
    arxiv_id = external_ids.get("ArXiv")
    if arxiv_id:
        candidates.append(f"https://arxiv.org/pdf/{arxiv_id}.pdf")

    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        headers={"User-Agent": "DeepQuery research demo"},
    ) as client:
        # Try PDF sources in order
        for url in candidates:
            text = await _fetch_pdf_text(url, client)
            if len(text) >= 500:
                return text[:_MAX_CHARS]

        # 3. PubMed Central plain-text via NCBI eutils
        pmc_id = external_ids.get("PubMedCentral")
        if pmc_id:
            try:
                resp = await client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    params={"db": "pmc", "id": pmc_id, "rettype": "text", "retmode": "text"},
                    timeout=_TIMEOUT,
                )
                if resp.status_code == 200 and len(resp.text) >= 500:
                    return resp.text[:_MAX_CHARS]
            except Exception:
                pass

    # Fallback: abstract + tldr (same as before)
    parts = []
    if paper.get("abstract"):
        parts.append(paper["abstract"])
    tldr = paper.get("tldr") or ""
    if tldr and tldr not in (paper.get("abstract") or ""):
        parts.append(tldr)
    return "\n\n".join(parts).strip()
