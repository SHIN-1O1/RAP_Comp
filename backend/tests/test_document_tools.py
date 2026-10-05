import pytest
from pathlib import Path
from backend.agent.budget import CallBudget
from backend.agent.logger import CallLogger
from backend.tools.tool_wrapper import execute_tool
from backend.tools.document_tools import (
    list_documents,
    list_headings,
    search_keyword,
    get_page,
)


def test_list_documents():
    docs = list_documents()
    assert isinstance(docs, list)
    assert len(docs) > 0
    # Must only contain metadata
    first_doc = docs[0]
    assert "doc_id" in first_doc
    assert "page_count" in first_doc
    assert "content" not in first_doc


def test_list_headings():
    docs = list_documents()
    doc_id = docs[0]["doc_id"]
    headings = list_headings(doc_id)
    assert isinstance(headings, list)
    for h in headings:
        assert "title" in h
        assert "page" in h


def test_search_keyword_and_get_page():
    docs = list_documents()
    doc_id = docs[0]["doc_id"]
    
    # Search for a common term e.g. "the"
    matching_pages = search_keyword(doc_id, "the")
    assert isinstance(matching_pages, list)
    if matching_pages:
        assert all(isinstance(p, int) for p in matching_pages)
        page_num = matching_pages[0]
        text = get_page(doc_id, page_num)
        assert isinstance(text, str)
        assert len(text) > 0
        assert "the" in text.lower()


def test_tool_wrapper_tracking():
    budget = CallBudget(max_calls=6)
    logger = CallLogger()
    docs = execute_tool("list_documents", {}, budget, logger)
    assert budget.used == 1
    assert budget.remaining == 5
    assert len(logger.records) == 1
    rec = logger.records[0]
    assert rec.call_number == 1
    assert rec.tool_name == "list_documents"
    assert rec.success is True
    assert rec.budget_remaining == 5
