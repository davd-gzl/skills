#!/usr/bin/env python3
"""Blind readability judge: per prompt and trial, every clean answer, labels hidden, order shuffled."""
import glob, json, os, random, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "judged"); os.makedirs(OUT, exist_ok=True)
CONDS = sys.argv[1].split(",") if sys.argv[1:] else ["none", "plugin", "rule", "rule2", "rule3"]
prompts = {p["id"]: p["prompt"] for p in json.load(open(os.path.join(HERE, "prompts.json")))["prompts"]}
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*"); FENCE = re.compile(r"```.*?```", re.S)

def clean(text, rc):
    p = FENCE.sub(" ", text)
    return not (("<function_calls>" in text) or ("<invoke" in text) or rc != 0 or (len(WORD.findall(p)) < 20 and "```" not in text))

RUBRIC = """You are judging answers to a developer's question for READABILITY, not length.
Score each answer on two scales, 1 to 5:
- pass1: a competent developer understands it on a single left-to-right read. 5 = nothing re-read, no ambiguity from dropped words, step order clear. 1 = must re-read or guess.
- substance: technical content is complete and correct for the question. 5 = nothing missing, 1 = hollow.
Terse is not a fault and long is not a merit; only the two scales count. Ignore markdown polish.
Then rank all answers from most to least readable overall (pass1 first, substance as tiebreak).
Reply with JSON only: {"scores": {"A": {"pass1": n, "substance": n}, ...}, "rank": ["A", ...], "note": "one sentence on what hurt readability most"}"""

def judge(pid, trial):
    outp = os.path.join(OUT, f"{pid}__t{trial}.json")
    if os.path.exists(outp):
        return
    items = []
    for c in CONDS:
        f = os.path.join(HERE, "out2", f"{pid}__{c}__t{trial}.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f)); t = (r.get("json") or {}).get("result", "")
        if clean(t, r["rc"]):
            items.append((c, t))
    if len(items) < 2:
        return
    random.Random(f"{pid}{trial}").shuffle(items)
    labels = [chr(65 + i) for i in range(len(items))]
    body = f"QUESTION:\n{prompts[pid]}\n\n" + "\n\n".join(f"===== ANSWER {l} =====\n{t}" for l, (c, t) in zip(labels, items))
    cmd = ["claude", "-p", "--model", "fable", "--effort", "high", "--tools", "", "--strict-mcp-config",
           "--disable-slash-commands", "--setting-sources", "", "--no-session-persistence", "--output-format", "json",
           "--append-system-prompt", RUBRIC, body]
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE") and k != "CLAUDE_CODE_ENTRYPOINT"}
    r = subprocess.run(cmd, cwd=os.path.join(HERE, "work"), env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    rec = {"id": pid, "trial": trial, "map": {l: c for l, (c, t) in zip(labels, items)}, "rc": r.returncode, "raw": r.stdout[-6000:]}
    try:
        res = json.loads(r.stdout)["result"]
        rec["result"] = res
        try:
            rec["verdict"] = json.loads(re.search(r"\{.*\}", res, re.S).group(0))
        except Exception:
            scores = {l: {"pass1": int(a), "substance": int(b)} for l, a, b in
                      re.findall(r'"([A-Z])":\s*\{"pass1":\s*(\d),\s*"substance":\s*(\d)\}', res)}
            rank = json.loads(re.search(r'"rank":\s*(\[[^\]]*\])', res).group(1))
            note = re.search(r'"note":\s*"(.*?)"\s*\}?\s*$', res, re.S)
            rec["verdict"] = {"scores": scores, "rank": rank, "note": note.group(1) if note else "", "lenient": True}
    except Exception as e:
        rec["error"] = str(e)
    json.dump(rec, open(outp, "w"), indent=1)
    print(pid, f"t{trial}", "ok" if "verdict" in rec else f"ERR {rec.get('error')}", flush=True)

jobs = [(pid, t) for pid in prompts for t in (1, 2)]
with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(lambda j: judge(*j), jobs))
print("judged", len(jobs))
