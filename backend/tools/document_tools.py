import re
from pathlib import Path
from typing import Any, Optional
import pypdf

from backend.config import DOCS_DIR, PROJECT_ROOT


def _resolve_doc_path(doc_id: str) -> Path:
    """Finds the document path by doc_id (filename or stem) in DOCS_DIR or PROJECT_ROOT."""
    # Check directly in DOCS_DIR
    p = DOCS_DIR / doc_id
    if p.exists() and p.is_file():
        return p
    
    # Check with .pdf extension
    p_pdf = DOCS_DIR / f"{doc_id}.pdf"
    if p_pdf.exists() and p_pdf.is_file():
        return p_pdf

    # Check root workspace for initial sample PDFs
    root_p = PROJECT_ROOT / doc_id
    if root_p.exists() and root_p.is_file():
        return root_p
    root_pdf = PROJECT_ROOT / f"{doc_id}.pdf"
    if root_pdf.exists() and root_pdf.is_file():
        return root_pdf

    # Check if doc_id matches any file name or stem
    for folder in [DOCS_DIR, PROJECT_ROOT]:
        for candidate in folder.glob("*.pdf"):
            if candidate.name == doc_id or candidate.stem == doc_id:
                return candidate

    raise FileNotFoundError(f"Document with id '{doc_id}' not found.")


def list_documents() -> list[dict[str, Any]]:
    """
    Returns titles and metadata for all available documents (nothing else).
    No document content is returned.
    """
    documents = []
    seen = set()

    for folder in [DOCS_DIR, PROJECT_ROOT]:
        for pdf_file in folder.glob("*.pdf"):
            if pdf_file.name in seen:
                continue
            seen.add(pdf_file.name)
            try:
                reader = pypdf.PdfReader(str(pdf_file))
                page_count = len(reader.pages)
                title = pdf_file.stem
                if reader.metadata and reader.metadata.title:
                    title = reader.metadata.title
                documents.append({
                    "doc_id": pdf_file.name,
                    "title": str(title),
                    "page_count": page_count,
                    "filename": pdf_file.name,
                    "size_bytes": pdf_file.stat().st_size
                })
            except Exception as e:
                documents.append({
                    "doc_id": pdf_file.name,
                    "title": pdf_file.stem,
                    "page_count": 0,
                    "filename": pdf_file.name,
                    "error": str(e)
                })

    return documents


def list_headings(doc_id: str) -> list[dict[str, Any]]:
    """
    Returns the table of contents / list of all headings for a document (nothing else).
    Extracted on-demand from the PDF outline / bookmarks.
    """
    doc_path = _resolve_doc_path(doc_id)
    reader = pypdf.PdfReader(str(doc_path))
    headings: list[dict[str, Any]] = []

    def _extract_outline(outline_items):
        for item in outline_items:
            if isinstance(item, list):
                _extract_outline(item)
            elif hasattr(item, "title"):
                page_num = None
                try:
                    if hasattr(item, "page"):
                        page_num = reader.get_destination_page_number(item) + 1
                except Exception:
                    page_num = None
                headings.append({
                    "title": str(item.title).strip(),
                    "page": page_num
                })

    try:
        if reader.outline:
            _extract_outline(reader.outline)
    except Exception:
        pass

    # If document has no PDF bookmarks/outline, fallback: scan first few pages (TOC or top lines)
    if not headings:
        # Check first 5 pages for section-like headings without loading the full document
        max_scan = min(10, len(reader.pages))
        for p_idx in range(max_scan):
            page_text = reader.pages[p_idx].extract_text() or ""
            for line in page_text.splitlines():
                line_str = line.strip()
                # Simple heuristic for headings like "1. Introduction", "Chapter 2", "Contents"
                if re.match(r'^(Chapter\s+\d+|Section\s+\d+|\d+(\.\d+)*\s+[A-Z]|[A-Z\s]{4,30}$)', line_str):
                    headings.append({
                        "title": line_str,
                        "page": p_idx + 1
                    })
                    if len(headings) >= 25:
                        break
            if len(headings) >= 25:
                break

    return headings


def search_keyword(doc_id: str, keyword: str) -> list[int]:
    """
    Returns page numbers (1-indexed) where a keyword appears.
    ONLY page numbers are returned, nothing else (no text snippets, no scores).
    Scans on-demand without any persistent index or vector DB.
    """
    if not keyword or not keyword.strip():
        return []

    doc_path = _resolve_doc_path(doc_id)
    reader = pypdf.PdfReader(str(doc_path))
    term = keyword.strip().lower()

    matching_pages: list[int] = []
    total_pages = len(reader.pages)

    for idx in range(total_pages):
        page = reader.pages[idx]
        text = (page.extract_text() or "").lower()
        if term in text:
            matching_pages.append(idx + 1)

    return matching_pages


def get_page(doc_id: str, page_number: int) -> str:
    """
    Returns the text of one page (only one page, 1-indexed, no page ranges).
    No pre-reading or caching is performed.
    """
    doc_path = _resolve_doc_path(doc_id)
    reader = pypdf.PdfReader(str(doc_path))
    total_pages = len(reader.pages)

    if page_number < 1 or page_number > total_pages:
        raise ValueError(
            f"Page number {page_number} is out of range. Document has {total_pages} pages (1-indexed)."
        )

    page = reader.pages[page_number - 1]
    text = page.extract_text() or ""
    return text
