# 🧠 CA Automatio

Hazaaron PDF / Word / Excel / TXT upload karo aur Hindi, Hinglish ya English mein poocho:
"Sharma Leather ka contract kya tha?" -> jawab + **kaunsi file, kaunsa page** (click karke seedha khulta hai).

## Naya kya hai (v2 Dashboard)
- 📊 **Dashboard:** total documents, pages, aur deadline counters
- ⏰ **Deadline alerts:** documents mein "valid until / due / expiry / renewal" ke saath likhi dates apne aap nikalti hain (din baaki, ya kitne din pehle nikal gayi)
- 🏷️ **Auto-category:** Contract, Tax/Notice, Property/Rent, Legal, Accounts, Factory/Ops
- 💬 **Poochho:** category chip chunke sirf us type ke documents mein search
- 📁 **Documents:** naam se filter, delete, click karke file khulti hai
- Dark mode aur mobile par bhi chalta hai

## Chalane ka tarika (5 minute)

**Windows:** `run.bat` pe double-click.
**Mac/Linux:** `./run.sh`
(Pehli baar Python 3.10+ chahiye: python.org se install karein.)

Browser mein khulega: http://127.0.0.1:5001

## Pehli baar demo
```
pip install reportlab
python make_samples.py      # 6 nakli Kanpur-style documents banata hai
python ingest.py samples
```
Phir poochho: `Verma Textiles ka advance kitna tha` / `GST notice tax difference` / `बैनामा विवाद`

## Apne documents daalne ke 3 tareeke
1. Browser mein drag & drop (5-5 ke batch mein upload hota hai)
2. Files ko `data/inbox/` mein daalo -> "inbox scan" button
3. Poora folder: `python ingest.py "D:\Clients"` (sabse tez, hazaaron files ke liye)

Duplicate files (same content) apne aap skip ho jaati hain.

## 🔌 Poora OFFLINE AI jawab (Ollama)
Internet ke bina bhi likha hua jawab chahiye? Local model chalao:

1. **Ollama install karo** (ollama.com se, ek baar internet chahiye). Windows/Mac/Linux teeno par.
2. **Model download karo** (ek baar, kuch GB):
   ```
   ollama pull qwen2.5:7b
   ```
3. `.env` mein likho:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=qwen2.5:7b
   ```
4. App chalao. Terminal mein dikhega `AI jawab: LOCAL/OFFLINE -> Ollama ready`. Uske baad internet band kar sakte ho.

**Computer ke hisaab se model** (naam badalte rehte hain, ollama.com/library dekho):
| RAM | Model idea | Speed |
|---|---|---|
| 8 GB | `qwen2.5:3b` ya `gemma3:4b` | theek, Hindi kamzor |
| 16 GB | `qwen2.5:7b` ya `gemma3:12b` | achha, 20-60 sec/jawab (CPU) |
| GPU (8GB+ VRAM) | `qwen2.5:14b` | tez aur behtar |

Dhyan rakho: local model Claude se kamzor hai, khaaskar Hinglish mein, aur kabhi galat ya adhura jawab de sakta hai. Isliye sources hamesha dikhte hain, unhe verify karo. Agar `ollama pull` ke baad bhi model nahi mile, startup message batayega.

## Mode
| Mode | Kaise | Kya milta hai |
|---|---|---|
| **Search mode** (default, free, offline) | kuch nahi karna | Best matching passages + file + page + highlight |
| **AI mode (Gemini)** | `.env` mein `GEMINI_API_KEY` daalo | Tez aur behtar Hindi/Hinglish jawab `[1][2]` citations ke saath (Free key: [Google AI Studio](https://aistudio.google.com)) |
| **AI mode (Claude)** | `.env` mein `ANTHROPIC_API_KEY` daalo | Claude se likha hua jawab citations ke saath |
| **AI mode (Ollama)** | `LLM_PROVIDER=ollama` | 100% offline local AI model bina internet |

Bina key ke bhi poora app chalta hai. AI mode mein sirf top passages model ko jaate hain, poori files nahi.

## Office mein sabke liye (LAN)
`.env` mein:
```
HOST=0.0.0.0
APP_PASSWORD=koi-mazboot-password
```
Phir office ke dusre computer se `http://<is-pc-ka-IP>:5000`. **Password zaroor lagao**, client ka data hai.

## Scanned PDF / photo wale documents (OCR)
Kanpur ke bahut se purane documents scanned hote hain. Tab:
1. Tesseract install karo (Hindi pack `hin` ke saath)
2. `pip install pytesseract pdf2image pillow` (+ Poppler)
Uske baad scanned pages apne aap OCR hoke index honge. Bina OCR ke aise files "Text nahi mila" dikhayengi.

## Structure
```
app.py            web server (Flask)
ingest.py         folder bulk-index
brain/extract.py  PDF/DOCX/XLSX/CSV/TXT reader (+ optional OCR)
brain/chunk.py    text ko tukdon mein todna
brain/store.py    SQLite + BM25 search (Hindi/English)
brain/llm.py      optional Claude jawab
templates/index.html  UI
```

## Limits (sach-sach)
- Search keyword-based (BM25) hai: shabd milna chahiye. AI mode isko Hinglish -> English/Hindi keywords se behtar banata hai.
- ~1 lakh pages tak aaram se chalega (index RAM mein). Usse bade ke liye vector DB/Postgres chahiye.
- Hindi stemming nahi hai ("बैनामा" vs "बैनामे" alag shabd).
- AI jawab hamesha source se verify karein, khaaskar legal/tax mein.

## Aage badhane ke idea (paise wale features)
Party-wise folder filter, expiry/renewal date alerts, WhatsApp bot se sawal, user login + audit log, har client ka alag workspace.
