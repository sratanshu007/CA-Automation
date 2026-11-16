import os, tempfile, secrets
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file, Response, abort
from werkzeug.utils import secure_filename

from brain import config, store, llm

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 ** 3   # 2 GB per request


@app.before_request
def _auth():
    if not config.APP_PASSWORD:
        return
    a = request.authorization
    ok = (a and secrets.compare_digest(a.username or "", config.APP_USER)
          and secrets.compare_digest(a.password or "", config.APP_PASSWORD))
    if not ok:
        return Response("Login zaroori hai", 401, {"WWW-Authenticate": 'Basic realm="Document Brain"'})


@app.get("/")
def home():
    return render_template("index.html", ai=llm.enabled(), ai_label=llm.label())


@app.get("/api/stats")
def stats():
    return jsonify(store.stats())


@app.get("/api/docs")
def docs():
    return jsonify(store.list_docs())


@app.post("/api/upload")
def upload():
    results = []
    for f in request.files.getlist("files"):
        name = Path(f.filename or "file").name
        if Path(name).suffix.lower() not in config.SUPPORTED:
            results.append({"status": "error", "name": name, "msg": "Format support nahi"})
            continue
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / secure_filename(name) if secure_filename(name) else Path(td) / "file"
            f.save(tmp)
            results.append(store.add_file(tmp, display_name=name))
    return jsonify(results)


@app.post("/api/scan-inbox")
def scan_inbox():
    """data/inbox folder (ya subfolders) ke saare naye files index karo."""
    results = []
    for p in sorted(config.INBOX.rglob("*")):
        if p.is_file() and p.suffix.lower() in config.SUPPORTED:
            results.append(store.add_file(p))
    return jsonify(results)


@app.post("/api/ask")
def ask():
    body = request.get_json(force=True)
    q = (body.get("question") or "").strip()
    if not q:
        return jsonify({"error": "Sawal likhein"}), 400
    doc_ids = set(body.get("doc_ids") or []) or None
    if body.get("category"):
        doc_ids = (doc_ids or set()) | store.docs_by_category(body["category"]) if not doc_ids else \
            doc_ids & store.docs_by_category(body["category"])
        if not doc_ids:
            return jsonify({"answer": None, "hits": [], "terms": [], "ai": llm.enabled()})
    search_q = q
    if llm.enabled():
        search_q = q + " " + llm.keywords(q)
    hits, terms = store.search(search_q, k=int(body.get("k", llm.max_sources())), doc_ids=doc_ids)
    answer = None
    if hits and llm.enabled():
        answer = llm.answer(q, hits)
    return jsonify({"answer": answer, "hits": hits, "terms": terms, "ai": llm.enabled()})


@app.get("/file/<int:doc_id>")
def file(doc_id):
    d = store.get_doc(doc_id)
    if not d:
        abort(404)
    return send_file(config.FILES / d["stored"], download_name=d["name"],
                     as_attachment=not d["name"].lower().endswith(".pdf"))


@app.delete("/api/docs/<int:doc_id>")
def delete(doc_id):
    return jsonify({"ok": store.delete_doc(doc_id)})


if __name__ == "__main__":
    print(f"\n  Document Brain chal raha hai -> http://{config.HOST}:{config.PORT}")
    if llm.LOCAL:
        ok, msg = llm.ollama_status()
        print("  AI jawab: LOCAL/OFFLINE ->", msg, "" if ok else "(tab tak sirf search chalega)")
    elif llm.enabled():
        print(f"  AI jawab: {llm.label()}")
    else:
        print("  AI jawab: OFF (sirf search + source)")
    print()
    app.run(host=config.HOST, port=config.PORT, debug=False, threaded=True)
