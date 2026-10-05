import json
import hashlib
from pathlib import Path
from typing import Optional, Any
import pypdf

from backend.config import CHUNKS_DIR, DOCS_DIR, PROJECT_ROOT
from backend.tools.document_tools import _resolve_doc_path, list_headings
from backend.retrieval.chunker import Chunk, chunk_document_pages


def compute_file_hash(file_path: Path) -> str:
    """Computes SHA256 content hash of a file for stale-index protection."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ChunkStore:
    """
    Local Chunk Store scoped strictly by doc_id.
    Stores and retrieves chunks in pure Python / JSON without vector databases.
    Guarantees cross-document isolation and stale index protection.
    """
    def __init__(self, doc_id: str, content_hash: str, chunks: Optional[list[Chunk]] = None):
        self.doc_id = doc_id
        self.content_hash = content_hash
        self.chunks: list[Chunk] = chunks or []
        self._page_map: dict[int, list[Chunk]] = {}
        self._build_index()

    def _build_index(self):
        self._page_map = {}
        for c in self.chunks:
            if c.page not in self._page_map:
                self._page_map[c.page] = []
            self._page_map[c.page].append(c)

    def get_chunks(self) -> list[Chunk]:
        return self.chunks

    def get_page_chunks(self, page: int) -> list[Chunk]:
        return self._page_map.get(page, [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content_hash": self.content_hash,
            "chunks_count": len(self.chunks),
            "chunks": [c.to_dict() for c in self.chunks],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ChunkStore":
        chunks = [Chunk.from_dict(cd) for cd in d.get("chunks", [])]
        return cls(doc_id=d["doc_id"], content_hash=d.get("content_hash", ""), chunks=chunks)

    def save_to_file(self, target_path: Path):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, source_path: Path) -> Optional["ChunkStore"]:
        if not source_path.exists():
            return None
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return cls.from_dict(d)
        except Exception:
            return None


def get_chunk_file_path(doc_id: str) -> Path:
    """Returns the JSON file path for a doc_id's chunk store."""
    clean_id = Path(doc_id).stem
    return CHUNKS_DIR / f"{clean_id}_chunks.json"


def get_or_build_chunk_store(doc_id: str, force_rebuild: bool = False) -> ChunkStore:
    """
    Retrieves the local ChunkStore for doc_id, building or refreshing it if:
    1. It does not exist on disk.
    2. The underlying PDF content hash has changed (stale-index protection).
    3. force_rebuild is True.
    """
    doc_path = _resolve_doc_path(doc_id)
    current_hash = compute_file_hash(doc_path)
    store_file = get_chunk_file_path(doc_id)

    if not force_rebuild and store_file.exists():
        cached_store = ChunkStore.load_from_file(store_file)
        if cached_store and cached_store.content_hash == current_hash and cached_store.doc_id == doc_id:
            return cached_store

    # Build fresh chunks from PDF pages
    reader = pypdf.PdfReader(str(doc_path))
    pages_dict: dict[int, str] = {}
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_dict[idx + 1] = text

    # Map headings to pages for section provenance if available
    page_sections: dict[int, str] = {}
    try:
        headings = list_headings(doc_id)
        for h in headings:
            h_page = h.get("page")
            h_title = h.get("title")
            if h_page and h_title and h_page not in page_sections:
                page_sections[int(h_page)] = str(h_title).strip()
    except Exception:
        pass

    chunks = chunk_document_pages(
        doc_id=doc_id,
        pages_dict=pages_dict,
        page_sections=page_sections,
    )

    store = ChunkStore(doc_id=doc_id, content_hash=current_hash, chunks=chunks)
    store.save_to_file(store_file)
    return store
