"""File se text nikalna. Return: list of (page_number, text)."""
import csv
from pathlib import Path


def _pdf(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            raise ValueError("PDF password-protected hai")
    pages = []
    for i, pg in enumerate(reader.pages, 1):
        try:
            t = pg.extract_text() or ""
        except Exception:
            t = ""
        pages.append([i, t])
    # Scanned pages ke liye optional OCR
    if any(len(t.strip()) < 20 for _, t in pages):
        _try_ocr(path, pages)
    return [(i, t) for i, t in pages]


def _try_ocr(path, pages):
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except Exception:
        return
    todo = [i for i, t in pages if len(t.strip()) < 20]
    for i in todo:
        try:
            img = convert_from_path(str(path), dpi=200, first_page=i, last_page=i)[0]
            try:
                txt = pytesseract.image_to_string(img, lang="eng+hin")
            except Exception:
                txt = pytesseract.image_to_string(img)
            pages[i - 1][1] = txt
        except Exception:
            pass


def _paginate(text, size=3000):
    """Docx/txt mein page nahi hota, isliye ~3000 char ka 'section' banate hain."""
    out, cur, n = [], "", 1
    for para in text.split("\n"):
        if len(cur) + len(para) > size and cur:
            out.append((n, cur)); n += 1; cur = ""
        cur += para + "\n"
    if cur.strip():
        out.append((n, cur))
    return out


def _docx(path):
    import docx
    d = docx.Document(str(path))
    parts = [p.text for p in d.paragraphs]
    for tb in d.tables:
        for row in tb.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells))
    return _paginate("\n".join(parts))


def _txt(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return _paginate(raw.decode(enc))
        except Exception:
            continue
    return []


def _csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig", errors="ignore") as f:
        for r in csv.reader(f):
            rows.append(" | ".join(r))
    return _paginate("\n".join(rows))


def _xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    pages = []
    for n, ws in enumerate(wb.worksheets, 1):
        lines = [f"[Sheet: {ws.title}]"]
        for row in ws.iter_rows(values_only=True):
            vals = [str(v) for v in row if v is not None]
            if vals:
                lines.append(" | ".join(vals))
        pages.append((n, "\n".join(lines)))
    return pages


def extract(path):
    ext = Path(path).suffix.lower()
    fn = {".pdf": _pdf, ".docx": _docx, ".txt": _txt, ".md": _txt,
          ".csv": _csv, ".xlsx": _xlsx}.get(ext)
    if not fn:
        raise ValueError(f"Format support nahi: {ext}")
    return fn(path)
