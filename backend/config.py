import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or current directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Document storage
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = DATA_DIR / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration
# Supports Gemini (default if GEMINI_API_KEY present) or OpenAI/compatible (if OPENAI_API_KEY present) or Mock
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini" if GEMINI_API_KEY else ("openai" if OPENAI_API_KEY else "auto"))
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash" if GEMINI_API_KEY else "gpt-4o-mini")

# Budget configuration
MAX_PRE_FINAL_CALLS = 6
