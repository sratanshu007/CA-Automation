import re

TOKEN_RE = re.compile(r"[A-Za-z0-9\u0900-\u097F\u0966-\u096F]+")

# English + Hinglish + Hindi stopwords (sawal ke faltu shabd)
STOP = set("""
a an the is are was were be been of in on at to for from by with and or not this that these those it its as
what which who whom whose when where how why did do does done can could should would will shall may
tell show give find me my our us your you i we he she they them his her their
ka ki ke ko se me mein par pe hai hain tha thi the ho hoga hogi kya kaun kab kahan kaise kyun kyu
aur ya bhi to toh nahi nahin is us ye yeh wo woh iska uska unka isme usme
kitne kitna kitni din pichle pichla pichli agle agla saal sal wala wali wale batao bata do dikhao dikha dijiye
का की के को से में पर है हैं था थी थे हो क्या कौन कब कहाँ कैसे और या भी तो नहीं यह वह इस उस
""".split())


def tokenize(text, drop_stop=False):
    toks = []
    for t in TOKEN_RE.findall(text.lower()):
        if len(t) > 3 and t.isascii() and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]                      # light plural stemming: contracts -> contract
        if drop_stop and (t in STOP or len(t) < 2):
            continue
        toks.append(t)
    return toks
