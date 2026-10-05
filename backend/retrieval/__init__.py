"""
Local Lexical Chunk Retrieval Module for RAP_Comp.
Pure Python, zero embeddings, zero vector databases.
Provides deterministic document chunking, provenance tracking, and lexical scoring.
"""

from backend.retrieval.chunker import Chunk, chunk_page, chunk_document_pages
from backend.retrieval.chunk_store import ChunkStore, get_or_build_chunk_store
from backend.retrieval.lexical_retriever import LexicalRetriever, LexicalSearchResult

__all__ = [
    "Chunk",
    "chunk_page",
    "chunk_document_pages",
    "ChunkStore",
    "get_or_build_chunk_store",
    "LexicalRetriever",
    "LexicalSearchResult",
]
