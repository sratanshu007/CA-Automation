"""AI jawab: Gemini / Claude (online) ya Ollama (poora offline, local model). Kuch na ho to sirf search."""
import json, urllib.request, urllib.error
from .config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    API_KEY, MODEL, PROVIDER, OLLAMA_URL, OLLAMA_MODEL
)

SYSTEM = """Tum ek office Document Brain assistant ho (CA / lawyer / factory ke documents).
Sirf diye gaye SOURCES ke aadhar par jawab do. Apni taraf se kuch mat jodo.
Har fact ke baad uska source number [1], [2] jaise likho.
Agar sources mein jawab nahi hai to saaf bolo: "Diye gaye documents mein yeh jankari nahi mili."
Jis bhasha mein user ne sawal poocha (Hindi / Hinglish / English) usi mein jawab do. Chhota aur seedha rakho.
Amount, dates, party ke naam bilkul wahi likho jo source mein hain."""

LOCAL = PROVIDER == "ollama"


def enabled():
    if PROVIDER == "gemini":
        return bool(GEMINI_API_KEY)
    elif PROVIDER == "claude":
        return bool(ANTHROPIC_API_KEY or API_KEY)
    elif PROVIDER == "ollama":
        return True
    return False


def label():
    if not enabled():
        return ""
    labels = {
        "gemini": f"Gemini · {GEMINI_MODEL} (online)",
        "claude": f"Claude · {ANTHROPIC_MODEL} (online)",
        "ollama": f"Local · {OLLAMA_MODEL} (offline)"
    }
    return labels.get(PROVIDER, "")


def max_sources():
    return 4 if LOCAL else 6          # chhota model = kam context = tez jawab


def _post(url, payload, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _call(system, user, max_tokens=900):
    if LOCAL:
        d = _post(f"{OLLAMA_URL}/api/chat", {
            "model": OLLAMA_MODEL, "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 6144, "num_predict": max_tokens},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
            {}, 300)
        return d.get("message", {}).get("content", "")
    elif PROVIDER == "gemini":
        model_name = GEMINI_MODEL.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": max_tokens
            }
        }
        if system:
            payload["system_instruction"] = {
                "parts": [{"text": system}]
            }
        headers = {"x-goog-api-key": GEMINI_API_KEY}
        d = _post(url, payload, headers, 60)
        candidates = d.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts if "text" in p)
        return ""
    elif PROVIDER == "claude":
        claude_key = ANTHROPIC_API_KEY or API_KEY
        claude_model = ANTHROPIC_MODEL or MODEL
        d = _post("https://api.anthropic.com/v1/messages",
                  {"model": claude_model, "max_tokens": max_tokens, "system": system,
                   "messages": [{"role": "user", "content": user}]},
                  {"x-api-key": claude_key, "anthropic-version": "2023-06-01"}, 60)
        return "".join(b.get("text", "") for b in d.get("content", []))
    return ""


def ollama_status():
    """Return (ok, message). Startup pe check."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as r:
            names = [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception:
        return False, "Ollama chalta nahi mila. Ollama install karke chalao."
    if not any(n == OLLAMA_MODEL or n.startswith(OLLAMA_MODEL + ":") or n.split(":")[0] == OLLAMA_MODEL for n in names):
        return False, f"Model '{OLLAMA_MODEL}' nahi mila. Chalao: ollama pull {OLLAMA_MODEL}"
    return True, "Ollama ready"


def keywords(question):
    """Hinglish sawal -> keywords. Local model pe skip (tezi ke liye)."""
    if LOCAL:
        return ""
    try:
        return _call("Convert the user's question into 4-10 search keywords for a document search "
                     "(names, document types, amounts, dates). Include English synonyms and the original "
                     "words. Output only space-separated keywords.", question, 80).strip()
    except Exception:
        return ""


def answer(question, hits):
    ctx = "\n\n".join(f"[{i}] ({h['name']}, page {h['page']})\n{h['text']}" for i, h in enumerate(hits, 1))
    try:
        return _call(SYSTEM, f"SOURCES:\n{ctx}\n\nSAWAL: {question}")
    except urllib.error.HTTPError as e:
        err_msg = ""
        try:
            err_data = json.loads(e.read().decode())
            err_msg = err_data.get("error", {}).get("message", "")
        except Exception:
            pass
        if err_msg:
            return f"(AI error {e.code}: {err_msg})"
        return f"(AI error {e.code}: settings / model check karein)"
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        return "(AI se connect nahi hua. Neeche ke sources dekhein. Ollama chal raha hai?)" if LOCAL else "(Internet / API nahi mila. Neeche ke sources dekhein.)"
    except Exception as e:
        return f"(AI jawab nahi aaya: {e})"
