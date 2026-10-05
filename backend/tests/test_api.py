import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_get_documents_endpoint():
    res = client.get("/api/documents")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    assert len(docs) > 0


def test_ask_endpoint():
    docs = client.get("/api/documents").json()
    doc_id = docs[0]["doc_id"]
    res = client.post("/api/ask", json={"doc_id": doc_id, "question": "What is the course number or title?"})
    assert res.status_code == 200
    data = res.json()
    assert "final_answer" in data
    assert data["calls_used"] <= 6
    assert "trace" in data
    assert len(data["trace"]) > 0
