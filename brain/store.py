"""SQLite storage + in-memory BM25 index."""
import hashlib, math, shutil, sqlite3, threading, time
from collections import defaultdict, Counter
from pathlib import Path

from .config import DB_PATH, FILES
from .extract import extract
from .chunk import chunk_page
from .textutil import tokenize
from . import insights
from datetime import date

_lock = threading.RLock()


def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

db = _conn()
db.executescript("""
CREATE TABLE IF NOT EXISTS docs(
  id INTEGER PRIMARY KEY, name TEXT, stored TEXT, sha TEXT UNIQUE,
  pages INTEGER, chars INTEGER, added REAL, note TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS chunks(
  id INTEGER PRIMARY KEY, doc_id INTEGER REFERENCES docs(id) ON DELETE CASCADE,
  page INTEGER, text TEXT);
CREATE INDEX IF NOT EXISTS ix_chunks_doc ON chunks(doc_id);
CREATE TABLE IF NOT EXISTS deadlines(
  id INTEGER PRIMARY KEY, doc_id INTEGER REFERENCES docs(id) ON DELETE CASCADE,
  page INTEGER, due TEXT, context TEXT);
""")
try:
    db.execute("ALTER TABLE docs ADD COLUMN category TEXT")
except sqlite3.OperationalError:
    pass
db.commit()


class BM25:
    k1, b = 1.4, 0.75

    def __init__(self):
        self.reset()

    def reset(self):
        self.post = defaultdict(dict)   # term -> {chunk_id: tf}
        self.len = {}
        self.meta = {}                  # chunk_id -> doc_id
        self.total = 0

    def add(self, cid, doc_id, text):
        toks = tokenize(text)
        self.len[cid] = len(toks); self.meta[cid] = doc_id; self.total += len(toks)
        for t, n in Counter(toks).items():
            self.post[t][cid] = n

    def search(self, query, k=8, doc_ids=None):
        terms = tokenize(query, drop_stop=True) or tokenize(query)
        N = len(self.len)
        if not N or not terms:
            return [], terms
        avg = self.total / N
        scores = defaultdict(float)
        for t in set(terms):
            plist = self.post.get(t)
            if not plist:
                continue
            idf = math.log(1 + (N - len(plist) + 0.5) / (len(plist) + 0.5))
            for cid, tf in plist.items():
                if doc_ids and self.meta[cid] not in doc_ids:
                    continue
                dl = self.len[cid]
                scores[cid] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * dl / avg))
        # bonus: kitne alag query-terms mila (sab terms wale chunk upar)
        for cid in list(scores):
            hit = sum(1 for t in set(terms) if cid in self.post.get(t, {}))
            scores[cid] *= 1 + 0.35 * (hit - 1)
        top = sorted(scores.items(), key=lambda x: -x[1])[:k]
        return top, terms


index = BM25()


def rebuild_index():
    with _lock:
        index.reset()
        for r in db.execute("SELECT id, doc_id, text FROM chunks"):
            index.add(r["id"], r["doc_id"], r["text"])


rebuild_index()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def add_file(path, display_name=None):
    """Return dict(status=added|duplicate|empty|error, ...)."""
    path = Path(path)
    name = display_name or path.name
    try:
        sha = sha256(path)
        with _lock:
            dup = db.execute("SELECT id,name FROM docs WHERE sha=?", (sha,)).fetchone()
            if dup:
                return {"status": "duplicate", "name": name, "same_as": dup["name"]}
        pages = extract(path)
        total_chars = sum(len(t) for _, t in pages)
        if total_chars < 20:
            return {"status": "empty", "name": name,
                    "msg": "Text nahi mila (scanned PDF/photo hogi). OCR install karein."}
        stored = f"{sha[:12]}_{Path(name).name}"
        shutil.copy2(path, FILES / stored)
        with _lock:
            cur = db.execute(
                "INSERT INTO docs(name,stored,sha,pages,chars,added) VALUES(?,?,?,?,?,?)",
                (name, stored, sha, len(pages), total_chars, time.time()))
            doc_id = cur.lastrowid
            n = 0
            for pg, txt in pages:
                for ch in chunk_page(txt):
                    c = db.execute("INSERT INTO chunks(doc_id,page,text) VALUES(?,?,?)",
                                   (doc_id, pg, ch))
                    index.add(c.lastrowid, doc_id, ch); n += 1
            _analyze(doc_id, name, pages)
            db.commit()
        return {"status": "added", "name": name, "pages": len(pages), "chunks": n}
    except Exception as e:
        return {"status": "error", "name": name, "msg": str(e)}


def list_docs():
    return [dict(r) for r in db.execute(
        "SELECT id,name,pages,chars,added,COALESCE(category,'Other') category FROM docs ORDER BY added DESC")]


def delete_doc(doc_id):
    with _lock:
        r = db.execute("SELECT stored FROM docs WHERE id=?", (doc_id,)).fetchone()
        if not r:
            return False
        (FILES / r["stored"]).unlink(missing_ok=True)
        db.execute("DELETE FROM docs WHERE id=?", (doc_id,))
        db.commit()
    rebuild_index()
    return True


def get_doc(doc_id):
    return db.execute("SELECT * FROM docs WHERE id=?", (doc_id,)).fetchone()


def search(query, k=8, doc_ids=None):
    hits, terms = index.search(query, k, doc_ids)
    out = []
    for cid, score in hits:
        r = db.execute("""SELECT c.id,c.page,c.text,d.id AS doc_id,d.name
                          FROM chunks c JOIN docs d ON d.id=c.doc_id WHERE c.id=?""", (cid,)).fetchone()
        if r:
            out.append({**dict(r), "score": round(score, 2)})
    return out, terms


def _analyze(doc_id, name, pages):
    cat = insights.classify(name, " ".join(t for _, t in pages[:3]))
    db.execute("UPDATE docs SET category=? WHERE id=?", (cat, doc_id))
    for pg, iso, ctx in insights.find_deadlines(pages):
        db.execute("INSERT INTO deadlines(doc_id,page,due,context) VALUES(?,?,?,?)", (doc_id, pg, iso, ctx))


def _backfill():
    with _lock:
        for r in db.execute("SELECT id,name FROM docs WHERE category IS NULL").fetchall():
            pages = {}
            for c in db.execute("SELECT page,text FROM chunks WHERE doc_id=? ORDER BY id", (r["id"],)):
                pages[c["page"]] = pages.get(c["page"], "") + c["text"] + "\n"
            _analyze(r["id"], r["name"], sorted(pages.items()))
        db.commit()

_backfill()


def docs_by_category(cat):
    return {r["id"] for r in db.execute("SELECT id FROM docs WHERE category=?", (cat,))}


def stats():
    today = date.today()
    q = lambda sql, *a: db.execute(sql, a).fetchall()
    docs = q("SELECT COUNT(*) n, COALESCE(SUM(pages),0) p FROM docs")[0]
    cats = [dict(r) for r in q("SELECT COALESCE(category,'Other') cat, COUNT(*) n FROM docs GROUP BY 1 ORDER BY n DESC")]
    dl = []
    for r in q("""SELECT k.id,k.page,k.due,k.context,d.id doc_id,d.name,d.category FROM deadlines k
                  JOIN docs d ON d.id=k.doc_id ORDER BY k.due"""):
        left = (date.fromisoformat(r["due"]) - today).days
        dl.append({**dict(r), "days_left": left})
    recent = [dict(r) for r in q("SELECT id,name,pages,category,added FROM docs ORDER BY added DESC LIMIT 8")]
    return {"docs": docs["n"], "pages": docs["p"], "categories": cats, "recent": recent,
            "overdue": sum(1 for d in dl if d["days_left"] < 0),
            "soon": sum(1 for d in dl if 0 <= d["days_left"] <= 30),
            "deadlines": [d for d in dl if d["days_left"] >= -365][:40]}
