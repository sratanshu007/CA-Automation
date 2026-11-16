import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _load_env():
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

DATA = ROOT / "data"
FILES = DATA / "files"
INBOX = DATA / "inbox"
DB_PATH = DATA / "brain.db"
for p in (FILES, INBOX):
    p.mkdir(parents=True, exist_ok=True)

APP_USER = os.getenv("APP_USER", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
API_KEY = ANTHROPIC_API_KEY
MODEL = ANTHROPIC_MODEL

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# off | gemini | claude | ollama
def _detect_provider():
    p = os.getenv("LLM_PROVIDER")
    if p:
        return p.strip().lower()
    if GEMINI_API_KEY:
        return "gemini"
    if ANTHROPIC_API_KEY:
        return "claude"
    return "off"

PROVIDER = _detect_provider()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5001"))

CHUNK_CHARS = 900
CHUNK_OVERLAP = 150
SUPPORTED = {".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx"}
