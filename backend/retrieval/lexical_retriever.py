import re
import math
from dataclasses import dataclass, field
from typing import Optional, Any
from backend.retrieval.chunk_store import ChunkStore
from backend.retrieval.chunker import Chunk


@dataclass
class LexicalSearchResult:
    chunk_id: str
    page: int
    score: float
    matched_terms: list[str] = field(default_factory=list)
    covered_entities: list[str] = field(default_factory=list)
    covered_attributes: list[str] = field(default_factory=list)
    section: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "page": self.page,
            "score": round(self.score, 3),
            "matched_terms": self.matched_terms,
            "covered_entities": self.covered_entities,
            "covered_attributes": self.covered_attributes,
            "section": self.section,
        }


def _stem(token: str) -> str:
    """Lightweight deterministic English stemmer for root matching."""
    t = token.lower()
    for suffix in ["ization", "ational", "tional", "iveness", "fulness", "ousness", "ement", "ities", "ation", "ality", "ness", "able", "ible", "ical", "ing", "ies", "ity", "ous", "ive", "ful", "less", "est", "ist", "ism", "ize", "ise", "ed", "al", "ly", "er", "es", "s"]:
        if t.endswith(suffix) and len(t) - len(suffix) >= 3:
            return t[:-len(suffix)]
    return t


def _tokenize(text: str) -> list[str]:
    """Extracts normalized alphanumeric tokens (length >= 2, plus special tokens like a* or ai)."""
    tokens = []
    for raw_tok in re.findall(r"\b[a-zA-Z0-9_\*]{2,}\b", text.lower()):
        tok = raw_tok.strip()
        if tok:
            tokens.append(tok)
    return tokens


class LexicalRetriever:
    """
    Deterministic Lexical Chunk Retriever for RAP_Comp.
    Implements lightweight BM25 / TF-IDF scoring with root stemming and entity-attribute co-occurrence detection.
    Zero embeddings, zero vector databases.
    """
    def __init__(self, chunk_store: ChunkStore, k1: float = 1.5, b: float = 0.75):
        self.chunk_store = chunk_store
        self.chunks = chunk_store.get_chunks()
        self.k1 = k1
        self.b = b
        self.doc_len: dict[str, int] = {}
        self.avg_doc_len: float = 1.0
        self.doc_freq: dict[str, int] = {}
        self.stemmed_doc_freq: dict[str, int] = {}
        self.total_docs: int = max(1, len(self.chunks))
        self._build_lexical_index()

    def _build_lexical_index(self):
        total_len = 0
        self.doc_freq = {}
        self.stemmed_doc_freq = {}
        self.doc_len = {}

        for chunk in self.chunks:
            tokens = _tokenize(chunk.text)
            c_len = len(tokens)
            self.doc_len[chunk.chunk_id] = c_len
            total_len += c_len

            unique_toks = set(tokens)
            for tok in unique_toks:
                self.doc_freq[tok] = self.doc_freq.get(tok, 0) + 1
                st = _stem(tok)
                self.stemmed_doc_freq[st] = self.stemmed_doc_freq.get(st, 0) + 1

        self.avg_doc_len = (total_len / self.total_docs) if self.total_docs > 0 else 1.0

    def _compute_idf(self, term: str) -> float:
        st = _stem(term)
        df = max(self.doc_freq.get(term, 0), self.stemmed_doc_freq.get(st, 0))
        # Standard Robertson-Spärck Jones BM25 IDF
        return math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))

    def search_chunks(
        self,
        query_terms: list[str],
        entities: Optional[list[str]] = None,
        attributes: Optional[list[str]] = None,
        top_k: int = 15,
    ) -> list[LexicalSearchResult]:
        """
        Executes lexical chunk matching over the local store.
        Evaluates exact phrase matches, BM25 token frequencies, stemming roots, and entity-attribute co-occurrences.
        """
        entities = [e.strip().lower() for e in (entities or []) if e.strip()]
        attributes = [a.strip().lower() for a in (attributes or []) if a.strip()]
        query_terms = [q.strip().lower() for q in query_terms if q.strip()]

        # Collect unique tokens to evaluate
        search_tokens = set()
        for qt in query_terms + entities + attributes:
            search_tokens.update(_tokenize(qt))

        results: list[LexicalSearchResult] = []

        for chunk in self.chunks:
            chunk_lower = chunk.text.lower()
            chunk_tokens = _tokenize(chunk.text)
            chunk_token_counts: dict[str, int] = {}
            chunk_stem_counts: dict[str, int] = {}

            for t in chunk_tokens:
                chunk_token_counts[t] = chunk_token_counts.get(t, 0) + 1
                st = _stem(t)
                chunk_stem_counts[st] = chunk_stem_counts.get(st, 0) + 1

            chunk_len = self.doc_len.get(chunk.chunk_id, len(chunk_tokens))
            score = 0.0
            matched_terms: list[str] = []
            matched_entities: list[str] = []
            matched_attributes: list[str] = []

            # 1. BM25 Token and Stem Matching
            for tok in search_tokens:
                st = _stem(tok)
                tf = chunk_token_counts.get(tok, 0)
                if tf == 0:
                    tf = chunk_stem_counts.get(st, 0)

                if tf > 0:
                    idf = self._compute_idf(tok)
                    tf_weight = (tf * (self.k1 + 1.0)) / (
                        tf + self.k1 * (1.0 - self.b + self.b * (chunk_len / self.avg_doc_len))
                    )
                    score += idf * tf_weight
                    if tok not in matched_terms:
                        matched_terms.append(tok)

            # 2. Exact and Stemmed Phrase Matching for Entities
            for ent in entities:
                ent_tokens = _tokenize(ent)
                if len(ent_tokens) > 1 and ent in chunk_lower:
                    score += 6.0  # Exact multi-word entity match
                    if ent not in matched_entities:
                        matched_entities.append(ent)
                elif all(_stem(t) in chunk_stem_counts for t in ent_tokens if len(t) > 2):
                    score += 4.0  # Stemmed entity match
                    if ent not in matched_entities:
                        matched_entities.append(ent)
                elif ent in chunk_lower:
                    if ent not in matched_entities:
                        matched_entities.append(ent)

            # 3. Exact and Stemmed Matching for Attributes
            for attr in attributes:
                attr_tokens = _tokenize(attr)
                if len(attr_tokens) > 1 and attr in chunk_lower:
                    score += 5.0  # Exact multi-word attribute match
                    if attr not in matched_attributes:
                        matched_attributes.append(attr)
                elif any(_stem(t) in chunk_stem_counts for t in attr_tokens if len(t) > 2):
                    score += 3.5  # Stemmed attribute match
                    if attr not in matched_attributes:
                        matched_attributes.append(attr)
                elif attr in chunk_lower:
                    if attr not in matched_attributes:
                        matched_attributes.append(attr)

            # 4. Entity × Attribute Co-occurrence Pair Bonus
            for ent in matched_entities:
                for attr in matched_attributes:
                    score += 8.0  # Significant bonus: chunk covers both entity and attribute

            # 5. Section / Heading relevance bonus
            if chunk.section:
                sec_lower = chunk.section.lower()
                for ent in entities:
                    if ent in sec_lower or _stem(ent) in sec_lower:
                        score += 5.0
                for attr in attributes:
                    if attr in sec_lower or _stem(attr) in sec_lower:
                        score += 3.0

            if score > 0.0:
                results.append(
                    LexicalSearchResult(
                        chunk_id=chunk.chunk_id,
                        page=chunk.page,
                        score=score,
                        matched_terms=matched_terms,
                        covered_entities=matched_entities,
                        covered_attributes=matched_attributes,
                        section=chunk.section,
                    )
                )

        # Sort descending by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def aggregate_to_candidate_pages(
        self, search_results: list[LexicalSearchResult]
    ) -> list[dict[str, Any]]:
        """
        Aggregates chunk-level search results into ranked candidate pages.
        Returns a list of dicts with page, aggregated score, matched terms, and covered entities/attributes.
        """
        page_groups: dict[int, list[LexicalSearchResult]] = {}
        for res in search_results:
            if res.page not in page_groups:
                page_groups[res.page] = []
            page_groups[res.page].append(res)

        aggregated: list[dict[str, Any]] = []

        for page, chunk_res_list in page_groups.items():
            sorted_scores = sorted([r.score for r in chunk_res_list], reverse=True)
            page_score = sorted_scores[0]
            if len(sorted_scores) > 1:
                page_score += 0.3 * sum(sorted_scores[1:])

            all_matched_terms = set()
            all_entities = set()
            all_attributes = set()
            sections = set()

            for r in chunk_res_list:
                all_matched_terms.update(r.matched_terms)
                all_entities.update(r.covered_entities)
                all_attributes.update(r.covered_attributes)
                if r.section:
                    sections.add(r.section)

            aggregated.append({
                "page": page,
                "score": round(page_score, 3),
                "matched_terms": list(all_matched_terms),
                "covered_entities": list(all_entities),
                "covered_attributes": list(all_attributes),
                "sections": list(sections),
                "chunk_count": len(chunk_res_list),
            })

        aggregated.sort(key=lambda x: x["score"], reverse=True)
        return aggregated
