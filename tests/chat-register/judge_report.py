#!/usr/bin/env python3
import glob, json, os, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__))
p1 = collections.defaultdict(list); sub = collections.defaultdict(list); rank = collections.defaultdict(list); wins = collections.Counter(); n = 0; notes = []
for f in sorted(glob.glob(os.path.join(HERE, "judged", "*.json"))):
    r = json.load(open(f)); v = r.get("verdict")
    if not v: continue
    n += 1; m = r["map"]
    for l, s in v["scores"].items():
        c = m.get(l); p1[c].append(s["pass1"]); sub[c].append(s["substance"])
    for i, l in enumerate(v["rank"]):
        rank[m.get(l)].append(i + 1)
    wins[m.get(v["rank"][0])] += 1
    notes.append(f"{r['id']} t{r['trial']}: {v.get('note','')}")
conds = sorted(p1, key=lambda c: -st.mean(p1[c]))
print(f"judged sets: {n}\n")
print("| condition | pass1 mean | substance mean | mean rank | ranked first | answers judged |")
print("|---|---|---|---|---|---|")
for c in conds:
    print(f"| {c} | {st.mean(p1[c]):.2f} | {st.mean(sub[c]):.2f} | {st.mean(rank[c]):.2f} | {wins[c]} | {len(p1[c])} |")
print("\nnotes:"); print("\n".join(notes))
