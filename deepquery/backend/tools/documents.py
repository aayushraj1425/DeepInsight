import io
import re
from pathlib import Path
from typing import Any

from tools.numbers import extract_numeric_snippets

MAX_UPLOADS = 5
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 50_000
MAX_EXCERPT_CHARS = 420

STOP_WORDS = {
    "about", "after", "also", "among", "analysis", "and", "are", "been", "between",
    "both", "data", "does", "during", "each", "effect", "effects", "from", "have",
    "into", "more", "most", "paper", "results", "research", "study", "than", "that",
    "their", "them", "there", "these", "this", "those", "using", "were", "when",
    "with", "within", "your",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,}")


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_kind(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".docx":
        return "docx"
    if suffix in {".txt", ".md"}:
        return "text"
    return "unsupported"


def _decode_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def _extract_pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _extract_docx_text(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    counts: dict[str, int] = {}
    for token in WORD_RE.findall(text.lower()):
        if token in STOP_WORDS or token.isdigit():
            continue
        counts[token] = counts.get(token, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in ranked[:limit]]


def _excerpt(text: str) -> str:
    value = text[:MAX_EXCERPT_CHARS].strip()
    if len(text) > MAX_EXCERPT_CHARS:
        return value.rstrip() + "..."
    return value


def _source_id(index: int, filename: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-") or "document"
    return f"upload:{index}:{stem}"


def _error_document(index: int, upload: dict[str, Any], message: str) -> dict[str, Any]:
    filename = upload["name"]
    kind = detect_kind(filename)
    return {
        "source_id": _source_id(index, filename),
        "name": filename,
        "kind": kind if kind != "unsupported" else "file",
        "excerpt": message,
        "full_text_truncated": "",
        "keywords": [],
        "numeric_findings": [],
        "error": message,
    }


def _extract_text(kind: str, data: bytes) -> str:
    if kind == "pdf":
        return _extract_pdf_text(data)
    if kind == "docx":
        return _extract_docx_text(data)
    if kind == "text":
        return _decode_text(data)
    raise ValueError("Unsupported file type")


def normalize_uploads(uploads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []

    for index, upload in enumerate(uploads[:MAX_UPLOADS], start=1):
        filename = upload["name"]
        data: bytes = upload["data"]
        kind = detect_kind(filename)

        if len(data) > MAX_UPLOAD_BYTES:
            documents.append(_error_document(index, upload, "Skipped: file exceeds 10 MB limit."))
            continue

        if kind == "unsupported":
            documents.append(_error_document(index, upload, "Skipped: unsupported file type."))
            continue

        try:
            text = _normalize_whitespace(_extract_text(kind, data))
        except Exception as exc:
            documents.append(_error_document(index, upload, f"Skipped: could not parse file ({exc})."))
            continue

        if not text:
            documents.append(_error_document(index, upload, "Skipped: no readable text found in file."))
            continue

        truncated = text[:MAX_TEXT_CHARS]
        documents.append({
            "source_id": _source_id(index, filename),
            "name": filename,
            "kind": kind,
            "excerpt": _excerpt(truncated),
            "full_text_truncated": truncated,
            "keywords": extract_keywords(truncated),
            "numeric_findings": extract_numeric_snippets(truncated),
            "error": "",
        })

    for index, upload in enumerate(uploads[MAX_UPLOADS:], start=MAX_UPLOADS + 1):
        documents.append(_error_document(index, upload, "Skipped: only the first 5 files are ingested."))

    return documents


def documents_summary_payload(documents: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for document in documents:
        numeric_snippets = document.get("numeric_findings") or []
        parts.append(
            "\n".join([
                f"Document: {document['name']}",
                f"Kind: {document['kind']}",
                f"Keywords: {', '.join(document.get('keywords') or []) or 'none'}",
                f"Excerpt: {document.get('excerpt') or 'none'}",
                "Numeric snippets: " + (" | ".join(numeric_snippets[:6]) if numeric_snippets else "none"),
            ])
        )
    return "\n\n".join(parts)


def document_source_index(documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        document["source_id"]: {
            "source_id": document["source_id"],
            "source_type": "upload",
            "title": document["name"],
            "kind": document["kind"],
            "excerpt": document["excerpt"],
        }
        for document in documents
    }
