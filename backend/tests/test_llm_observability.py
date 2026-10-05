from unittest.mock import MagicMock
import json
import pytest
from backend.agent.controller import AgentController
from backend.agent.llm_client import (
    call_llm_with_metadata,
    set_gemini_client,
    set_openai_client,
    get_gemini_client,
    get_openai_client,
    LLMCallMetadata,
)


def test_gemini_api_success(monkeypatch):
    """
    Test Case A: Valid / configured API path.
    Mocks Gemini generate_content() to return successful content.
    Asserts mode == 'api' and provider == 'gemini'.
    """
    mock_client = MagicMock()
    mock_resp = MagicMock()
    # Planning response
    mock_resp.text = json.dumps({
        "intent": "factual",
        "entities": ["intelligent agent"],
        "attributes": ["definition"],
        "keywords": ["intelligent", "agent"],
        "strategy": "keyword_then_page",
    })
    mock_client.models.generate_content.return_value = mock_resp

    old_client = get_gemini_client()
    try:
        set_gemini_client(mock_client)
        monkeypatch.setenv("LLM_PROVIDER", "gemini")

        controller = AgentController(max_calls=6)
        res = controller.run("CSCI415009_V2.pdf", "What is an intelligent agent?")

        # 1. Planner LLM call
        plan_record = res["trace"][0]
        assert plan_record["call_type"] == "llm_planning"
        assert plan_record["llm_metadata"] is not None
        assert plan_record["llm_metadata"]["mode"] == "api"
        assert plan_record["llm_metadata"]["provider"] == "gemini"
        assert plan_record["llm_metadata"]["model"] is not None

        # 2. Final Answer LLM call
        final_record = [r for r in res["trace"] if r["call_type"] == "final_answer"][0]
        assert final_record["llm_metadata"] is not None
        assert final_record["llm_metadata"]["mode"] == "api"
        assert final_record["llm_metadata"]["provider"] == "gemini"
    finally:
        set_gemini_client(old_client)


def test_gemini_api_failure_falls_back_single_attempt(monkeypatch):
    """
    Test Case B: API failure.
    Mocks generate_content() to raise an exception.
    Asserts fallback is used, mode == 'rule_based_fallback', and no second API request occurs per step.
    """
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("429 Quota exceeded for model")

    old_client = get_gemini_client()
    try:
        set_gemini_client(mock_client)
        monkeypatch.setenv("LLM_PROVIDER", "gemini")

        controller = AgentController(max_calls=6)
        res = controller.run("CSCI415009_V2.pdf", "What is an intelligent agent?")

        # Exactly 2 API attempts were made across the run: 1 for planning, 1 for final answer (NO retries)
        assert mock_client.models.generate_content.call_count == 2

        # 1. Planner LLM record
        plan_record = res["trace"][0]
        assert plan_record["llm_metadata"]["mode"] == "rule_based_fallback"
        assert plan_record["llm_metadata"]["provider"] == "local"
        assert plan_record["llm_metadata"]["model"] is None
        assert "quota" in plan_record["llm_metadata"]["reason"].lower()

        # 2. Final Answer LLM record
        final_record = [r for r in res["trace"] if r["call_type"] == "final_answer"][0]
        assert final_record["llm_metadata"]["mode"] == "rule_based_fallback"
        assert final_record["llm_metadata"]["provider"] == "local"
        assert "quota" in final_record["llm_metadata"]["reason"].lower()

        # Deterministic fallback answer was produced
        assert "perceives and acts" in res["final_answer"].lower()
    finally:
        set_gemini_client(old_client)


def test_no_api_key_configured(monkeypatch):
    """
    Test Case C: No API key configured.
    Asserts local fallback is used, mode == 'rule_based_fallback', and no API call occurs.
    """
    old_gemini = get_gemini_client()
    old_openai = get_openai_client()
    try:
        set_gemini_client(None)
        set_openai_client(None)
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("OPENAI_API_KEY", "")

        text, meta = call_llm_with_metadata("System prompt", "User prompt Question: What is an intelligent agent?")
        assert meta.mode == "rule_based_fallback"
        assert meta.provider == "local"
        assert meta.model is None
        assert "No API key configured" in meta.reason
    finally:
        set_gemini_client(old_gemini)
        set_openai_client(old_openai)


def test_secret_safety_in_trace(monkeypatch):
    """
    Test Case D: Secret safety.
    Ensures that sensitive API keys or headers are NEVER exposed in trace or summaries.
    """
    secret_key = "AIzaSyD_TOP_SECRET_KEY_123456789"
    mock_client = MagicMock()
    # Simulate an error message that might accidentally contain the key
    mock_client.models.generate_content.side_effect = Exception(f"HTTP 403 Forbidden with key={secret_key}")

    old_client = get_gemini_client()
    try:
        set_gemini_client(mock_client)
        monkeypatch.setenv("LLM_PROVIDER", "gemini")

        controller = AgentController(max_calls=6)
        res = controller.run("CSCI415009_V2.pdf", "When was the term AI introduced?")

        trace_json = json.dumps(res["trace"])
        trace_summary = res["trace_summary"]

        assert secret_key not in trace_json
        assert secret_key not in trace_summary
        assert secret_key not in res["final_answer"]

        # Ensure sanitized message is present
        assert "key=***" in trace_json or "authentication failed" in trace_json or "401/403" in trace_json
    finally:
        set_gemini_client(old_client)
