import re
from .config import CHUNK_CHARS, CHUNK_OVERLAP

_SENT = re.compile(r"(?<=[.!?।])\s+|\n{2,}")


def chunk_page(text):
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    if len(text) <= CHUNK_CHARS:
        return [text]
    pieces = [p for p in _SENT.split(text) if p and p.strip()]
    chunks, cur = [], ""
    for p in pieces:
        if len(cur) + len(p) + 1 > CHUNK_CHARS and cur:
            chunks.append(cur.strip())
            cur = cur[-CHUNK_OVERLAP:] + " "
        cur += p + " "
        while len(cur) > CHUNK_CHARS * 2:       # bahut lamba bina full-stop wala text
            chunks.append(cur[:CHUNK_CHARS]); cur = cur[CHUNK_CHARS - CHUNK_OVERLAP:]
    if cur.strip():
        chunks.append(cur.strip())
    return chunks
