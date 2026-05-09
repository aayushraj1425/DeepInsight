import io
import pandas as pd


def parse_pdf(content: bytes, filename: str) -> list[dict]:
    """Extract text from PDF, return list of {title, abstract, source} dicts."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({"page": i + 1, "text": text})

    if not pages:
        return []

    # Chunk across pages into ~600-char segments with 80-char overlap
    full_text = "\n".join(p["text"] for p in pages)
    chunks = _chunk_text(full_text, size=600, overlap=80)

    return [
        {
            "title": f"{filename} [chunk {i+1}/{len(chunks)}]",
            "abstract": chunk,
            "paper_id": f"file:{filename}:chunk{i}",
            "year": None,
            "source": "upload",
        }
        for i, chunk in enumerate(chunks)
    ]


def parse_csv(content: bytes, filename: str) -> list[dict]:
    """Convert CSV into descriptive text chunks, return list of {title, abstract} dicts."""
    df = pd.read_csv(io.BytesIO(content))
    df = df.dropna(how="all")

    n_rows, n_cols = df.shape
    col_info = ", ".join(
        f"{col} ({df[col].dtype})" for col in df.columns
    )

    # Header chunk — schema + stats
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    stats_lines = []
    for col in numeric_cols[:8]:
        s = df[col].dropna()
        if len(s) > 0:
            stats_lines.append(
                f"  {col}: mean={s.mean():.3g}, min={s.min():.3g}, max={s.max():.3g}, n={len(s)}"
            )

    header_text = (
        f"Dataset: {filename}\n"
        f"Rows: {n_rows}, Columns: {n_cols}\n"
        f"Column schema: {col_info}\n"
        + ("Numeric summary:\n" + "\n".join(stats_lines) if stats_lines else "")
    )

    chunks = [
        {
            "title": f"{filename} [schema & statistics]",
            "abstract": header_text,
            "paper_id": f"file:{filename}:header",
            "year": None,
            "source": "upload",
        }
    ]

    # Row-level chunks — every 20 rows
    chunk_size = 20
    for start in range(0, min(n_rows, 200), chunk_size):
        slice_df = df.iloc[start: start + chunk_size]
        rows_text = slice_df.to_string(index=False, max_cols=12)
        chunk_idx = start // chunk_size
        chunks.append(
            {
                "title": f"{filename} [rows {start+1}–{start+len(slice_df)}]",
                "abstract": f"Dataset: {filename}\n{rows_text}",
                "paper_id": f"file:{filename}:rows{chunk_idx}",
                "year": None,
                "source": "upload",
            }
        )

    return chunks


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]
