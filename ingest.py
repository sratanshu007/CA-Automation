"""Command line se poora folder index karo:
    python ingest.py "D:\\Clients\\Contracts"
    python ingest.py            # data/inbox folder
"""
import sys
from pathlib import Path
from brain import config, store

root = Path(sys.argv[1]) if len(sys.argv) > 1 else config.INBOX
files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in config.SUPPORTED]
print(f"{len(files)} files mile in {root}")
for i, p in enumerate(files, 1):
    r = store.add_file(p)
    extra = r.get("msg") or (f"{r.get('pages')} pages" if r["status"] == "added" else "")
    print(f"[{i}/{len(files)}] {r['status']:9} {p.name}  {extra}")
print("Ho gaya. Ab app.py chalao.")
