import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import DOCS_DIR, PROJECT_ROOT
from backend.models.schemas import (
    AskRequest,
    AskResponse,
    DocumentMetadataSchema,
)
from backend.tools.document_tools import list_documents
from backend.agent.controller import AgentController

app = FastAPI(
    title="Budgeted Document QA Agent",
    description="Agentic QA harness enforcing hard 6-call pre-final budget and strict evidence-only answering.",
    version="1.0.0",
)

# Enable CORS for local Vite frontend dev server and direct browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "budgeted-doc-agent"}


@app.get("/api/documents", response_model=list[DocumentMetadataSchema])
def get_documents():
    """List available documents with metadata only (no document text)."""
    return list_documents()


@app.post("/api/upload", response_model=DocumentMetadataSchema)
async def upload_document(file: UploadFile = File(...)):
    """Accepts an unseen PDF upload for live demonstration."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")

    target_path = DOCS_DIR / file.filename
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded PDF: {str(e)}")

    # Retrieve metadata using document tools
    all_docs = list_documents()
    for doc in all_docs:
        if doc["filename"] == file.filename or doc["doc_id"] == file.filename:
            return doc

    return {
        "doc_id": file.filename,
        "title": file.filename,
        "page_count": 0,
        "filename": file.filename,
        "size_bytes": target_path.stat().st_size,
    }


@app.post("/api/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    """
    Executes question answering under the strict 6-call pre-final budget.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not req.doc_id or not req.doc_id.strip():
        raise HTTPException(status_code=400, detail="Document ID must be provided.")

    controller = AgentController(max_calls=6)
    result = controller.run(doc_id=req.doc_id, question=req.question.strip())
    return result


# Mount frontend static distribution if built
dist_dir = PROJECT_ROOT / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
