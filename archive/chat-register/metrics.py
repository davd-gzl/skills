#!/usr/bin/env python3
"""Prose metrics per condition over out2/*.json; code excluded, fake tool transcripts dropped."""
import glob, json, os, re, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
ART = re.compile(r"\b(a|an|the)\b", re.I)
FILL = re.compile(r"\b(just|really|basically|actually|simply|essentially|generally|quite|very)\b", re.I)
PLEAS = re.compile(r"\b(sure|certainly|of course|happy to|glad to|great question|absolutely|no problem)\b", re.I)
HEDGE = re.compile(r"\b(might|maybe|perhaps|probably|likely|i think|i believe|it seems|could be|possibly|tend to)\b", re.I)
FENCE = re.compile(r"```.*?```", re.S)
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")

def prose(text):
    t = FENCE.sub(" ", text)
    t = re.sub(r"`[^`]*`", " ", t)
    return t

def sentences(t):
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", t) if WORD.search(s)]

rows = {}
for f in sorted(glob.glob(os.path.join(HERE, "out2", "*.json"))):
    r = json.load(open(f))
    j = r.get("json") or {}
    text = j.get("result") or ""
    u = j.get("usage") or {}
    out_tok = (u["output_tokens"] - u.get("output_tokens_details", {}).get("thinking_tokens", 0)) if u.get("output_tokens") else None
    p = prose(text)
    fake = ("<function_calls>" in text) or ("<invoke" in text) or (r.get("rc") != 0) or (len(WORD.findall(p)) < 20 and "```" not in text)
    words = WORD.findall(p)
    n = max(len(words), 1)
    sents = sentences(p)
    avg_sent = n / max(len(sents), 1)
    rows.setdefault(r["cond"], []).append(dict(
        id=r["id"], rc=r["rc"], secs=r["secs"], tok=out_tok, words=len(words), all_words=len(WORD.findall(text)),
        art=100 * len(ART.findall(p)) / n, fill=100 * len(FILL.findall(p)) / n,
        pleas=len(PLEAS.findall(p)), hedge=100 * len(HEDGE.findall(p)) / n, sent=avg_sent,
        code=len(FENCE.findall(text)), fake=fake))

def med(c, k):
    v = [x[k] for x in rows[c] if x[k] is not None and not x["fake"]]
    return st.median(v) if v else float("nan")

conds = [c for c in ("none", "plugin", "rule", "rule2", "rule3", "rule4", "rule5") if c in rows]
print("| metric (median over prompts) | " + " | ".join(conds) + " |")
print("|---|" + "---|" * len(conds))
for k, lab in (("tok", "answer tokens"), ("words", "prose words, code excluded"), ("art", "articles per 100 words"),
               ("fill", "filler per 100 words"), ("hedge", "hedges per 100 words"), ("pleas", "pleasantries, count"),
               ("sent", "words per sentence"), ("code", "code blocks"), ("secs", "seconds")):
    print(f"| {lab} | " + " | ".join(f"{med(c, k):.1f}" for c in conds) + " |")
print()
print("| prompt | " + " | ".join(f"{c} words/articles per trial" for c in conds) + " |")
print("|---|" + "---|" * len(conds))
ids = sorted({x["id"] for c in rows for x in rows[c]})
for i in ids:
    cells = []
    for c in conds:
        m = [x for x in rows[c] if x["id"] == i]
        cells.append(" ; ".join(f"{x['words']}w/{x['art']:.1f}" + ("!" if x["fake"] else "") for x in m) if m else "-")
    print(f"| {i} | " + " | ".join(cells) + " |")
bad = [(c, x["id"], x["rc"]) for c in rows for x in rows[c] if x["rc"] != 0 or x["tok"] is None]
print("\nfailed:", bad or "none", "\nruns:", {c: len(rows[c]) for c in rows}, "\nexcluded as fake tool transcripts (!):", {c: sum(x["fake"] for x in rows[c]) for c in rows})
