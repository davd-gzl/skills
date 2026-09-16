#!/usr/bin/env python3
"""Run claude -p over the caveman benchmark prompts, one call per prompt, condition and trial."""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
COND = {"plugin": "caveman-skill.md", "rule": "rule.md", "none": None, "rule2": "rule2.md", "rule3": "rule3.md", "rule4": "rule4.md", "rule5": "rule5.md"}
MODEL, EFFORT = os.environ.get("MODEL", "fable"), os.environ.get("EFFORT", "medium")
SHA = "84cc3c14fa1e10182adaced856e003406ccd250d"  # JuliusBrussee/caveman, MIT, the plugin version measured

def fetch(path, dest):
    if not os.path.exists(dest):
        b64 = subprocess.run(["gh", "api", f"repos/JuliusBrussee/caveman/contents/{path}?ref={SHA}", "--jq", ".content"],
                             check=True, capture_output=True, text=True).stdout
        import base64
        open(dest, "w").write(base64.b64decode(b64).decode())

fetch("caveman/SKILL.md", os.path.join(HERE, "caveman-skill.md"))
fetch("benchmarks/prompts.json", os.path.join(HERE, "prompts.json"))

def call(pid, cond, prompt, trial):
    outp = os.path.join(HERE, "out2", f"{pid}__{cond}__t{trial}.json")
    if os.path.exists(outp):
        return outp
    cmd = ["claude", "-p", "--model", MODEL, "--effort", EFFORT, "--tools", "",
           "--strict-mcp-config", "--disable-slash-commands", "--setting-sources", "",
           "--no-session-persistence", "--output-format", "json"]
    if COND[cond]:
        cmd += ["--append-system-prompt-file", os.path.join(HERE, COND[cond])]
    cmd.append(prompt)
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE") and k != "CLAUDE_CODE_ENTRYPOINT"}
    t = time.time()
    r = subprocess.run(cmd, cwd=os.path.join(HERE, "work"), env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    rec = {"id": pid, "cond": cond, "trial": trial, "rc": r.returncode, "secs": round(time.time() - t, 1),
           "stderr": r.stderr[-2000:], "raw": r.stdout}
    try:
        rec["json"] = json.loads(r.stdout)
    except Exception as e:
        rec["json_error"] = str(e)
    json.dump(rec, open(outp, "w"), indent=1)
    print(f"{pid:28} {cond:7} t{trial} rc={r.returncode} {rec['secs']}s", flush=True)
    return outp

prompts = json.load(open(os.path.join(HERE, "prompts.json")))["prompts"]
if sys.argv[1:] == ["--smoke"]:
    p = prompts[0]
    out = call(p["id"], "rule", p["prompt"], 0)
    print(open(out).read()[:3000])
    sys.exit(0)
n = int(sys.argv[1]) if sys.argv[1:] else len(prompts)
jobs = [(p["id"], c, p["prompt"], t) for t in (1, 2) for p in prompts[:n] for c in COND]
with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(lambda j: call(*j), jobs))
print("done", len(jobs))
