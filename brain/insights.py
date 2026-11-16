"""Auto-category + deadline/expiry dates nikalna."""
import re
from datetime import date

CATS = [
    ("Contract", r"contract|agreement|supply|purchase order|sales|arbitration|अनुबंध|इकरारनामा"),
    ("Tax / Notice", r"\bgst|gstin|income tax|\btds\b|notice|assessment|itr|return|नोटिस"),
    ("Property / Rent", r"rent|landlord|tenant|lease|sale deed|baina|property|plot|बैनामा|किराया|मकान"),
    ("Legal", r"court|suit|petition|advocate|legal opinion|affidavit|vakalat|न्यायालय|वाद"),
    ("Accounts", r"invoice|bill|voucher|ledger|receipt|balance sheet|payment|इनवॉइस"),
    ("Factory / Ops", r"machine|maintenance|plant|production|breakdown|service|vendor|inspection"),
]
MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
D1 = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")
D2 = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})[a-z]*\.?,?\s+(\d{4})\b")
KEY = re.compile(r"\b(due|expir\w*|valid\w*|renew\w*|deadline|last date|till|until|lock-in ends?)\b"
                 r"|समाप्ति|अंतिम तिथि|नवीनीकरण", re.I)


def classify(name, text):
    blob = (name + " " + text[:4000]).lower()
    best, score = "Other", 0
    for cat, pat in CATS:
        n = len(re.findall(pat, blob))
        if n > score:
            best, score = cat, n
    return best


def _dates(s):
    for m in D1.finditer(s):
        d, mo, y = map(int, m.groups())
        yield m.group(0), (y, mo, d)
    for m in D2.finditer(s):
        mo = MONTHS.get(m.group(2)[:3].lower())
        if mo:
            yield m.group(0), (int(m.group(3)), mo, int(m.group(1)))


def find_deadlines(pages):
    """pages: [(page, text)] -> [(page, iso_date, context)]"""
    out, seen = [], set()
    for pg, text in pages:
        for sent in re.split(r"(?<=[.!?।])\s+|\n", text):
            if not KEY.search(sent):
                continue
            for _raw, (y, mo, d) in _dates(sent):
                try:
                    iso = date(y, mo, d).isoformat()
                except ValueError:
                    continue
                if (pg, iso) not in seen:
                    seen.add((pg, iso))
                    out.append((pg, iso, sent.strip()[:220]))
    return out
